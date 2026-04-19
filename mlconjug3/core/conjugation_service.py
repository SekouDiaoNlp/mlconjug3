"""
conjugation_service.py

Core shared service layer for mlconjug3.

This module isolates all conjugation logic so that it can be reused
by both the CLI and the Textual TUI without duplication.

It acts as a thin abstraction over the underlying Conjugator model.
"""

from mlconjug3.mlconjug import Conjugator


class ConjugationService:
    """
    Service responsible for orchestrating verb conjugation.

    Parameters
    ----------
    language : str
        Target language code (e.g., 'fr', 'en', 'es').
    subject : str
        Subject format ('abbrev' or 'pronoun').

    Notes
    -----
    This class is intentionally stateless aside from language configuration.
    It can be safely reused across CLI and TUI sessions.
    """

    def __init__(self, language: str = "fr", subject: str = "abbrev"):
        self.language = language
        self.subject = subject
        self.conjugator = Conjugator(language)

    def set_language(self, language: str) -> None:
        """
        Update language and reinitialize internal model.

        Parameters
        ----------
        language : str
            New language code.
        """
        self.language = language
        self.conjugator = Conjugator(language)

    def conjugate(self, verbs):
        """
        Conjugate one or multiple verbs.

        Parameters
        ----------
        verbs : str | list[str]
            Verb or list of verbs to conjugate.

        Returns
        -------
        list
            Conjugation results from underlying model.
        """
        return self.conjugator.conjugate(verbs, self.subject)
