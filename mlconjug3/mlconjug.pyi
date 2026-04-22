# Stubs for mlconjug3.mlconjug (Python 3)

from .constants import *
from .verbs import Verb
from .conjug_manager import ConjugManager
from .models import Model
from .feature_extractor import extract_verb_features
from sklearn.pipeline import Pipeline

# I am commenting out the sklearn imports because they have yet no stub files.
# from sklearn.feature_extraction.text import CountVectorizer
# from sklearn.base import BaseEstimator
from typing import (
    Optional,
    Mapping,
    List,
    Sequence,
    DefaultDict,
    Any,
    Tuple,
    Type,
    AbstractSet,
    Union,
    Literal,
)

class Conjugator:
    language: str = ...
    conjug_manager: ConjugManager = ...
    backend: str = ...
    model: Model = ...
    def __init__(
        self,
        language: str = ...,
        model: Optional[Model] = ...,
        backend: Literal["legacy", "unimorph"] = ...,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def conjugate(
        self, verb: Union[str, List[str]], subject: str = ...
    ) -> Union[Optional[Verb], List[Optional[Verb]]]: ...
    def _conjugate(self, verb: str, subject: str = ...) -> Optional[Verb]: ...
    def set_model(self, model: Model) -> None: ...
