"""
state.py

Global state container for the mlconjug3 TUI application.
"""

from collections import deque


class TUIState:
    """
    Shared application state for the TUI.
    """

    def __init__(self):
        self.language: str = "fr"
        self.subject: str = "abbrev"

        # -------------------------
        # UX ENHANCEMENTS
        # -------------------------
        self.history = deque(maxlen=50)   # recent verbs
        self.favorites = set()

    def add_history(self, verb: str):
        if verb:
            self.history.appendleft(verb)

    def toggle_favorite(self, verb: str):
        if verb in self.favorites:
            self.favorites.remove(verb)
        else:
            self.favorites.add(verb)
