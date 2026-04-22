"""
mlconjug3.tui.widgets.filter_bar

Global multi-select filtering widget for conjugation views.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import SelectionList, Static


@dataclass(frozen=True, slots=True)
class FilterState:
    """
    Snapshot of selected filter values.
    """

    moods: set[str]
    tenses: set[str]


class FiltersChanged(Message):
    """
    Emitted when filters change.
    """

    def __init__(self, state: FilterState) -> None:
        super().__init__()
        self.state = state


class FilterBar(Horizontal):
    """
    Global filter bar (moods + tenses) using multi-select lists.
    """

    def __init__(
        self,
        *,
        moods: Iterable[str] = (),
        tenses: Iterable[str] = (),
        selected_moods: Iterable[str] = (),
        selected_tenses: Iterable[str] = (),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._moods = list(moods)
        self._tenses = list(tenses)
        self._selected_moods = set(selected_moods)
        self._selected_tenses = set(selected_tenses)

        self.mood_list: SelectionList[str] = SelectionList(id="mood_filters")
        self.tense_list: SelectionList[str] = SelectionList(id="tense_filters")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Moods", classes="title")
            yield self.mood_list
        with Vertical():
            yield Static("Tenses", classes="title")
            yield self.tense_list

    def on_mount(self) -> None:
        self.set_options(self._moods, self._tenses)
        self.set_selected(self._selected_moods, self._selected_tenses)

    def set_options(self, moods: Iterable[str], tenses: Iterable[str]) -> None:
        """
        Replace available filter options.
        """

        self._moods = list(moods)
        self._tenses = list(tenses)
        self.mood_list.clear_options()
        self.tense_list.clear_options()
        for m in self._moods:
            self.mood_list.add_option((str(m), str(m).lower()))
        for t in self._tenses:
            self.tense_list.add_option((str(t), str(t).lower()))

    def set_selected(self, moods: Iterable[str], tenses: Iterable[str]) -> None:
        """
        Set selected filters.
        """

        self._selected_moods = {str(m).lower() for m in moods}
        self._selected_tenses = {str(t).lower() for t in tenses}
        self.mood_list.deselect_all()
        self.tense_list.deselect_all()
        for key in self._selected_moods:
            self.mood_list.select(key)
        for key in self._selected_tenses:
            self.tense_list.select(key)

        self.post_message(self._build_message())

    def _build_message(self) -> FiltersChanged:
        moods = set(self.mood_list.selected)
        tenses = set(self.tense_list.selected)
        return FiltersChanged(FilterState(moods=moods, tenses=tenses))

    def on_selection_list_selected_changed(self, _event: SelectionList.SelectedChanged[Any]) -> None:
        self.post_message(self._build_message())

