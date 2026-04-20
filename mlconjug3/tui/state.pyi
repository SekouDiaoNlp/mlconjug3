from collections import deque
from typing import Deque, Set


class TUIState:
    """
    Typed interface for mlconjug3 TUI state container.
    """

    language: str
    subject: str
    history: Deque[str]
    favorites: Set[str]

    def __init__(self) -> None: ...

    def add_history(self, verb: str) -> None: ...

    def toggle_favorite(self, verb: str) -> None: ...
