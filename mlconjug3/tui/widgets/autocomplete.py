from __future__ import annotations
from textual.widgets import ListView, ListItem, Label


class AutocompleteSuggestions(ListView):
    """
    Simple suggestion list for verb autocomplete.
    """

    def show_suggestions(self, suggestions: list[str]) -> None:
        self.clear()

        if not suggestions:
            self.remove_class("visible")
            return

        for s in suggestions:
            self.append(ListItem(Label(s)))

        self.add_class("visible")
