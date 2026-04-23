"""
mlconjug3.tui.learn.engine

Guided learning engine for the TUI.

This module implements a small deterministic state machine that can be
driven by UI events:

- pickVerb -> revealKeyForms -> quizPrompt -> revealAnswer -> next
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


ConjugationTable = Mapping[str, Any]


class LearnStep(str, Enum):
    """
    Guided learning steps.
    """

    PICK_VERB = "pickVerb"
    REVEAL_KEY_FORMS = "revealKeyForms"
    QUIZ_PROMPT = "quizPrompt"
    REVEAL_ANSWER = "revealAnswer"


@dataclass(frozen=True, slots=True)
class LearnQuiz:
    """
    A single quiz question.

    Attributes
    ----------
    mood:
        Target mood.
    tense:
        Target tense.
    person:
        Target person label.
    answer:
        Correct form (may be '?' when missing).
    """

    mood: str
    tense: str
    person: str
    answer: str


def _safe_str(value: Any) -> str:
    if value is None:
        return "?"
    s = str(value).strip()
    return s if s else "?"


def build_quiz(table: ConjugationTable, seed: int) -> Optional[LearnQuiz]:
    """
    Build a deterministic quiz item from a conjugation table.

    Parameters
    ----------
    table:
        Conjugation table (mood -> tense -> persons).
    seed:
        Deterministic seed.

    Returns
    -------
    LearnQuiz | None
        Quiz item if table contains a dict-shaped cell.
    """

    items: list[tuple[str, str, str, str]] = []
    for mood, tenses in table.items():
        if not isinstance(tenses, Mapping):
            continue
        for tense, persons in tenses.items():
            if not isinstance(persons, Mapping):
                continue
            for person, form in persons.items():
                items.append((str(mood), str(tense), str(person), _safe_str(form)))

    if not items:
        return None

    idx = seed % len(items)
    mood, tense, person, answer = items[idx]
    return LearnQuiz(mood=mood, tense=tense, person=person, answer=answer)

