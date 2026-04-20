from typing import Any, List, Optional
from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Select, Button

from mlconjug3.tui.state import TUIState
from mlconjug3.core.conjugation_service import ConjugationService
from mlconjug3.tui.cache import ConjugationCache


class Mlconjug3TUI(App):
    CSS_PATH: str
    DEBOUNCE_DELAY: float

    def __init__(self) -> None: ...

    state: TUIState
    service: ConjugationService
    cache: ConjugationCache

    verbs: List[str]

    def compose(self) -> ComposeResult: ...

    def _status_bar_text(self) -> str: ...

    def _refresh_status_bar(self) -> None: ...

    def _is_valid(self, verb: str) -> bool: ...

    def on_input_changed(self, event: Input.Changed) -> None: ...

    def _update_verb(self, verb: str) -> None: ...

    def on_verb_selected(self, message: Any) -> None: ...

    def on_input_submitted(self, event: Input.Submitted) -> None: ...

    def on_button_pressed(self, event: Button.Pressed) -> None: ...

    def _run_batch(self) -> None: ...

    def on_select_changed(self, event: Select.Changed) -> None: ...


def main() -> None: ...
