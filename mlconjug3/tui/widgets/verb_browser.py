"""
verb_browser.py

Interactive verb browser widget for Explorer mode.

Fix:
- Uses compose() instead of append() in __init__
- Compatible with Textual lifecycle
"""

from textual.widgets import ListView, ListItem, Label
from textual.message import Message


class VerbSelected(Message):
    """
    Message emitted when a verb is selected.
    """

    def __init__(self, verb: str) -> None:
        self.verb = verb
        super().__init__()


class VerbBrowser(ListView):
    """
    Scrollable list of verbs with selection support.

    Parameters
    ----------
    verbs : iterable of str
        Verbs to display.
    irregular_verbs : set of str, optional
        Verbs to highlight.
    """

    def __init__(self, verbs, irregular_verbs=None, **kwargs):
        super().__init__(**kwargs)

        self.verbs = sorted(verbs)
        self.irregular_verbs = irregular_verbs or set()

    def compose(self):
        """
        Proper Textual composition lifecycle.
        """
        for verb in self.verbs:
            style = "bold red" if verb in self.irregular_verbs else ""
            yield ListItem(Label(verb, classes=style))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """
        Handle selection event.
        """
        label = event.item.query_one(Label)
        verb = label.renderable
        self.post_message(VerbSelected(str(verb)))
