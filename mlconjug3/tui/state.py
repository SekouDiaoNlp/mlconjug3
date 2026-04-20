"""
state.py

Global state container for the mlconjug3 TUI application.

This module defines a lightweight state manager used across the
Textual-based terminal UI. It tracks user preferences, navigation
history, and interactive session data such as favorites.

The state object is intentionally simple and framework-agnostic,
allowing it to be safely reused across UI components without coupling.
"""

from collections import deque
from typing import Deque, Set


class TUIState:
    """
    Shared application state for the mlconjug3 TUI.

    This class acts as a centralized in-memory store for:
    - User-selected language
    - Conjugation display mode (subject format)
    - Recently accessed verbs (history)
    - Favorite verbs

    It is designed to be lightweight and mutable, with no persistence
    layer by default.
    """

    def __init__(self) -> None:
        """
        Initialize the TUI state container with default values.
        """

        self.language: str = "fr"
        self.subject: str = "abbrev"

        self.history: Deque[str] = deque(maxlen=50)
        self.favorites: Set[str] = set()

    def add_history(self, verb: str) -> None:
        """
        Add a verb to the recent history list.

        The history is stored as a bounded deque (max length 50),
        ensuring old entries are automatically discarded.

        Parameters
        ----------
        verb : str
            The verb to record in history.
        """
        if verb:
            self.history.appendleft(verb)

    def toggle_favorite(self, verb: str) -> None:
        """
        Toggle the favorite status of a verb.

        If the verb is already marked as favorite, it will be removed.
        Otherwise, it will be added to the favorites set.

        Parameters
        ----------
        verb : str
            The verb to toggle in the favorites collection.
        """
        if verb in self.favorites:
            self.favorites.remove(verb)
        else:
            self.favorites.add(verb)
