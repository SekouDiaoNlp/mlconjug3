"""
mlconjug3.tui.widgets.verb_shelf

Lightweight verb list widget used for History/Favorites shelves.

Unlike `VerbBrowser`, this widget is optimized for programmatic updates to the
underlying verb list (e.g., when history grows or favorites change).
"""

from __future__ import annotations

from typing import Any, Iterable

from textual.containers import Vertical
from textual.widgets import ListItem, ListView, Label, Static
from textual.app import ComposeResult

from mlconjug3.tui.widgets.verb_browser import VerbSelected


class VerbShelf(Vertical):
    """
    A simple titled verb list with selection messages.

    Parameters
    ----------
    title:
        Shelf title (e.g., "History", "Favorites").
    verbs:
        Initial verbs to display.
    """

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
        """
        Replace the shelf contents.

        Parameters
        ----------
        verbs:
            Verbs to render.
        """

        self._verbs = list(verbs)
        self.list_view.clear()
        for verb in self._verbs:
            item = ListItem(Label(verb))
            self.list_view.append(item)

    def on_mount(self) -> None:
        self.set_verbs(self._verbs)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Emit `VerbSelected` when a list item is selected.

        Parameters
        ----------
        event:
            Textual list selection event.
        """

        label = event.item.query_one(Label)
        verb = getattr(label, "renderable", str(label))
        self.post_message(VerbSelected(str(verb)))

