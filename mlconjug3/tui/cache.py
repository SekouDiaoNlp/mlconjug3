"""
cache.py

Lightweight in-memory cache for TUI performance optimization.

This avoids recomputing conjugations for the same verb repeatedly,
which is especially important for live typing and Explorer mode.
"""

from functools import lru_cache


class ConjugationCache:
    """
    Simple LRU-based cache for conjugation results.
    """

    def __init__(self, maxsize: int = 512):
        self._cache = lru_cache(maxsize=maxsize)(self._compute)

    def get(self, key, compute_fn):
        """
        Retrieve cached result or compute it.

        Parameters
        ----------
        key : str
            Cache key (verb + language + subject)
        compute_fn : callable
            Function to compute result if missing

        Returns
        -------
        Any
            Cached or computed conjugation result
        """
        self._compute_fn = compute_fn
        return self._cache(key)

    def _compute(self, key):
        return self._compute_fn(key)
