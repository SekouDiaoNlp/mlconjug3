"""
mlconjug3.tui.search.fuzzy

Dependency-free fuzzy matching for verb suggestions.

The TUI needs fast, deterministic suggestions without adding new
dependencies. This module provides a small ranking function optimized for
interactive filtering:

- prefix matches rank highest
- substring matches rank next
- subsequence matches (characters in order) rank last
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class FuzzyMatch:
    """
    Ranked match result.

    Attributes
    ----------
    candidate:
        The matched string.
    score:
        Sort key; lower is better.
    """

    candidate: str
    score: tuple[int, int, int]


def _subsequence_span(candidate: str, query: str) -> int | None:
    """
    Return the span length of a subsequence match or None if not a match.

    Parameters
    ----------
    candidate:
        Candidate string.
    query:
        Query string.

    Returns
    -------
    int | None
        Span length for the first subsequence match, or None.
    """

    if not query:
        return 0

    it = iter(range(len(candidate)))
    start: int | None = None
    last: int | None = None
    ci = 0

    for qc in query:
        found = False
        for i in range(ci, len(candidate)):
            if candidate[i] == qc:
                if start is None:
                    start = i
                last = i
                ci = i + 1
                found = True
                break
        if not found:
            return None

    assert start is not None and last is not None
    return last - start + 1


def suggest(candidates: Iterable[str], query: str, *, limit: int = 20) -> list[str]:
    """
    Return ranked suggestions for a query.

    Parameters
    ----------
    candidates:
        Candidate strings to search.
    query:
        Search query.
    limit:
        Maximum number of suggestions.

    Returns
    -------
    list[str]
        Suggestions ranked best-first.
    """

    q = query.strip().lower()
    if not q:
        return []

    matches: list[FuzzyMatch] = []
    for cand in candidates:
        c = cand.lower()

        if c.startswith(q):
            matches.append(FuzzyMatch(cand, (0, 0, len(c))))
            continue

        idx = c.find(q)
        if idx != -1:
            matches.append(FuzzyMatch(cand, (1, idx, len(c))))
            continue

        span = _subsequence_span(c, q)
        if span is not None:
            matches.append(FuzzyMatch(cand, (2, span, len(c))))

    matches.sort(key=lambda m: m.score)
    return [m.candidate for m in matches[:limit]]

