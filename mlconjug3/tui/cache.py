"""
cache.py

Lightweight memoization layer for verb conjugation results.

This module provides a thin wrapper around functools.lru_cache
to cache conjugation results for the TUI layer.

It is designed for:
- Reducing repeated ML inference calls
- Improving responsiveness in live verb input
- Keeping UI latency minimal

Design note:
------------
This cache binds a compute function dynamically at runtime.
The compute function is injected via `get()` and must remain
valid for the duration of cache access.
"""

from functools import lru_cache
from typing import Callable, Any, Optional


class ConjugationCache:
    """
    Lightweight LRU cache wrapper for conjugation computations.

    This class wraps functools.lru_cache but introduces a dynamic
    compute function binding mechanism.

    Warning
    -------
    The compute function is stored internally and used by the cached
    wrapper. Changing it between calls affects cached behavior.
    This design is intentional for flexible TUI integration, but
    requires careful usage.
    """

    def __init__(self, maxsize: int = 512) -> None:
        """
        Initialize the conjugation cache.

        Parameters
        ----------
        maxsize : int, optional
            Maximum number of cached entries (default is 512).
        """

        self._compute_fn: Optional[Callable[[str], Any]] = None

        @lru_cache(maxsize=maxsize)
        def _cache(key: str) -> Any:
            """
            Internal cached wrapper function.

            Parameters
            ----------
            key : str
                Cache key (typically a verb string).

            Returns
            -------
            Any
                Result of the compute function.
            """
            if self._compute_fn is None:
                raise RuntimeError("Compute function not initialized.")
            return self._compute_fn(key)

        self._cache = _cache

    def get(self, key: str, compute_fn: Callable[[str], Any]) -> Any:
        """
        Retrieve a cached or computed result.

        If the key is not cached, the provided compute function
        will be used and its result stored in the cache.

        Parameters
        ----------
        key : str
            Cache lookup key (typically a verb).
        compute_fn : Callable[[str], Any]
            Function used to compute the value if missing.

        Returns
        -------
        Any
            Cached or computed result.
        """

        self._compute_fn = compute_fn
        return self._cache(key)
