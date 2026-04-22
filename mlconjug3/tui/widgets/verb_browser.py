"""
verb_browser.py

Interactive verb exploration widget for the mlconjug3 TUI.

This module provides a searchable list-based browser for verbs,
allowing users to quickly filter and select verbs for conjugation.

It is designed for:
- Fast keyboard-driven search
- Low-latency filtering
- Seamless integration with the conjugation pipeline

The widget emits a VerbSelected message when a verb is chosen.
"""

from typing import List, Any

from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem, Label
from textual.message import Message
from textual import events

from mlconjug3.tui.search.fuzzy import suggest


class VerbListItem(ListItem):
    """
    List item carrying a verb payload.

    Attributes
    ----------
    verb:
        Verb represented by this list item.
    """

    def __init__(self, verb: str) -> None:
        super().__init__(Label(verb))
        self.verb: str = verb


class VerbSelected(Message):
    """
    Message emitted when a verb is selected in the browser.

    Attributes
    ----------
    verb : str
        The selected verb string.
    """

    def __init__(self, verb: str) -> None:
        """
        Initialize the VerbSelected message.

        Parameters
        ----------
        verb : str
            The verb that was selected by the user.
        """
        super().__init__()
        self.verb: str = verb


class VerbBrowser(Vertical):
    """
    Searchable verb browser widget.

    This widget displays a filtered list of verbs and allows users
    to select one for conjugation.

    Features
    --------
    - Real-time filtering via search input
    - Keyboard-friendly selection
    - Configurable maximum result size
    """

    def __init__(self, verbs: List[str], max_results: int = 100, **kwargs: Any) -> None:
        """
        Initialize the VerbBrowser widget.

        Parameters
        ----------
        verbs : list of str
            Full list of available verbs.
        max_results : int, optional
            Maximum number of verbs displayed at once (default is 100).
        **kwargs :
            Additional arguments passed to the parent widget.
        """

        super().__init__(**kwargs)

        self.verbs: List[str] = sorted(verbs)
        self.max_results: int = max_results

        self.search_input: Input = Input(placeholder="Search verb...")
        self.list_view: ListView = ListView()

    def compose(self):
        """
        Compose child widgets.

        Returns
        -------
        Generator
            Yielded child widgets for the layout.
        """

        yield self.search_input
        yield self.list_view

    def on_mount(self) -> None:
        """
        Called when the widget is mounted.

        Initializes the verb list with default entries.
        """

        self._update_list(self.verbs[: self.max_results])

    def _update_list(self, verbs: List[str]) -> None:
        """
        Update the displayed verb list.

        Parameters
        ----------
        verbs : list of str
            Filtered list of verbs to display.
        """

        self.list_view.clear()

        for verb in verbs[: self.max_results]:
            self.list_view.append(VerbListItem(verb))

    def on_input_changed(self, event: Input.Changed) -> None:
        """
        Handle search input changes.

        Parameters
        ----------
        event : Input.Changed
            Event containing the updated input value.
        """

        query = event.value.strip().lower()

        if not query:
            filtered = self.verbs[: self.max_results]
        else:
            filtered = suggest(self.verbs, query, limit=self.max_results)

        self._update_list(filtered)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Handle verb selection from the list.

        Parameters
        ----------
        event : ListView.Selected
            Selection event from the ListView.
        """

        item = event.item
        verb = getattr(item, "verb", None)
        if isinstance(verb, str):
            self.post_message(VerbSelected(verb))
            return
        label = item.query_one(Label)
        self.post_message(VerbSelected(str(getattr(label, "renderable", str(label)))))
