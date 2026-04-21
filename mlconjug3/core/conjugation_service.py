"""
conjugation_service.py

Service layer abstraction for verb conjugation.

This module provides a thin wrapper around the mlconjug3 Conjugator
class, exposing a simplified interface for the TUI layer.

It is responsible for:
- Managing language selection
- Maintaining conjugation subject format
- Delegating conjugation requests to the core engine

This separation ensures that the TUI does not directly depend on
low-level conjugation logic or model management.
"""

from mlconjug3.core.application_service import (
    BackendName,
    ConjugationApplicationService,
    ConjugationResult,
    VerbResult,
)


class ConjugationService:
    """
    High-level service layer for verb conjugation.

    This class acts as a bridge between the TUI and the underlying
    mlconjug3 conjugation engine.

    It encapsulates:
    - Language selection
    - Subject formatting mode
    - Conjugation execution

    Attributes
    ----------
    language : str
        Active language code used by the conjugator.
    subject : str
        Subject format mode ("abbrev" or "pronoun").
    conjugator : Conjugator
        Underlying conjugation engine instance.
    """

    def __init__(
        self,
        language: str = "fr",
        subject: str = "abbrev",
        backend: BackendName = "legacy",
    ) -> None:
        """
        Initialize the conjugation service.

        Parameters
        ----------
        language : str, optional
            Language code for conjugation (default is "fr").
        subject : str, optional
            Subject formatting mode (default is "abbrev").
        backend : str, optional
            Backend identifier ("legacy" or "unimorph"), default is "legacy".
        """

        self._app_service = ConjugationApplicationService(
            language=language, subject=subject, backend=backend
        )
        self.language: str = language
        self.subject: str = subject
        self.backend: str = backend
        self.conjugator = self._app_service.conjugator

    def set_language(self, language: str) -> None:
        """
        Update the active language and reset the conjugator.

        Parameters
        ----------
        language : str
            New language code to use.
        """

        self.language = language
        self._app_service.set_language(language)
        self.conjugator = self._app_service.conjugator

    def set_subject(self, subject: str) -> None:
        """
        Update subject formatting mode.

        Parameters
        ----------
        subject : str
            Subject mode ("abbrev" or "pronoun").
        """

        self.subject = subject
        self._app_service.set_subject(subject)

    def set_backend(self, backend: BackendName) -> None:
        """
        Update the active backend and refresh the conjugator.

        Parameters
        ----------
        backend : str
            Backend identifier ("legacy" or "unimorph").

        Raises
        ------
        ValueError
            If `backend` is unsupported by the underlying conjugator.
        """
        self.backend = backend
        self._app_service.set_backend(backend)
        self.conjugator = self._app_service.conjugator

    def conjugate(self, verbs: str | list[str]) -> VerbResult | list[VerbResult]:
        """
        Conjugate one or multiple verbs.

        Parameters
        ----------
        verbs : str or list[str]
            Verb(s) to conjugate.

        Returns
        -------
        VerbResult or list[VerbResult]
            Conjugation result(s) from the underlying engine.
        """

        return self._app_service.conjugate(verbs)

    def conjugate_normalized(self, verbs: str | list[str]) -> ConjugationResult:
        """
        Conjugate input verbs and return normalized results.

        Parameters
        ----------
        verbs : str or list[str]
            Verb(s) to conjugate.

        Returns
        -------
        ConjugationResult
            Normalized conjugation payload for interface layers.
        """
        return self._app_service.conjugate_normalized(verbs)

    def is_valid_verb(self, verb: str) -> bool:
        """
        Validate whether a verb is accepted by the active language/backend.

        Parameters
        ----------
        verb : str
            Verb to validate.

        Returns
        -------
        bool
            True if valid, False otherwise.
        """
        return self._app_service.is_valid_verb(verb)

    def list_verbs(self) -> list[str]:
        """
        List available verbs for the active language/backend.

        Returns
        -------
        list of str
            Known verbs exposed by the current conjugation manager.
        """
        return self._app_service.list_verbs()
