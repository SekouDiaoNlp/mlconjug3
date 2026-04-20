from __future__ import annotations

from typing import Any, List, ClassVar

from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Button

from mlconjug3.tui.state import TUIState
from mlconjug3.core.conjugation_service import ConjugationService
from mlconjug3.tui.cache import ConjugationCache


class Mlconjug3TUI(App[None]):
    """
    Typed interface for the mlconjug3 TUI application.
    """

    CSS_PATH: ClassVar[str]
    DEBOUNCE_DELAY: ClassVar[float]

    state: TUIState
    service: ConjugationService
    cache: ConjugationCache

    verbs: List[str]

    def __init__(self) -> None: ...

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
