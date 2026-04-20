"""
app.py

Improved TUI:
- Global status bar
- Verb history tracking
- State integration
- Cleaner explorer UX
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, Static, Button, Select
from textual.containers import Horizontal, Vertical, VerticalScroll

from mlconjug3.core.conjugation_service import ConjugationService
from mlconjug3.tui.cache import ConjugationCache
from mlconjug3.tui.widgets.results_table import ResultsTable
from mlconjug3.tui.widgets.verb_browser import VerbBrowser, VerbSelected
from mlconjug3.tui.state import TUIState


class Mlconjug3TUI(App):
    """
    Main TUI application.
    """

    CSS_PATH = "theme.css"
    DEBOUNCE_DELAY = 0.25

    def __init__(self):
        super().__init__()

        self.state = TUIState()
        self.service = ConjugationService(language="fr")
        self.cache = ConjugationCache()

        self._timer = None
        self.verbs = list(self.service.conjugator.conjug_manager.verbs.keys())

    # ---------------- UI ----------------
    def compose(self) -> ComposeResult:

        yield Header()

        # ---------------- STATUS BAR ----------------
        yield Static(
            self._status_bar_text(),
            id="status_bar"
        )

        with TabbedContent():

            # ---------------- CONJUGATE ----------------
            with TabPane("Conjugate"):
                yield Static("Live conjugation", classes="title")

                yield Input(
                    placeholder="Type a verb...",
                    id="verb_input"
                )

                yield ResultsTable(id="results")

            # ---------------- EXPLORER ----------------
            with TabPane("Explorer"):

                with Horizontal():

                    with Vertical(classes="panel"):
                        yield Static("Verb Explorer", classes="title")
                        yield VerbBrowser(self.verbs)

                    with Vertical(classes="panel"):
                        yield Static("Verb Details", classes="title")

                        with VerticalScroll(id="explorer_scroll"):
                            yield ResultsTable(id="explorer_results")

            # ---------------- BATCH ----------------
            with TabPane("Batch"):
                yield Static("Enter verbs separated by spaces or commas")

                yield Input(
                    placeholder="aller, manger, finir",
                    id="batch_input"
                )

                yield Button("Run batch", id="run_batch")
                yield ResultsTable(id="batch_results")

            # ---------------- SETTINGS ----------------
            with TabPane("Settings"):

                yield Static("Language")

                yield Select(
                    options=[
                        ("French", "fr"),
                        ("English", "en"),
                        ("Spanish", "es"),
                        ("Italian", "it"),
                        ("Portuguese", "pt"),
                        ("Romanian", "ro"),
                    ],
                    value="fr",
                    id="lang_select",
                )

                yield Static("Subject format")

                yield Select(
                    options=[
                        ("Abbrev", "abbrev"),
                        ("Pronoun", "pronoun"),
                    ],
                    value="abbrev",
                    id="subject_select",
                )

        yield Footer()

    # ---------------- STATUS BAR ----------------
    def _status_bar_text(self) -> str:
        return (
            f"LANG: {self.state.language.upper()} | "
            f"MODE: {self.state.subject.upper()} | "
            f"HISTORY: {len(self.state.history)}"
        )

    def _refresh_status_bar(self):
        bar = self.query_one("#status_bar", Static)
        bar.update(self._status_bar_text())

    # ---------------- EXPLORER ----------------
    def on_verb_selected(self, message: VerbSelected):
        verb = message.verb

        self.state.add_history(verb)
        self._refresh_status_bar()

        result = self.service.conjugate(verb)
        if not result:
            return

        table = self.query_one("#explorer_results", ResultsTable)
        table.update_conjugation(verb, result.conjug_info)

    # ---------------- LIVE ----------------
    def on_input_changed(self, event: Input.Changed):
        if event.input.id != "verb_input":
            return

        verb = event.value.strip()

        if self._timer:
            self._timer.stop()

        self._timer = self.set_timer(
            self.DEBOUNCE_DELAY,
            lambda: self._update_verb(verb),
        )

    def _update_verb(self, verb: str):
        if not verb:
            return

        def compute(_):
            return self.service.conjugate(verb)

        result = self.cache.get(verb, compute)

        table = self.query_one("#results", ResultsTable)

        if result:
            self.state.add_history(verb)
            self._refresh_status_bar()

            table.update_conjugation(
                verb,
                result.conjug_info
            )

    # ---------------- BATCH ----------------
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "run_batch":
            return

        input_widget = self.query_one("#batch_input", Input)

        verbs = [
            v.strip()
            for v in input_widget.value.replace(",", " ").split()
            if v.strip()
        ]

        results_table = self.query_one("#batch_results", ResultsTable)

        for verb in verbs:
            result = self.service.conjugate(verb)
            if result:
                results_table.update_conjugation(
                    verb,
                    result.conjug_info,
                    append=True
                )

    # ---------------- SETTINGS ----------------
    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "lang_select":
            self.service.set_language(event.value)
            self.state.language = event.value
            self.verbs = list(self.service.conjugator.conjug_manager.verbs.keys())

            self._refresh_status_bar()

        elif event.select.id == "subject_select":
            self.service.subject = event.value
            self.state.subject = event.value

            self._refresh_status_bar()


def main():
    Mlconjug3TUI().run()


if __name__ == "__main__":
    main()
