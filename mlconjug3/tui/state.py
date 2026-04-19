"""
state.py

Global state container for the mlconjug3 TUI application.

This module stores UI-level state such as selected language,
subject format, and cached conjugation results.
"""


class TUIState:
    """
    Shared application state for the TUI.

    This is intentionally lightweight and framework-agnostic.
    """

    def __init__(self):
        self.language: str = "fr"
        self.subject: str = "abbrev"
        self.cache = {}
