from __future__ import annotations

import re
from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, ListItem, ListView
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual import on

from .engine import ConjugationEngine, MorphAnalyzer, VerbAutocompleteEngine
from .widgets import (
    AutocompleteSuggestions,
    ResultsTable,
    InsightsPanel,
    VerbBrowser,
    VerbSelected,
    HelpScreen
)
from .state import AppState, UIPreferences, SessionStore, SUPPORTED_LANGUAGES, LANGUAGE_NAMES
from mlconjug3.core.morphology.summary import VerbMorphologySummary


class MLConjug3App(App):
    """
    The main mlconjug3 TUI application.
    A retro-modern linguistic laboratory.
    """

    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("ctrl+f", "focus_search", "Search", show=True),
        Binding("ctrl+l", "cycle_language", "Language", show=True),
        Binding("ctrl+m", "cycle_mode", "Mode", show=True),
        Binding("ctrl+b", "toggle_bookmark", "Bookmark", show=True),
        Binding("ctrl+h", "toggle_history", "History", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.prefs = UIPreferences.load()
        self.session = SessionStore.load()
        self.engine = ConjugationEngine()
        self.analyzer = MorphAnalyzer()
        self.autocomplete = VerbAutocompleteEngine()
        self._verbs_loaded: set[str] = set()

    # ------------------------------------------------------------------
    # UI LAYOUT
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="top-bar"):
            yield Input(placeholder="Type a verb (e.g. manger)", id="verb-input")
            yield Static("FR", id="lang-badge")
            yield Static("SIMPLE", id="mode-badge")
            yield Static("☆", id="bookmark-indicator")

        with Horizontal(id="main"):
            with Vertical(id="left-pane"):
                yield ResultsTable(id="results-table")
            
            with Vertical(id="right-pane"):
                yield InsightsPanel(id="insights-panel")
                yield VerbBrowser(verbs=[], id="verb-browser")

        yield AutocompleteSuggestions(id="suggestions")
        yield Footer()

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self.title = "mlconjug3 — Linguistic Lab"
        self.sub_title = "Deterministic Verb Conjugation"
        
        # Apply preferences
        if self.prefs.theme == "light":
            self.add_class("-theme-light")
        elif self.prefs.theme == "high_contrast":
            self.add_class("-high-contrast")
            
        if self.prefs.reduced_motion:
            self.add_class("-reduced-motion")
            
        self.state.language = self.prefs.default_language
        self.state.mode = self.prefs.default_mode
        
        self._update_badges()
        self._load_language_data(self.state.language)
        
        if self.state.verb:
            self.conjugate_verb(self.state.verb)
        
        self.query_one("#verb-input").focus()

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_focus_search(self) -> None:
        self.query_one("#verb-input").focus()

    def action_cycle_language(self) -> None:
        idx = SUPPORTED_LANGUAGES.index(self.state.language)
        next_idx = (idx + 1) % len(SUPPORTED_LANGUAGES)
        self.state.language = SUPPORTED_LANGUAGES[next_idx]
        self._load_language_data(self.state.language)
        self._update_badges()
        self.notify(f"Language switched to {LANGUAGE_NAMES[self.state.language]}")

    def action_cycle_mode(self) -> None:
        modes = ["simple", "learner", "research"]
        idx = modes.index(self.state.mode)
        next_idx = (idx + 1) % len(modes)
        self.state.mode = modes[next_idx]
        self._update_badges()
        self.notify(f"Mode switched to {self.state.mode.capitalize()}")

    def action_toggle_bookmark(self) -> None:
        if not self.state.verb:
            return
        is_added = self.session.toggle_bookmark(self.state.verb, self.state.language)
        self._update_bookmark_indicator()
        msg = "Bookmarked" if is_added else "Removed from bookmarks"
        self.notify(msg)

    def action_toggle_history(self) -> None:
        # Placeholder for history modal
        self.notify("History coming soon", severity="warning")

    # ------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------

    @on(Input.Changed, "#verb-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_suggestions(event.value)

    @on(Input.Submitted, "#verb-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        verb = event.value.strip()
        if verb:
            self.conjugate_verb(verb)
            self.query_one("#suggestions").remove_class("visible")

    @on(VerbSelected)
    def on_verb_selected(self, event: VerbSelected) -> None:
        self.conjugate_verb(event.verb)
        self.query_one("#verb-input").value = event.verb
        self.query_one("#suggestions").remove_class("visible")

    @on(ListView.Selected, "#suggestions")
    def on_suggestion_selected(self, event: ListView.Selected) -> None:
        if event.item:
            verb = str(event.item.query_one(Static).renderable)
            self.conjugate_verb(verb)
            self.query_one("#verb-input").value = verb
            self.query_one("#suggestions").remove_class("visible")

    # ------------------------------------------------------------------
    # LOGIC
    # ------------------------------------------------------------------

    def _load_language_data(self, lang: str) -> None:
        if lang in self._verbs_loaded:
            return
            
        # Get verbs from engine/mlconjug3
        conjugator = self.engine._get(lang)
        verbs = list(conjugator.conjug_manager.verbs.keys())
        
        self.autocomplete.load_verbs(verbs, lang)
        
        # Update VerbBrowser
        browser = self.query_one(VerbBrowser)
        browser.verbs = sorted(verbs)
        browser._update_list(browser.verbs[:browser.max_results])
        
        self._verbs_loaded.add(lang)

    def _update_badges(self) -> None:
        self.query_one("#lang-badge").update(self.state.language.upper())
        self.query_one("#mode-badge").update(self.state.mode.upper())
        
        # Update classes for CSS targeting
        self.remove_class("-mode-simple", "-mode-learner", "-mode-research")
        self.add_class(f"-mode-{self.state.mode}")
        
    def _update_bookmark_indicator(self) -> None:
        if self.session.is_bookmarked(self.state.verb, self.state.language):
            self.query_one("#bookmark-indicator").update("★")
        else:
            self.query_one("#bookmark-indicator").update("☆")

    def conjugate_verb(self, verb: str) -> None:
        try:
            result = self.engine.conjugate(verb, self.state.language)
            self.state.verb = verb
            
            # Update results table
            table = self.query_one(ResultsTable)
            # Use appropriate mode based on app mode
            mode = "RULE" if result.is_known else "ML"
            table.update_conjugation(
                verb=result.verb,
                conjugation=result.moods,
                confidence=result.confidence,
                mode=mode
            )
            
            # Update insights
            morph = self.analyzer.analyse(result)
            insights = self.query_one(InsightsPanel)
            
            # We need to bridge MorphResult to VerbMorphologySummary or just update InsightsPanel
            # For now let's use a dummy summary or fix InsightsPanel to accept MorphResult
            # InsightsPanel currently expects VerbMorphologySummary
            
            summary = VerbMorphologySummary(
                verb=verb,
                language=self.state.language,
                conjugation_class=morph.conjugation_class,
                moods=list(result.moods.keys()),
                tenses=list({t for m in result.moods.values() for t in m.keys()}),
                persons=list({p for m in result.moods.values() for t in m.values() for p in range(len(t))}),
                distinct_forms=len({f for m in result.moods.values() for t in m.values() for f in t if f != "?"}),
                filled_cells=sum(len(t) for m in result.moods.values() for t in m.values() if any(f != "?" for f in t)),
                missing_cells=morph.defective_count,
                irregular_proxy=morph.is_irregular,
                defective=bool(morph.defective_forms),
                productivity=None,
                defectiveness=morph.defective_count / 100.0, # approximation
                transitivity=morph.transitivity
            )
            insights.set_summary(summary, verb_root=morph.stem, verb_template=morph.template)
            
            # Update history
            self.session.add_history(verb, self.state.language)
            self._update_bookmark_indicator()
            
        except Exception as e:
            self.notify(f"Error conjugating {verb}: {str(e)}", severity="error")

    def update_suggestions(self, value: str) -> None:
        prefix = value.strip().lower()
        suggestions_widget = self.query_one(AutocompleteSuggestions)

        if not prefix:
            suggestions_widget.show_suggestions([])
            return

        suggestions = self.autocomplete.suggest(prefix, self.state.language)
        suggestions_widget.show_suggestions(suggestions)
