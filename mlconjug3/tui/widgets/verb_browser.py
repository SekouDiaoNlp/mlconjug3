"""
verb_browser.py

High-performance verb browser widget for mlconjug3 TUI.

This widget provides:
- Lazy rendering (no full dataset mount)
- Incremental filtering via search input
- Fast ListView updates (bounded result set)
- Event-driven verb selection

Designed for large linguistic datasets (thousands of verbs)
without UI lag.
"""

from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem, Label
from textual.message import Message


class VerbSelected(Message):
    """
    Message emitted when a verb is selected in the browser.

    Attributes
    ----------
    verb : str
        Selected verb.
    """

    def __init__(self, verb: str) -> None:
        super().__init__()
        self.verb = verb


class VerbBrowser(Vertical):
    """
    Optimized verb browser with search + lazy rendering.

    Parameters
    ----------
    verbs : list[str]
        Full list of verbs.
    max_results : int, default=100
        Maximum number of verbs displayed at once.
    """

    def __init__(self, verbs: list[str], max_results: int = 100, **kwargs):
        super().__init__(**kwargs)

        self.verbs = sorted(verbs)
        self.filtered_verbs = self.verbs[:max_results]
        self.max_results = max_results

        self.search_input = Input(placeholder="Search verb...", id="verb-search")
        self.list_view = ListView(id="verb-list")

    def compose(self):
        """
        Compose child widgets.
        """
        yield self.search_input
        yield self.list_view

    def on_mount(self) -> None:
        """
        Initialize list after mounting.
        """
        self._update_list(self.filtered_verbs)

    def _update_list(self, verbs: list[str]) -> None:
        """
        Efficiently update the ListView content.

        Parameters
        ----------
        verbs : list[str]
            Verbs to display.
        """
        self.list_view.clear()

        for verb in verbs[: self.max_results]:
            self.list_view.append(ListItem(Label(verb)))

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handle live search filtering.

        Parameters
        ----------
        event : Input.Changed
            Input change event.
        """
        query = event.value.strip().lower()

        if not query:
            self.filtered_verbs = self.verbs[: self.max_results]
        else:
            self.filtered_verbs = [
                v for v in self.verbs if query in v
            ][: self.max_results]

        self._update_list(self.filtered_verbs)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Emit selected verb event.

        Parameters
        ----------
        event : ListView.Selected
            Selection event.
        """
        label = event.item.query_one(Label)
        verb = label.renderable

        self.post_message(VerbSelected(verb))
