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

from typing import Union, List, Any
from mlconjug3.mlconjug import Conjugator


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

    def __init__(self, language: str = "fr", subject: str = "abbrev") -> None:
        """
        Initialize the conjugation service.

        Parameters
        ----------
        language : str, optional
            Language code for conjugation (default is "fr").
        subject : str, optional
            Subject formatting mode (default is "abbrev").
        """

        self.language: str = language
        self.subject: str = subject
        self.conjugator: Conjugator = Conjugator(language)

    def set_language(self, language: str) -> None:
        """
        Update the active language and reset the conjugator.

        Parameters
        ----------
        language : str
            New language code to use.
        """

        self.language = language
        self.conjugator = Conjugator(language)

    def set_subject(self, subject: str) -> None:
        """
        Update subject formatting mode.

        Parameters
        ----------
        subject : str
            Subject mode ("abbrev" or "pronoun").
        """

        self.subject = subject

    def conjugate(self, verbs: Union[str, List[str]]) -> Any:
        """
        Conjugate one or multiple verbs.

        Parameters
        ----------
        verbs : str or list of str
            Verb(s) to conjugate.

        Returns
        -------
        Any
            Conjugation result(s) from the underlying engine.
        """

        return self.conjugator.conjugate(verbs, self.subject)
