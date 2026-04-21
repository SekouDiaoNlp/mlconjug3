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

from typing import Optional, List, Any

from textual.app import App, ComposeResult
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

from mlconjug3.core.conjugation_service import ConjugationService
from mlconjug3.core.options import LANGUAGE_OPTIONS, SUBJECT_OPTIONS
from mlconjug3.tui.cache import ConjugationCache
from mlconjug3.tui.widgets.results_table import ResultsTable
from mlconjug3.tui.widgets.verb_browser import VerbBrowser, VerbSelected
from mlconjug3.tui.state import TUIState


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

    service : ConjugationService
        Backend service handling conjugation logic.

    cache : ConjugationCache
        LRU cache for conjugation results.
    """

    CSS_PATH: str = "theme.css"
    DEBOUNCE_DELAY: float = 0.25

    def __init__(self) -> None:
        """
        Initialize the TUI application and core services.
        """
        super().__init__()

        self.state: TUIState = TUIState()
        self.service: ConjugationService = ConjugationService(language="fr")
        self.cache: ConjugationCache = ConjugationCache()

        self._timer: Optional[Any] = None
        self._last_valid: Optional[str] = None

        self.verbs: List[str] = self.service.list_verbs()

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

        with TabbedContent():

            # ---------------- CONJUGATE ----------------
            with TabPane("Conjugate"):
                yield Static("Live conjugation", classes="title")

                yield Input(placeholder="Type a verb...", id="verb_input")
                yield Static("", id="input_feedback", markup=False)
                yield ResultsTable(id="results")

            # ---------------- EXPLORER ----------------
            with TabPane("Explorer"):

                with Horizontal():

                    with Vertical(classes="panel left-panel"):
                        yield Static("Verb Explorer", classes="title")
                        yield VerbBrowser(self.verbs)

                    with Vertical(classes="panel right-panel"):
                        yield Static("Verb Details", classes="title")

                        with VerticalScroll(id="explorer_scroll"):
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
        return (
            f"LANG: {self.state.language.upper()} | "
            f"MODE: {self.state.subject.upper()} | "
            f"HISTORY: {len(self.state.history)}"
        )

    def _refresh_status_bar(self) -> None:
        """
        Refresh the status bar display.
        """
        self.query_one("#status_bar", Static).update(self._status_bar_text())

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

        if self._timer:
            self._timer.stop()

        self._timer = self.set_timer(
            self.DEBOUNCE_DELAY,
            lambda: self._update_verb(verb),
        )

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
            feedback.update(f"Invalid verb: {verb}")
            table.clear()
            return

        feedback.update("")

        result = self.cache.get(verb, lambda _: self.service.conjugate(verb))

        if result:
            verb_obj = result[0] if isinstance(result, list) else result

            self.state.add_history(verb)
            self._refresh_status_bar()

            table.update_conjugation(
                verb,
                verb_obj.conjug_info,
                mode="ML" if getattr(verb_obj, "predicted", False) else "RULE",
                confidence=getattr(verb_obj, "confidence_score", None),
            )

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

        result = self.service.conjugate(verb)
        if not result:
            return

        self.query_one("#explorer_results", ResultsTable).update_conjugation(
            verb, result.conjug_info
        )

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

        for verb in verbs:
            if not self._is_valid(verb):
                continue

            result = self.service.conjugate(verb)

            if result:
                verb_obj = result[0] if isinstance(result, list) else result

                results_table.update_conjugation(
                    verb,
                    verb_obj.conjug_info,
                    append=True,
                    mode="ML" if getattr(verb_obj, "predicted", False) else "RULE",
                    confidence=getattr(verb_obj, "confidence_score", None),
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

        elif event.select.id == "subject_select":
            self.service.set_subject(event.value)
            self.state.subject = event.value
            self._refresh_status_bar()


def main() -> None:
    """
    Entry point for the TUI application.
    """
    Mlconjug3TUI().run()


if __name__ == "__main__":
    main()
