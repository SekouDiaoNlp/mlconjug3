"""
cache.py
"""

from functools import lru_cache


class ConjugationCache:
    def __init__(self, maxsize: int = 512):
        self._compute_fn = None

        @lru_cache(maxsize=maxsize)
        def _cache(key):
            return self._compute_fn(key)

        self._cache = _cache

    def get(self, key, compute_fn):
        self._compute_fn = compute_fn
        return self._cache(key)
