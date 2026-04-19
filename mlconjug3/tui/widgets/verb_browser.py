"""
verb_browser.py
"""

from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem, Label
from textual.message import Message


class VerbSelected(Message):
    def __init__(self, verb: str) -> None:
        super().__init__()
        self.verb = verb


class VerbBrowser(Vertical):
    def __init__(self, verbs: list[str], max_results: int = 100, **kwargs):
        super().__init__(**kwargs)

        self.verbs = sorted(verbs)
        self.max_results = max_results

        self.search_input = Input(placeholder="Search verb...")
        self.list_view = ListView()

    def compose(self):
        yield self.search_input
        yield self.list_view

    def on_mount(self) -> None:
        self._update_list(self.verbs[: self.max_results])

    def _update_list(self, verbs: list[str]) -> None:
        self.list_view.clear()

        for verb in verbs[: self.max_results]:
            # Store verb directly on the item (important fix)
            item = ListItem(Label(verb))
            item.verb = verb
            self.list_view.append(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip().lower()

        if not query:
            filtered = self.verbs[: self.max_results]
        else:
            filtered = [
                v for v in self.verbs if query in v
            ][: self.max_results]

        self._update_list(filtered)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Robust retrieval (no Label internals)
        item = event.item

        verb = getattr(item, "verb", None)
        if verb is None:
            label = item.query_one(Label)
            verb = str(label.renderable) if hasattr(label, "renderable") else label.plain

        self.post_message(VerbSelected(verb))
