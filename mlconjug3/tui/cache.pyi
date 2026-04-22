from typing import Callable, Any, Optional


class ConjugationCache:
    """
    Typed interface for conjugation cache.
    """

    def __init__(self, maxsize: int = 512) -> None: ...

    _compute_fn: Optional[Callable[[str], Any]]

    def get(self, key: str, compute_fn: Callable[[str], Any]) -> Any: ...
