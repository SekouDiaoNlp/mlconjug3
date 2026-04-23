"""
mlconjug3.core.morphology.summary
Lightweight morphology summary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


ConjugationTable = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class VerbMorphologySummary:
    moods: list[str]
    tenses: list[str]
    persons: list[str]
    distinct_forms: int
    filled_cells: int
    missing_cells: int
    productivity: Optional[float]
    conjugation_class: Optional[str]
    defectiveness: Optional[float]
    defective: bool
    transitivity: Optional[str]
    irregular_proxy: bool


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() in ("", "?"))


def summarize(*, language: str, infinitive: str, table: ConjugationTable, irregular_proxy: bool):
    moods, tenses, persons = set(), set(), set()
    filled = missing = 0
    forms = set()

    for mood, mood_val in table.items():
        moods.add(mood)
        if not isinstance(mood_val, Mapping):
            continue
        for tense, tense_val in mood_val.items():
            tenses.add(tense)
            if not isinstance(tense_val, Mapping):
                continue
            for person, form in tense_val.items():
                persons.add(str(person))
                if _is_missing(form):
                    missing += 1
                else:
                    filled += 1
                    forms.add(str(form))

    denom = filled + missing
    return VerbMorphologySummary(
        moods=sorted(moods),
        tenses=sorted(tenses),
        persons=sorted(persons),
        distinct_forms=len(forms),
        filled_cells=filled,
        missing_cells=missing,
        productivity=(filled / denom) if denom else None,
        conjugation_class=None,
        defectiveness=(missing / denom) if denom else None,
        defective=(missing / denom) >= 0.25 if denom else False,
        transitivity=None,
        irregular_proxy=irregular_proxy,
    )
