"""
mlconjug3.tui.lexicon

Optional lightweight verb lexicon for the Textual TUI.

This module is UI-only: it provides fast metadata lookups that enrich the
exploration experience (transitivity, valency, auxiliaries, registers, etc.).
When a verb isn't present, callers must treat the metadata as unknown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True, slots=True)
class VerbLexiconEntry:
    """
    UI-facing verb metadata entry.

    Attributes
    ----------
    infinitive:
        Canonical infinitive key (lowercase).
    transitivity:
        "transitive", "intransitive", "ditransitive", or None if unknown.
    valency_frames:
        Short human-readable frames such as "SUBJ + OBJ" or "SUBJ + OBJ + IO".
    auxiliaries:
        Auxiliary verbs used to build compound tenses when relevant (e.g., French
        "avoir"/"être"). Empty when unknown / not applicable.
    reflexive:
        True when verb is reflexive-only in the lexicon, False when explicitly
        non-reflexive, None when unknown.
    registers:
        Register/usage labels, e.g. {"formal", "colloquial", "slang"}.
    frequency:
        Optional relative frequency score in [0..1] when available.
    """

    infinitive: str
    transitivity: Optional[str] = None
    valency_frames: tuple[str, ...] = ()
    auxiliaries: tuple[str, ...] = ()
    reflexive: Optional[bool] = None
    registers: frozenset[str] = frozenset()
    frequency: Optional[float] = None


_LEX_FR: dict[str, VerbLexiconEntry] = {
    "aller": VerbLexiconEntry(
        infinitive="aller",
        transitivity="intransitive",
        valency_frames=("SUBJ", "SUBJ + OBL"),
        auxiliaries=("être",),
        reflexive=False,
        registers=frozenset({"common"}),
        frequency=0.98,
    ),
    "manger": VerbLexiconEntry(
        infinitive="manger",
        transitivity="transitive",
        valency_frames=("SUBJ + OBJ",),
        auxiliaries=("avoir",),
        reflexive=False,
        registers=frozenset({"common"}),
        frequency=0.86,
    ),
    "finir": VerbLexiconEntry(
        infinitive="finir",
        transitivity="transitive",
        valency_frames=("SUBJ + OBJ",),
        auxiliaries=("avoir",),
        reflexive=False,
        registers=frozenset({"common"}),
        frequency=0.70,
    ),
}


def lookup(language: str, infinitive: str) -> Optional[VerbLexiconEntry]:
    """
    Lookup a verb metadata entry.

    Parameters
    ----------
    language:
        Language code.
    infinitive:
        Verb infinitive key.

    Returns
    -------
    VerbLexiconEntry | None
        Entry when present, otherwise None.
    """

    lang = (language or "").lower().strip()
    key = (infinitive or "").lower().strip()
    if not key:
        return None
    if lang == "fr":
        return _LEX_FR.get(key)
    return None


def known_verbs(language: str) -> Iterable[str]:
    """
    Return all verbs known to this lexicon for a language.
    """

    lang = (language or "").lower().strip()
    if lang == "fr":
        return tuple(_LEX_FR.keys())
    return ()

