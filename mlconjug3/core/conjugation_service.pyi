from typing import Union, List, Any
from mlconjug3.mlconjug import Conjugator


class ConjugationService:
    """
    Typed interface for ConjugationService.
    """

    language: str
    subject: str
    conjugator: Conjugator

    def __init__(self, language: str = "fr", subject: str = "abbrev") -> None: ...

    def set_language(self, language: str) -> None: ...

    def set_subject(self, subject: str) -> None: ...

    def conjugate(self, verbs: Union[str, List[str]]) -> Any: ...
