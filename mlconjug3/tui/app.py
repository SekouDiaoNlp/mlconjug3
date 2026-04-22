"""
app.py

Main TUI application for mlconjug3.

This module implements a Textual-based terminal user interface for:
- Interactive verb conjugation
- Multi-language support
- Batch processing of verbs
- Verb exploration and navigation

The interface is designed to be:
- Keyboard-first
- Fast and responsive
- Suitable for both learners and power users
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any
import random

from textual.app import App, ComposeResult
from textual.worker import Worker, WorkerState
from textual.widgets import (
    Header,
    Footer,
    Input,
    TabbedContent,
    TabPane,
    Static,
    Button,
    Select,
)
from textual.containers import Horizontal, Vertical, VerticalScroll

from mlconjug3.core.options import LANGUAGE_OPTIONS, SUBJECT_OPTIONS
from mlconjug3.tui.cache import ConjugationCache
from mlconjug3.tui.services.conjugation_facade import (
    ConjugationViewModel,
    TUIConjugationFacade,
)
from mlconjug3.tui.widgets.results_table import ResultsTable
from mlconjug3.tui.widgets.verb_browser import VerbBrowser, VerbSelected
from mlconjug3.tui.widgets.verb_shelf import VerbShelf
from mlconjug3.tui.widgets.filter_bar import FilterBar, FiltersChanged
from mlconjug3.tui.widgets.suggest_dropdown import SuggestDropdown, SuggestionChosen
from mlconjug3.tui.widgets.profile_panel import ProfilePanel, VerbProfile
from mlconjug3.tui.widgets.help_screen import HelpScreen
from mlconjug3.core.morphology.summary import summarize
from mlconjug3.tui.state import TUIState
from mlconjug3.tui.search.fuzzy import suggest
from mlconjug3.core.export import ExportPayload, to_json, to_text
from mlconjug3.tui.learn.engine import LearnStep, build_quiz
from mlconjug3.tui.lexicon import lookup as lex_lookup


class Mlconjug3TUI(App):
    """
    Main application class for the mlconjug3 TUI.

    This class orchestrates all UI components, services, and state
    management required for interactive verb conjugation.

    Attributes
    ----------
    CSS_PATH : str
        Path to the CSS theme file.
    DEBOUNCE_DELAY : float
        Delay used to throttle input updates.

    state : TUIState
        Global application state manager.

    service : TUIConjugationFacade
        Backend facade for normalized conjugation access.

    cache : ConjugationCache
        LRU cache for conjugation results.
    """

    CSS_PATH: str = "theme.css"
    DEBOUNCE_DELAY: float = 0.25
    BINDINGS = [
        ("f", "toggle_favorite", "Favorite"),
        ("t", "toggle_theme", "Theme"),
        ("d", "toggle_density", "Density"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self) -> None:
        """
        Initialize the TUI application and core services.
        """
        super().__init__()

        self.state: TUIState = TUIState()
        self.state.load()

        self.service: TUIConjugationFacade = TUIConjugationFacade(
            language=self.state.language, subject=self.state.subject
        )
        self.cache: ConjugationCache = ConjugationCache()

        self._timer: Optional[Any] = None
        self._last_valid: Optional[str] = None
        self._current_verb: Optional[str] = None
        self._current_table: Optional[dict[str, Any]] = None
        self._learn_step: LearnStep = LearnStep.PICK_VERB
        self._learn_quiz_answer: Optional[str] = None
        self._learn_current_verb: Optional[str] = None
        self._theme_variant: str = "dark"
        self._density_variant: str = "spacious"
        self._current_template: Optional[str] = None
        self._current_root: Optional[str] = None

        self.verbs: List[str] = self.service.list_verbs()

    def on_mount(self) -> None:
        """
        Apply initial UI variants (theme, density) after mount.
        """
        self._apply_variants()
        self._refresh_learn_controls()

    def _apply_variants(self) -> None:
        """
        Apply screen-level variant classes for theme and density.
        """
        screen = self.screen
        screen.set_class(self._theme_variant == "light", "theme-light")
        screen.set_class(self._theme_variant == "dark", "theme-dark")
        screen.set_class(self._density_variant == "compact", "density-compact")
        screen.set_class(self._density_variant == "spacious", "density-spacious")

    # -------------------------
    # UI LAYOUT
    # -------------------------
    def compose(self) -> ComposeResult:
        """
        Compose the UI layout.

        Returns
        -------
        ComposeResult
            Generator yielding UI components.
        """
        yield Header()
        yield Static(self._status_bar_text(), id="status_bar")
        yield FilterBar(
            moods=[],
            tenses=[],
            selected_moods=self.state.selected_moods,
            selected_tenses=self.state.selected_tenses,
            id="filter_bar",
        )

        with TabbedContent():

            # ---------------- CONJUGATE ----------------
            with TabPane("Conjugate"):
                yield Static("Live conjugation", classes="title")

                with Horizontal():
                    with Vertical(classes="panel left-panel"):
                        yield Input(placeholder="Type a verb...", id="verb_input")
                        yield SuggestDropdown(id="verb_suggest")
                        yield Static("", id="input_feedback", markup=False)
                        with Horizontal():
                            yield Button("Export JSON", id="export_json")
                            yield Button("Export Text", id="export_text")
                        yield ResultsTable(id="results")
                    with Vertical(classes="panel right-panel"):
                        yield ProfilePanel(id="profile")

            # ---------------- EXPLORER ----------------
            with TabPane("Explorer"):

                with Horizontal():

                    with Vertical(classes="panel left-panel"):
                        yield Static("Verb Explorer", classes="title")
                        yield VerbBrowser(self.verbs)

                    with Vertical(classes="panel right-panel"):
                        yield Static("Verb Details", classes="title")

                        with VerticalScroll(id="explorer_scroll"):
                            yield ProfilePanel(id="explorer_profile")
                            yield ResultsTable(id="explorer_results")

            # ---------------- BATCH ----------------
            with TabPane("Batch"):
                yield Static("Enter verbs separated by spaces or commas")

                yield Input(
                    placeholder="aller, manger, finir",
                    id="batch_input",
                )

                yield Button("Run batch", id="run_batch")
                yield ResultsTable(id="batch_results")

            # ---------------- COMPARE ----------------
            with TabPane("Compare"):
                with Horizontal():
                    with Vertical(classes="panel left-panel"):
                        yield Static("Verb A", classes="title")
                        yield Input(placeholder="Type verb A...", id="compare_a_input")
                        yield ResultsTable(id="compare_a_results")
                    with Vertical(classes="panel right-panel"):
                        yield Static("Verb B", classes="title")
                        yield Input(placeholder="Type verb B...", id="compare_b_input")
                        yield ResultsTable(id="compare_b_results")

            # ---------------- LEARN ----------------
            with TabPane("Learn"):
                yield Static("Learning mode", classes="title")
                yield Static("", id="learn_streak", markup=True)
                yield Static(
                    "Flow: Next verb → Reveal key forms → Quiz → Show answer → Mark ✅/❌",
                    id="learn_help",
                    classes="muted",
                )
                with Horizontal():
                    yield Button("Next verb", id="learn_next")
                    yield Button("Reveal key forms", id="learn_reveal")
                    yield Button("Quiz me", id="learn_quiz")
                    yield Button("Show answer", id="learn_answer")
                    yield Button("Correct", id="learn_correct")
                    yield Button("Wrong", id="learn_wrong")
                yield Static("", id="learn_prompt", markup=False)
                yield ResultsTable(id="learn_results")

            # ---------------- LIBRARY ----------------
            with TabPane("Library"):
                with Horizontal():
                    with Vertical(classes="panel left-panel"):
                        yield VerbShelf(
                            "History", list(self.state.history), id="history_shelf"
                        )
                    with Vertical(classes="panel right-panel"):
                        yield VerbShelf(
                            "Favorites", sorted(self.state.favorites), id="favorites_shelf"
                        )

            # ---------------- SETTINGS ----------------
            with TabPane("Settings"):

                yield Static("Language")

                yield Select(
                    options=LANGUAGE_OPTIONS,
                    value="fr",
                    id="lang_select",
                )

                yield Static("Subject format")

                yield Select(
                    options=SUBJECT_OPTIONS,
                    value="abbrev",
                    id="subject_select",
                )

        yield Footer()

    # -------------------------
    # STATUS BAR
    # -------------------------
    def _status_bar_text(self) -> str:
        """
        Build the status bar text.

        Returns
        -------
        str
            Formatted status string.
        """
        lang = self.state.language.upper()
        subject = self.state.subject.upper()
        hist = len(self.state.history)
        fav = len(self.state.favorites)
        theme = "LIGHT" if self._theme_variant == "light" else "DARK"
        density = "COMPACT" if self._density_variant == "compact" else "SPACIOUS"
        verb = (self._current_verb or "").strip()
        tpl = self._current_template
        root = self._current_root
        out = (
            f"[b]🌍[/b] [#7aa2ff]{lang}[/]  "
            f"[b]👤[/b] [#c0caf5]{subject}[/]  "
        )
        if verb:
            out += f"[b]🏷[/b] [#9aa4b2]{(tpl or '?')}[/]  "
            out += f"[b]🌱[/b] [#9aa4b2]{(root or '?')}[/]  "
        out += (
            f"[b]🕘[/b] [#9aa4b2]{hist}[/]  "
            f"[b]⭐[/b] [#e0af68]{fav}[/]  "
            f"[#9aa4b2]•[/] [b]🌓[/b] [#9aa4b2]{theme}[/]  "
            f"[b]↕[/b] [#9aa4b2]{density}[/]"
        )
        return out

    def _refresh_status_bar(self) -> None:
        """
        Refresh the status bar display.
        """
        self.query_one("#status_bar", Static).update(self._status_bar_text())
        self._refresh_library()

    def _refresh_library(self) -> None:
        """
        Refresh library shelves (history/favorites) if mounted.
        """

        try:
            self.query_one("#history_shelf", VerbShelf).set_verbs(
                list(reversed(self.state.history))
            )
            self.query_one("#favorites_shelf", VerbShelf).set_verbs(
                sorted(self.state.favorites)
            )
        except Exception:
            return

    # -------------------------
    # VALIDATION
    # -------------------------
    def _is_valid(self, verb: str) -> bool:
        """
        Validate whether a verb is supported by the current language.

        Parameters
        ----------
        verb : str
            Verb to validate.

        Returns
        -------
        bool
            True if valid, False otherwise.
        """
        try:
            return self.service.is_valid_verb(verb)
        except Exception:
            return False

    def _missing_forms(self, table: dict[str, Any]) -> tuple[str, ...]:
        """
        Compute a compact list of missing form coordinates.

        Parameters
        ----------
        table:
            Conjugation table.

        Returns
        -------
        tuple[str, ...]
            Strings like "mood/tense/person".
        """
        out: list[str] = []
        for mood, mood_val in (table or {}).items():
            if not isinstance(mood_val, dict):
                continue
            for tense, tense_val in (mood_val or {}).items():
                if not isinstance(tense_val, dict):
                    continue
                for person, form in tense_val.items():
                    if form is None:
                        out.append(f"{mood}/{tense}/{person}")
                    elif isinstance(form, str) and form.strip() in {"", "?"}:
                        out.append(f"{mood}/{tense}/{person}")
        return tuple(out)

    # -------------------------
    # LIVE INPUT
    # -------------------------
    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handle live input changes in the conjugation tab.

        Parameters
        ----------
        event : Input.Changed
            Textual input change event.
        """
        if event.input.id != "verb_input":
            return

        verb = event.value.strip().lower()
        try:
            self.query_one("#verb_suggest", SuggestDropdown).set_suggestions(
                suggest(self.verbs, verb, limit=8) if verb else []
            )
        except Exception:
            pass

        if self._timer:
            self._timer.stop()

        self._timer = self.set_timer(
            self.DEBOUNCE_DELAY,
            lambda: self._update_verb(verb),
        )

    def on_suggestion_chosen(self, message: SuggestionChosen) -> None:
        """
        Apply a chosen suggestion to the input and conjugate.
        """

        try:
            inp = self.query_one("#verb_input", Input)
            inp.value = message.value
        except Exception:
            return
        self._update_verb(message.value.strip().lower())

    def _update_verb(self, verb: str) -> None:
        """
        Update conjugation view for a given verb.

        Parameters
        ----------
        verb : str
            Verb to conjugate.
        """
        if not verb:
            self.query_one("#results", ResultsTable).clear()
            return

        feedback = self.query_one("#input_feedback", Static)
        table = self.query_one("#results", ResultsTable)

        if not self._is_valid(verb):
            suggestions = suggest(self.verbs, verb, limit=5)
            hint = ""
            if suggestions:
                hint = "  Did you mean: " + ", ".join(suggestions)
            feedback.update(f"Invalid verb: {verb}{hint}")
            table.clear()
            return

        feedback.update("")
        self._compute_and_apply_single(verb)

    def _compute_and_apply_single(self, verb: str) -> None:
        """
        Compute conjugation for a single verb in a background worker.

        Parameters
        ----------
        verb:
            Verb to conjugate.
        """

        self.run_worker(
            lambda: self.cache.get(verb, lambda k: self.service.conjugate_one(k)),
            name=f"single:{verb}",
            group="conjugate_single",
            exclusive=True,
            thread=True,
        )

    def _apply_single_result(
        self, verb: str, vm: Optional[ConjugationViewModel]
    ) -> None:
        """
        Apply a computed conjugation result to the UI.

        Parameters
        ----------
        verb:
            Verb that was requested.
        vm:
            Computed view model, or None when missing.
        """

        table = self.query_one("#results", ResultsTable)
        if vm is None:
            table.clear()
            return

        self._current_verb = verb
        self._current_table = dict(vm.table)
        self._current_template = getattr(vm, "verb_template", None)
        self._current_root = getattr(vm, "verb_root", None)
        self.state.add_history(verb)
        self._refresh_status_bar()

        table.update_conjugation(
            verb,
            dict(vm.table),
            mode="ML" if vm.predicted else "RULE",
            confidence=vm.confidence_score,
            allowed_moods=self.state.selected_moods or None,
            allowed_tenses=self.state.selected_tenses or None,
        )

        self._refresh_filter_options(dict(vm.table))

        try:
            summary = summarize(
                    language=self.state.language,
                    infinitive=verb,
                    table=dict(vm.table),
                    irregular_proxy=vm.predicted,
                )
            lex = lex_lookup(self.state.language, verb)
            missing = self._missing_forms(dict(vm.table))
            self.query_one("#profile", ProfilePanel).set_profile(
                VerbProfile(
                    verb=verb,
                    root=getattr(vm, "verb_root", None),
                    template=getattr(vm, "verb_template", None),
                    morphology=summary,
                    lexicon=lex,
                    predicted=bool(vm.predicted),
                    confidence_score=vm.confidence_score,
                    missing_forms=missing,
                )
            )
        except Exception:
            return

    # -------------------------
    # EXPLORER
    # -------------------------
    def on_verb_selected(self, message: VerbSelected) -> None:
        """
        Handle verb selection from the explorer panel.

        Parameters
        ----------
        message : VerbSelected
            Selected verb message event.
        """
        verb = message.verb

        self.state.add_history(verb)
        self._refresh_status_bar()

        if not self._is_valid(verb):
            return

        self._compute_and_apply_explorer(verb)

    def _compute_and_apply_explorer(self, verb: str) -> None:
        """
        Compute conjugation for explorer selection in a background worker.

        Parameters
        ----------
        verb:
            Selected verb.
        """

        self.run_worker(
            lambda: self.service.conjugate_one(verb),
            name=f"explorer:{verb}",
            group="conjugate_explorer",
            exclusive=True,
            thread=True,
        )

    def _apply_explorer_result(
        self, verb: str, vm: Optional[ConjugationViewModel]
    ) -> None:
        """
        Apply explorer conjugation result.

        Parameters
        ----------
        verb:
            Selected verb.
        vm:
            View model or None.
        """

        if vm is None:
            return
        self._current_verb = verb
        self._current_template = getattr(vm, "verb_template", None)
        self._current_root = getattr(vm, "verb_root", None)
        try:
            summary = summarize(
                language=self.state.language,
                infinitive=verb,
                table=dict(vm.table),
                irregular_proxy=vm.predicted,
            )
            lex = lex_lookup(self.state.language, verb)
            missing = self._missing_forms(dict(vm.table))
            self.query_one("#explorer_profile", ProfilePanel).set_profile(
                VerbProfile(
                    verb=verb,
                    root=getattr(vm, "verb_root", None),
                    template=getattr(vm, "verb_template", None),
                    morphology=summary,
                    lexicon=lex,
                    predicted=bool(vm.predicted),
                    confidence_score=vm.confidence_score,
                    missing_forms=missing,
                )
            )
        except Exception:
            pass
        self.query_one("#explorer_results", ResultsTable).update_conjugation(
            verb,
            dict(vm.table),
            mode="ML" if vm.predicted else "RULE",
            confidence=vm.confidence_score,
            allowed_moods=self.state.selected_moods or None,
            allowed_tenses=self.state.selected_tenses or None,
        )

    def action_toggle_favorite(self) -> None:
        """
        Toggle favorite status for the current verb.
        """

        if not self._current_verb:
            return
        self.state.toggle_favorite(self._current_verb)
        self._refresh_status_bar()

    def action_toggle_theme(self) -> None:
        """
        Toggle between dark and light themes.
        """
        self._theme_variant = "light" if self._theme_variant == "dark" else "dark"
        self._apply_variants()
        self._refresh_status_bar()

    def action_toggle_density(self) -> None:
        """
        Toggle between compact and spacious density.
        """
        self._density_variant = (
            "compact" if self._density_variant == "spacious" else "spacious"
        )
        self._apply_variants()
        self._refresh_status_bar()

    def action_show_help(self) -> None:
        """
        Show the in-app help modal.
        """
        self.push_screen(HelpScreen())

    # -------------------------
    # BATCH PROCESSING
    # -------------------------
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle batch input submission.

        Parameters
        ----------
        event : Input.Submitted
            Input submission event.
        """
        if event.input.id == "batch_input":
            self._run_batch()
        elif event.input.id == "compare_a_input":
            self._compare_update("a", event.value.strip().lower())
        elif event.input.id == "compare_b_input":
            self._compare_update("b", event.value.strip().lower())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.

        Parameters
        ----------
        event : Button.Pressed
            Button event.
        """
        if event.button.id == "run_batch":
            self._run_batch()
        elif event.button.id == "export_json":
            self._export_current("json")
        elif event.button.id == "export_text":
            self._export_current("text")
        elif event.button.id == "learn_next":
            self._learn_next()
        elif event.button.id == "learn_reveal":
            self._learn_reveal_key_forms()
        elif event.button.id == "learn_quiz":
            self._learn_quiz()
        elif event.button.id == "learn_answer":
            self._learn_show_answer()
        elif event.button.id == "learn_correct":
            self._learn_mark(correct=True)
        elif event.button.id == "learn_wrong":
            self._learn_mark(correct=False)

    def _run_batch(self) -> None:
        """
        Execute batch conjugation for multiple verbs.
        """
        input_widget = self.query_one("#batch_input", Input)
        results_table = self.query_one("#batch_results", ResultsTable)

        results_table.clear()

        verbs = [
            v.strip().lower()
            for v in input_widget.value.replace(",", " ").split()
            if v.strip()
        ]

        self._compute_and_apply_batch(verbs)

    def _compare_update(self, side: str, verb: str) -> None:
        """
        Update conjugation for compare view.

        Parameters
        ----------
        side:
            Either "a" or "b".
        verb:
            Verb to conjugate.
        """

        if not verb or not self._is_valid(verb):
            return
        self.run_worker(
            lambda: self.service.conjugate_one(verb),
            name=f"compare:{side}:{verb}",
            group=f"conjugate_compare_{side}",
            exclusive=True,
            thread=True,
        )

    def _learn_next(self) -> None:
        """
        Pick a new verb for learning mode and show its conjugation.
        """

        if not self.verbs:
            return
        rng = random.Random(self.state.learn_seed)
        verb = rng.choice(self.verbs)
        self.state.learn_seed += 1
        self.state.save()
        try:
            self._learn_step = LearnStep.REVEAL_KEY_FORMS
            self._learn_current_verb = verb
            self._learn_quiz_answer = None
            self._refresh_learn_streak()
            self._refresh_learn_controls()
            self.query_one("#learn_prompt", Static).update(
                f"Verb: {verb}\n"
                f"1) Explore the table\n"
                f"2) Press 'Reveal key forms' when ready"
            )
        except Exception:
            return

        self.run_worker(
            lambda: self.service.conjugate_one(verb),
            name=f"learn:{verb}",
            group="conjugate_learn",
            exclusive=True,
            thread=True,
        )

    def _refresh_learn_streak(self) -> None:
        try:
            streak = self.state.learn_streak
            best = self.state.learn_best_streak
            badge = "🌱" if streak == 0 else ("🔥" if streak >= 5 else "✨")
            self.query_one("#learn_streak", Static).update(
                f"[b]{badge}[/b] Streak [b]{streak}[/b]   "
                f"[#9aa4b2]Best[/] [b]{best}[/b]"
            )
        except Exception:
            return

    def _learn_reveal_key_forms(self) -> None:
        if self._learn_step not in {LearnStep.REVEAL_KEY_FORMS, LearnStep.QUIZ_PROMPT}:
            return
        if not self._current_table:
            return
        # For now: re-render with current filters (acts as the reveal)
        try:
            self.query_one("#learn_prompt", Static).update(
                "Key forms revealed.\nPress 'Quiz me' to practice one cell."
            )
        except Exception:
            return
        self._learn_step = LearnStep.QUIZ_PROMPT
        self._refresh_learn_controls()

    def _learn_quiz(self) -> None:
        if not self._current_table:
            return
        quiz = build_quiz(self._current_table, self.state.learn_seed)
        self.state.learn_seed += 1
        self.state.save()
        if quiz is None:
            return
        self._learn_quiz_answer = quiz.answer
        self._learn_step = LearnStep.QUIZ_PROMPT
        try:
            self.query_one("#learn_prompt", Static).update(
                f"Quiz:\n{quiz.mood} / {quiz.tense}\n{quiz.person} = ?\n"
                f"Try to answer, then press 'Show answer'."
            )
        except Exception:
            return
        self._refresh_learn_controls()

    def _learn_show_answer(self) -> None:
        if self._learn_quiz_answer is None:
            return
        self._learn_step = LearnStep.REVEAL_ANSWER
        try:
            self.query_one("#learn_prompt", Static).update(
                f"Answer: {self._learn_quiz_answer}\n"
                f"Mark yourself 'Correct' or 'Wrong'."
            )
        except Exception:
            return
        self._refresh_learn_controls()

    def _learn_mark(self, *, correct: bool) -> None:
        if self._learn_step != LearnStep.REVEAL_ANSWER:
            return
        if correct:
            self.state.learn_streak += 1
            if self.state.learn_streak > self.state.learn_best_streak:
                self.state.learn_best_streak = self.state.learn_streak
        else:
            self.state.learn_streak = 0
        self.state.save()
        self._refresh_learn_streak()
        self._learn_step = LearnStep.PICK_VERB
        self._learn_quiz_answer = None
        self._refresh_learn_controls()

    def _refresh_learn_controls(self) -> None:
        """
        Enable/disable Learn buttons based on the current step.
        """
        try:
            next_btn = self.query_one("#learn_next", Button)
            reveal_btn = self.query_one("#learn_reveal", Button)
            quiz_btn = self.query_one("#learn_quiz", Button)
            ans_btn = self.query_one("#learn_answer", Button)
            ok_btn = self.query_one("#learn_correct", Button)
            bad_btn = self.query_one("#learn_wrong", Button)
        except Exception:
            return

        step = self._learn_step
        next_btn.disabled = step not in {LearnStep.PICK_VERB}
        reveal_btn.disabled = step not in {LearnStep.REVEAL_KEY_FORMS, LearnStep.QUIZ_PROMPT}
        quiz_btn.disabled = step not in {LearnStep.QUIZ_PROMPT}
        ans_btn.disabled = step not in {LearnStep.QUIZ_PROMPT} or self._learn_quiz_answer is None
        ok_btn.disabled = step not in {LearnStep.REVEAL_ANSWER}
        bad_btn.disabled = step not in {LearnStep.REVEAL_ANSWER}

    def _export_current(self, fmt: str) -> None:
        """
        Export the currently displayed conjugation.

        Parameters
        ----------
        fmt:
            "json" or "text".
        """

        if not self._current_verb or not self._current_table:
            return

        payload = ExportPayload(
            verb=self._current_verb,
            language=self.state.language,
            subject=self.state.subject,
            table=self._current_table,
        )

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"mlconjug3-{self._current_verb}-{self.state.language}-{stamp}"
        out_path = Path.cwd() / (base + (".json" if fmt == "json" else ".txt"))

        text = to_json(payload) if fmt == "json" else to_text(payload)
        out_path.write_text(text, encoding="utf-8")

        try:
            self.query_one("#input_feedback", Static).update(f"Exported: {out_path}")
        except Exception:
            return

    def _compute_and_apply_batch(self, verbs: list[str]) -> None:
        """
        Compute conjugations for a batch of verbs in a background worker.

        Parameters
        ----------
        verbs:
            Verbs to conjugate.
        """

        valid = [v for v in verbs if self._is_valid(v)]
        self.run_worker(
            lambda: self.service.conjugate_many(valid),
            name="batch",
            group="conjugate_batch",
            exclusive=True,
            thread=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """
        Handle worker completion events.

        Parameters
        ----------
        event:
            Worker state change event emitted by Textual.
        """

        worker: Worker[Any] = event.worker
        if event.state != WorkerState.SUCCESS:
            return

        if worker.group == "conjugate_single":
            if not worker.name.startswith("single:"):
                return
            verb = worker.name.removeprefix("single:")
            self._apply_single_result(verb, worker.result)
            return

        if worker.group == "conjugate_explorer":
            if not worker.name.startswith("explorer:"):
                return
            verb = worker.name.removeprefix("explorer:")
            self._apply_explorer_result(verb, worker.result)
            return

        if worker.group == "conjugate_batch":
            self._apply_batch_result(worker.result)
            return

        if worker.group in {"conjugate_compare_a", "conjugate_compare_b"}:
            if not worker.name.startswith("compare:"):
                return
            _prefix, side, verb = worker.name.split(":", 2)
            vm = worker.result
            if vm is None:
                return
            table_id = "#compare_a_results" if side == "a" else "#compare_b_results"
            self.query_one(table_id, ResultsTable).update_conjugation(
                verb,
                dict(vm.table),
                mode="ML" if vm.predicted else "RULE",
                confidence=vm.confidence_score,
                allowed_moods=self.state.selected_moods or None,
                allowed_tenses=self.state.selected_tenses or None,
            )
            return

        if worker.group == "conjugate_learn":
            vm = worker.result
            if vm is None:
                return
            self._current_verb = vm.verb
            self._current_table = dict(vm.table)
            self.query_one("#learn_results", ResultsTable).update_conjugation(
                vm.verb,
                dict(vm.table),
                mode="ML" if vm.predicted else "RULE",
                confidence=vm.confidence_score,
                allowed_moods=self.state.selected_moods or None,
                allowed_tenses=self.state.selected_tenses or None,
            )
            return

    def _apply_batch_result(self, vms: list[ConjugationViewModel]) -> None:
        """
        Apply batch conjugation results to the batch table.

        Parameters
        ----------
        vms:
            View models to append.
        """

        results_table = self.query_one("#batch_results", ResultsTable)
        for vm in vms:
            results_table.update_conjugation(
                vm.verb,
                dict(vm.table),
                append=True,
                mode="ML" if vm.predicted else "RULE",
                confidence=vm.confidence_score,
                allowed_moods=self.state.selected_moods or None,
                allowed_tenses=self.state.selected_tenses or None,
            )

    # -------------------------
    # SETTINGS
    # -------------------------
    def on_select_changed(self, event: Select.Changed) -> None:
        """
        Handle language and subject configuration changes.

        Parameters
        ----------
        event : Select.Changed
            Selection change event.
        """
        if event.select.id == "lang_select":
            self.service.set_language(event.value)
            self.state.language = event.value
            self.verbs = self.service.list_verbs()
            self._refresh_status_bar()
            self.state.save()

        elif event.select.id == "subject_select":
            self.service.set_subject(event.value)
            self.state.subject = event.value
            self._refresh_status_bar()
            self.state.save()

    def on_filters_changed(self, message: FiltersChanged) -> None:
        """
        Persist global filter state and re-render current views.
        """

        self.state.selected_moods = set(message.state.moods)
        self.state.selected_tenses = set(message.state.tenses)
        self.state.save()
        if self._current_verb:
            self._update_verb(self._current_verb)

    def _refresh_filter_options(self, table: dict[str, Any]) -> None:
        """
        Update mood/tense filter options based on a conjugation table.

        Parameters
        ----------
        table:
            Conjugation table (mood -> tense -> forms).
        """

        moods = sorted({str(m).capitalize() for m in table.keys()})
        tenses: set[str] = set()
        for mood_val in table.values():
            if isinstance(mood_val, dict):
                tenses.update(str(t).capitalize() for t in mood_val.keys())

        try:
            bar = self.query_one("#filter_bar", FilterBar)
        except Exception:
            return
        bar.set_options(moods, sorted(tenses))


def main() -> None:
    """
    Entry point for the TUI application.

    This entrypoint supports a minimal `--help` mode for discoverability.
    """

    import sys

    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        sys.stdout.write(
            "mlconjug3-tui\n\n"
            "Launch the interactive Textual UI.\n\n"
            "Usage:\n"
            "  mlconjug3-tui\n\n"
            "Keyboard:\n"
            "  f    Toggle favorite for current verb\n"
            "\n"
        )
        return

    Mlconjug3TUI().run()


if __name__ == "__main__":
    main()
