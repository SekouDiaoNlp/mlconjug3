"""
app.py

Working Textual TUI for mlconjug3.

Fixes:
- Proper widget lifecycle
- Explorer now mounts correctly
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, Static

from mlconjug3.mlconjug import Conjugator
from mlconjug3.tui.cache import ConjugationCache
from mlconjug3.tui.widgets.results_table import ResultsTable
from mlconjug3.tui.widgets.verb_browser import VerbBrowser, VerbSelected


class Mlconjug3TUI(App):
    """
    Main TUI application.
    """

    CSS_PATH = "theme.css"
    DEBOUNCE_DELAY = 0.25

    def __init__(self):
        super().__init__()

        self.conjugator = Conjugator(language="fr")
        self.cache = ConjugationCache()

        self._timer = None
        self.verbs = list(self.conjugator.conjug_manager.verbs.keys())

    def compose(self) -> ComposeResult:
        yield Header()

        with TabbedContent():

            # -------- CONJUGATE --------
            with TabPane("Conjugate"):
                yield Static("Live conjugation")
                yield Input(placeholder="Type a verb...", id="verb_input")
                yield ResultsTable(id="results")

            # -------- EXPLORER --------
            with TabPane("Explorer"):
                yield VerbBrowser(self.verbs)

            with TabPane("Batch"):
                yield Static("Batch mode coming soon")

            with TabPane("Settings"):
                yield Static("Settings coming soon")

        yield Footer()

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

        key = f"{self.conjugator.language}:{verb}:abbrev"

        def compute(_):
            return self.conjugator.conjugate(verb)

        result = self.cache.get(key, compute)

        table = self.query_one("#results", ResultsTable)
        if result:
            table.update_conjugation(verb, result.conjug_info)

    def on_verb_selected(self, message: VerbSelected):
        verb = message.verb

        result = self.conjugator.conjugate(verb)

        table = self.query_one("#explorer_results", ResultsTable)
        if result:
            table.update_conjugation(verb, result.conjug_info)


def main():
    Mlconjug3TUI().run()


if __name__ == "__main__":
    main()
