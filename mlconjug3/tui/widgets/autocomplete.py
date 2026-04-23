from textual.widget import Widget
from textual.widgets import ListView


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
            self.append(s)

        self.add_class("visible")
