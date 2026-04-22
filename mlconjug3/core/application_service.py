"""
application_service.py

Shared application orchestration used by CLI and TUI.

This module centralizes interface-agnostic conjugation workflows so both
terminal interfaces can reuse the same business logic and output shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, TypeAlias, overload

from mlconjug3.mlconjug import Conjugator
from mlconjug3.verbs import Verb

BackendName = Literal["legacy", "unimorph"]
VerbResult: TypeAlias = Verb | None
ConjugationTable: TypeAlias = Mapping[str, object]
RawConjugationMap: TypeAlias = dict[str, VerbResult]


@dataclass
class ConjugationResult:
    """
    Normalized result object for interface layers.

    Attributes
    ----------
    conjugations : Mapping[str, ConjugationTable]
        Mapping of verb -> conjugation table for successfully conjugated verbs.
    missing : list[str]
        Verbs that could not be conjugated.
    raw : RawConjugationMap
        Raw mapping of verb -> returned verb object (or None when missing).
    """

    conjugations: Mapping[str, ConjugationTable]
    missing: list[str]
    raw: RawConjugationMap


class ConjugationApplicationService:
    """
    Interface-agnostic conjugation orchestrator.

    This service encapsulates language, subject, and backend settings and
    exposes a normalized API that can be consumed by both CLI and TUI layers.
    """

    def __init__(
        self,
        language: str = "fr",
        subject: str = "abbrev",
        backend: BackendName = "legacy",
    ) -> None:
        """
        Initialize the application service.

        Parameters
        ----------
        language : str, optional
            Language code used by the conjugator, by default "fr".
        subject : str, optional
            Subject format ("abbrev" or "pronoun"), by default "abbrev".
        backend : str, optional
            Conjugation backend identifier ("legacy" or "unimorph"),
            by default "legacy".
        """
        self.language = language
        self.subject = subject
        self.backend = backend
        self.conjugator = Conjugator(language=language, backend=backend)

    def set_language(self, language: str) -> None:
        """
        Set the active language and rebuild the conjugator instance.

        Parameters
        ----------
        language : str
            New language code.
        """
        self.language = language
        self.conjugator = Conjugator(language=language, backend=self.backend)

    def set_subject(self, subject: str) -> None:
        """
        Set the active subject output format.

        Parameters
        ----------
        subject : str
            Subject style ("abbrev" or "pronoun").
        """
        self.subject = subject

    def set_backend(self, backend: BackendName) -> None:
        """
        Set the active backend and rebuild the conjugator instance.

        Parameters
        ----------
        backend : str
            Backend identifier ("legacy" or "unimorph").

        Raises
        ------
        ValueError
            If `backend` is unsupported by `Conjugator`.
        """
        self.backend = backend
        self.conjugator = Conjugator(language=self.language, backend=backend)

    def is_valid_verb(self, verb: str) -> bool:
        """
        Validate whether a verb is likely supported by current language rules.

        Parameters
        ----------
        verb : str
            Verb to validate.

        Returns
        -------
        bool
            True when accepted by current manager validation, False otherwise.
        """
        try:
            return self.conjugator.conjug_manager.is_valid_verb(verb)
        except Exception:
            return False

    def list_verbs(self) -> list[str]:
        """
        Return all known verbs in the current backend dictionary.

        Returns
        -------
        list[str]
            Available verb forms.
        """
        return list(self.conjugator.conjug_manager.verbs.keys())

    @overload
    def conjugate(self, verbs: str) -> VerbResult: ...

    @overload
    def conjugate(self, verbs: list[str]) -> list[VerbResult]: ...

    def conjugate(self, verbs: str | list[str]) -> VerbResult | list[VerbResult]:
        """
        Conjugate one or many verbs.

        Parameters
        ----------
        verbs : str or list[str]
            Verb input(s) to conjugate.

        Returns
        -------
        VerbResult or list[VerbResult]
            Raw conjugator output. Single input returns one verb object (or
            None), while list input returns one result per input verb.
        """
        return self.conjugator.conjugate(verbs, self.subject)

    def conjugate_normalized(self, verbs: str | list[str]) -> ConjugationResult:
        """
        Conjugate input verbs and normalize outputs for UI/rendering layers.

        Parameters
        ----------
        verbs : str or list[str]
            Single verb or iterable of verbs.

        Returns
        -------
        ConjugationResult
            Structured result with successful conjugations, missing verbs,
            and raw backend objects.

        Examples
        --------
        >>> service = ConjugationApplicationService(language="fr")
        >>> result = service.conjugate_normalized(["aller", "xxyyzz"])
        >>> isinstance(result.missing, list)
        True
        """
        if isinstance(verbs, str):
            requested_verbs = [verbs]
            raw_result = self.conjugate(verbs)
            raw = {verbs: raw_result}
        else:
            requested_verbs = [verb for verb in verbs]
            raw_results = self.conjugate(requested_verbs)
            raw = dict(zip(requested_verbs, raw_results))

        conjugations = {
            verb: result.conjug_info
            for verb, result in raw.items()
            if result is not None
        }
        missing = [verb for verb, result in raw.items() if result is None]

        return ConjugationResult(
            conjugations=conjugations,
            missing=missing,
            raw=raw,
        )
