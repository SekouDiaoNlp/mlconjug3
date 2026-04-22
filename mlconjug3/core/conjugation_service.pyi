from typing import Literal
from mlconjug3.mlconjug import Conjugator
from mlconjug3.core.application_service import ConjugationResult
from mlconjug3.verbs import Verb

BackendName = Literal["legacy", "unimorph"]
VerbResult = Verb | None

class ConjugationService:
    """
    Typed interface for ConjugationService.
    """

    language: str
    subject: str
    backend: BackendName
    conjugator: Conjugator

    def __init__(
        self,
        language: str = "fr",
        subject: str = "abbrev",
        backend: BackendName = "legacy",
    ) -> None: ...

    def set_language(self, language: str) -> None: ...

    def set_subject(self, subject: str) -> None: ...

    def set_backend(self, backend: BackendName) -> None: ...

    def conjugate(self, verbs: str | list[str]) -> VerbResult | list[VerbResult]: ...

    def conjugate_normalized(self, verbs: str | list[str]) -> ConjugationResult: ...

    def is_valid_verb(self, verb: str) -> bool: ...

    def list_verbs(self) -> list[str]: ...
