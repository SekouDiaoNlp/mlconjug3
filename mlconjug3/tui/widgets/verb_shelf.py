from __future__ import annotations

from typing import Any, Iterable

from textual.containers import Vertical
from textual.widgets import ListItem, ListView, Label, Static
from textual.app import ComposeResult

from mlconjug3.tui.widgets.verb_browser import VerbSelected


class VerbShelf(Vertical):
    def __init__(self, title: str, verbs: Iterable[str] = (), **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._title_text = title
        self._verbs: list[str] = list(verbs)

        self._title = Static(title, classes="title")
        self.list_view = ListView()

    def compose(self) -> ComposeResult:
        yield self._title
        yield self.list_view

    def set_verbs(self, verbs: Iterable[str]) -> None:
        self._verbs = list(verbs)
        self.list_view.clear()

        for verb in self._verbs:
            self.list_view.append(ListItem(Label(verb)))

    def on_mount(self) -> None:
        self.set_verbs(self._verbs)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        label = item.query_one(Label)
        verb = getattr(label, "renderable", None) or str(label)
        self.post_message(VerbSelected(str(verb)))
