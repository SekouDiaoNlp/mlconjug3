"""
conjugation_service.py
"""

from mlconjug3.mlconjug import Conjugator


class ConjugationService:
    def __init__(self, language: str = "fr", subject: str = "abbrev"):
        self.language = language
        self.subject = subject
        self.conjugator = Conjugator(language)

    def set_language(self, language: str) -> None:
        self.language = language
        self.conjugator = Conjugator(language)

    def conjugate(self, verbs):
        return self.conjugator.conjugate(verbs, self.subject)
