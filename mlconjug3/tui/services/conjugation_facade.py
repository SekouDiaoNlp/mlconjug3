"""
mlconjug3.tui.services.conjugation_facade

UI-facing conjugation facade for the Textual TUI.

The TUI must remain event-driven and non-blocking. This module provides a
small, strictly-typed surface that:

- delegates all conjugation execution to the existing service layer
  (`mlconjug3.core.application_service.ConjugationApplicationService`)
- normalizes raw backend objects into a stable payload for widgets
- extracts lightweight presentation metadata (predicted/confidence) without
  coupling widgets to backend types
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from mlconjug3.core.application_service import (
    BackendName,
    ConjugationApplicationService,
    ConjugationTable,
)


@dataclass(frozen=True, slots=True)
class ConjugationViewModel:
    """
    Render-ready conjugation payload for the TUI.

    Attributes
    ----------
    verb:
        Infinitive verb form used as the lookup key.
    table:
        Nested mood/tense/person structure suitable for rendering.
    predicted:
        True when the backend indicates an ML-predicted result.
    confidence_score:
        Optional confidence score provided by the ML backend.
    """

    verb: str
    table: Mapping[str, Any]
    predicted: bool
    confidence_score: Optional[float]
    verb_root: Optional[str]
    verb_template: Optional[str]


class TUIConjugationFacade:
    """
    UI-facing wrapper around `ConjugationApplicationService`.

    This facade provides single-verb and batch conjugation helpers that
    return stable, typed payloads for Textual widgets.
    """

    def __init__(
        self,
        *,
        language: str = "fr",
        subject: str = "abbrev",
        backend: BackendName = "legacy",
    ) -> None:
        """
        Initialize the facade.

        Parameters
        ----------
        language:
            Language code used by the conjugation pipeline.
        subject:
            Subject display mode ("abbrev" or "pronoun").
        backend:
            Backend identifier ("legacy" or "unimorph").
        """

        self._app = ConjugationApplicationService(
            language=language, subject=subject, backend=backend
        )

    @property
    def language(self) -> str:
        """
        Current language code.

        Returns
        -------
        str
            Active language.
        """

        return self._app.language

    def set_language(self, language: str) -> None:
        """
        Update language.

        Parameters
        ----------
        language:
            New language code.
        """

        self._app.set_language(language)

    def set_subject(self, subject: str) -> None:
        """
        Update subject output mode.

        Parameters
        ----------
        subject:
            New subject mode.
        """

        self._app.set_subject(subject)

    def is_valid_verb(self, verb: str) -> bool:
        """
        Validate verb input for the active language/backend.

        Parameters
        ----------
        verb:
            Verb to validate.

        Returns
        -------
        bool
            True if accepted, False otherwise.
        """

        return self._app.is_valid_verb(verb)

    def list_verbs(self) -> list[str]:
        """
        List all known verbs for the current language/backend.

        Returns
        -------
        list[str]
            Verb list.
        """

        return self._app.list_verbs()

    def conjugate_one(self, verb: str) -> Optional[ConjugationViewModel]:
        """
        Conjugate a single verb and return a view model.

        Parameters
        ----------
        verb:
            Verb to conjugate.

        Returns
        -------
        ConjugationViewModel | None
            View model when conjugation succeeded, otherwise None.
        """

        normalized = self._app.conjugate_normalized(verb)
        table = normalized.conjugations.get(verb)
        raw = normalized.raw.get(verb)
        if table is None or raw is None:
            return None

        predicted = bool(getattr(raw, "predicted", False))
        confidence = getattr(raw, "confidence_score", None)
        confidence_score = confidence if isinstance(confidence, float) else None
        verb_info = getattr(raw, "verb_info", None)
        root = getattr(verb_info, "root", None)
        template = getattr(verb_info, "template", None)
        verb_root = root if isinstance(root, str) else None
        verb_template = template if isinstance(template, str) else None

        return ConjugationViewModel(
            verb=verb,
            table=table,
            predicted=predicted,
            confidence_score=confidence_score,
            verb_root=verb_root,
            verb_template=verb_template,
        )

    def conjugate_many(self, verbs: list[str]) -> list[ConjugationViewModel]:
        """
        Conjugate multiple verbs and return one view model per successful verb.

        Parameters
        ----------
        verbs:
            Input verbs to conjugate.

        Returns
        -------
        list[ConjugationViewModel]
            View models for successfully conjugated verbs, preserving the input
            order for verbs that succeed.
        """

        normalized = self._app.conjugate_normalized(verbs)
        out: list[ConjugationViewModel] = []

        for verb in verbs:
            table: Optional[ConjugationTable] = normalized.conjugations.get(verb)
            raw = normalized.raw.get(verb)
            if table is None or raw is None:
                continue

            predicted = bool(getattr(raw, "predicted", False))
            confidence = getattr(raw, "confidence_score", None)
            confidence_score = confidence if isinstance(confidence, float) else None
            verb_info = getattr(raw, "verb_info", None)
            root = getattr(verb_info, "root", None)
            template = getattr(verb_info, "template", None)
            verb_root = root if isinstance(root, str) else None
            verb_template = template if isinstance(template, str) else None

            out.append(
                ConjugationViewModel(
                    verb=verb,
                    table=table,
                    predicted=predicted,
                    confidence_score=confidence_score,
                    verb_root=verb_root,
                    verb_template=verb_template,
                )
            )

        return out

