"""
This module defines the VerbInfo and Verb hierarchy classes used for representing verb conjugation data.

It provides:
- VerbInfo: a lightweight container for verb metadata (infinitive, root, template)
- VerbMeta: an abstract metaclass defining the verb interface
- Verb: the base implementation of a conjugated verb
- Language-specific subclasses: VerbFr, VerbEn, VerbEs, VerbIt, VerbPt, VerbRo

Each language class customizes how conjugation forms are constructed.
"""

import abc
from collections import OrderedDict
from mlconjug3.constants import *


class VerbInfo:
    """
    Container for verb metadata used in conjugation.
    """

    __slots__ = ("infinitive", "root", "template")

    def __init__(self, infinitive, root, template):
        self.infinitive = infinitive
        if not root:
            self.root = "" if template[0] == ":" else template[: template.index(":")]
        else:
            self.root = root
        self.template = template

    def __repr__(self):
        return "{}.{}({}, {}, {})".format(
            __name__, self.__class__.__name__, self.infinitive, self.root, self.template
        )

    def __eq__(self, other):
        if not isinstance(other, VerbInfo):
            return NotImplemented
        return (
            self.infinitive == other.infinitive
            and self.root == other.root
            and self.template == other.template
        )


class VerbMeta(abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, verb_info, conjug_info, subject="abbrev", predicted=False):
        pass

    @abc.abstractproperty
    def language(self):
        pass

    @abc.abstractmethod
    def __getitem__(self, key):
        pass

    @abc.abstractmethod
    def __setitem__(self, key, value):
        pass

    @abc.abstractmethod
    def __contains__(self, item):
        pass

    @abc.abstractmethod
    def __iter__(self):
        pass

    @abc.abstractmethod
    def iterate(self):
        pass

    @abc.abstractmethod
    def load_conjug(self):
        pass

    @abc.abstractmethod
    def conjugate(self, subject, tense):
        pass


class Verb(metaclass=VerbMeta):
    """
    Base class representing a conjugated verb.
    """

    __slots__ = (
        "name",
        "verb_info",
        "conjug_info",
        "full_forms",
        "subject",
        "predicted",
        "confidence_score",
    )

    language = "default"

    def __init__(self, verb_info, conjug_info, subject="abbrev", predicted=False):
        self.name = verb_info.infinitive
        self.verb_info = verb_info
        self.conjug_info = conjug_info
        self.full_forms = {}
        self.subject = subject
        self.predicted = predicted
        self.confidence_score = None

        if subject == "pronoun":
            self._load_conjug(subject)
            self.full_forms = self.conjug_info
        else:
            self._load_conjug("pronoun")
            self.full_forms = self.conjug_info
            self._load_conjug(subject)

    def __repr__(self):
        return "{}.{}({})".format(__name__, self.__class__.__name__, self.name)

    def __getitem__(self, key):
        if len(key) == 3:
            mood, tense, person = key
            return self.conjug_info[mood][tense][person]
        elif len(key) == 2:
            mood, tense = key
            return self.conjug_info[mood][tense]
        else:
            return self.conjug_info[key]

    def __setitem__(self, key, value):
        if len(key) == 3:
            mood, tense, person = key
            self.conjug_info[mood][tense][person] = value
        elif len(key) == 2:
            mood, tense = key
            self.conjug_info[mood][tense] = value
        else:
            self.conjug_info[key] = value

    def __contains__(self, item):
        try:
            for mood, tenses in self.full_forms.items():
                for tense, persons in tenses.items():

                    if persons is None:
                        continue

                    if isinstance(persons, str):
                        if " ".join((tense, persons)) == item or persons == item:
                            return True
                    else:
                        for pers, form_ in persons.items():
                            if " ".join((pers, form_)) == item or form_ == item:
                                return True
            return False
        except Exception:
            return False

    def __iter__(self):
        """
        Safe iteration over conjugation forms.
        """
        for mood, tenses in self.conjug_info.items():
            for tense, persons in tenses.items():

                if persons is None:
                    continue

                if isinstance(persons, str):
                    yield mood, tense, persons

                elif isinstance(persons, dict):
                    for pers, form in persons.items():
                        yield mood, tense, pers, form

    def __len__(self):
        """
        SAFE LENGTH CALCULATION (FIXED)

        Handles:
        - None values (bug source)
        - dict-based conjugations
        - string forms
        - unexpected structures
        """
        count = 0

        for mood, tenses in self.conjug_info.items():
            for tense, persons in tenses.items():

                if persons is None:
                    continue

                if isinstance(persons, str):
                    count += 1

                elif isinstance(persons, dict):
                    count += len(persons)

                elif isinstance(persons, list):
                    count += len(persons)

                else:
                    # unknown structure → ignore safely
                    continue

        return count

    def iterate(self):
        return [item for item in self]

    def _load_conjug(self, subject="abbrev"):
        for mood, tense in self.conjug_info.items():
            for tense_name, persons in tense.items():

                if persons is None:
                    continue

                if isinstance(persons, list):
                    persons_dict = OrderedDict()
                    for pers, term in persons:
                        key = ABBREVS[pers] if len(persons) == 6 else ""
                        if term is not None:
                            self.conjugate_person(key, persons_dict, term)
                        else:
                            persons_dict[key] = None
                    self.conjug_info[mood][tense_name] = persons_dict

                elif isinstance(persons, str):
                    self.conjug_info[mood][tense_name] = self.verb_info.root + persons

    def conjugate_person(self, key, persons_dict, term):
        persons_dict[key] = self.verb_info.root + term


class VerbFr(Verb):
    __slots__ = ()
    language = "fr"


class VerbEn(Verb):
    __slots__ = ()
    language = "en"


class VerbEs(Verb):
    __slots__ = ()
    language = "es"


class VerbIt(Verb):
    __slots__ = ()
    language = "it"


class VerbPt(Verb):
    __slots__ = ()
    language = "pt"


class VerbRo(Verb):
    __slots__ = ()
    language = "ro"


if __name__ == "__main__":
    pass
