"""
mlconjug3.tui.widgets.suggest_dropdown

Suggestion dropdown widget for verb inputs.
"""

from __future__ import annotations

from typing import Any, Iterable

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import ListItem, ListView, Label, Static


class SuggestionItem(ListItem):
    """
    List item carrying a suggestion payload.
    """

    def __init__(self, value: str) -> None:
        super().__init__(Label(value))
        self.value: str = value


class SuggestionChosen(Message):
    """
    Emitted when a suggestion is selected.
    """

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value


class SuggestDropdown(Static):
    """
    A simple suggestion dropdown with a `ListView`.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.list_view = ListView()
        self._pending: list[str] = []

    def compose(self) -> ComposeResult:
        yield self.list_view

    def set_suggestions(self, values: Iterable[str]) -> None:
        """
        Replace suggestions.
        """
        pending = [str(v) for v in values]
        self._pending = pending

        try:
            self.list_view.clear()
            for v in pending:
                self.list_view.append(SuggestionItem(v))
        except LookupError:
            # Not mounted / no active app yet.
            return

    def on_mount(self) -> None:
        if self._pending:
            self.set_suggestions(self._pending)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        value = getattr(item, "value", None)
        if isinstance(value, str):
            self.post_message(SuggestionChosen(value))
