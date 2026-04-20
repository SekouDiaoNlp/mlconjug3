from typing import List, Optional, Any
from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem
from textual.message import Message


class VerbSelected(Message):
    """
    Typed message emitted when a verb is selected.
    """

    verb: str

    def __init__(self, verb: str) -> None: ...


class VerbBrowser(Vertical):
    """
    Typed interface for VerbBrowser widget.
    """

    verbs: List[str]
    max_results: int

    search_input: Input
    list_view: ListView

    def __init__(self, verbs: List[str], max_results: int = 100, **kwargs: Any) -> None: ...

    def compose(self): ...

    def on_mount(self) -> None: ...

    def _update_list(self, verbs: List[str]) -> None: ...

    def on_input_changed(self, event: Input.Changed) -> None: ...

    def on_list_view_selected(self, event: ListView.Selected) -> None: ...
