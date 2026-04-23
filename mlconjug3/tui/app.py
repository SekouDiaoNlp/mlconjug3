from __future__ import annotations

import re

from textual.app import App, ComposeResult
from textual.widgets import Input, Static
from textual.containers import Vertical

from .engine import VerbAutocompleteEngine
from .widgets import AutocompleteSuggestions
from .state import AppState, UIPreferences


def _safe_id(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9_-]", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "item"


class MLConjug3App(App):
    CSS_PATH = "app.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.prefs = UIPreferences.load()
        self.autocomplete = VerbAutocompleteEngine()

    # ------------------------------------------------------------------
    # UI LAYOUT (THIS WAS MISSING ❌)
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("mlconjug3 TUI", id="title"),
            Input(placeholder="Type a verb (e.g. manger)", id="verb-input"),
            AutocompleteSuggestions(id="suggestions"),
            id="main"
        )

    # ------------------------------------------------------------------
    # INIT STATE
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self.state.language = self.prefs.default_language
        self.state.mode = self.prefs.default_mode

    # ------------------------------------------------------------------
    # INPUT EVENTS
    # ------------------------------------------------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_suggestions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.state.verb = event.value.strip()

    # ------------------------------------------------------------------
    # AUTOCOMPLETE
    # ------------------------------------------------------------------

    def update_suggestions(self, value: str) -> None:
        prefix = value.strip().lower()

        suggestions_widget = self.query_one(AutocompleteSuggestions)

        if not prefix:
            suggestions_widget.show_suggestions([])
            return

        suggestions = self.autocomplete.suggest(prefix, self.state.language)
        suggestions_widget.show_suggestions(suggestions)
