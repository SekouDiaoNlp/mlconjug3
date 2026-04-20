"""
Conjugation manager module for mlconjug3.

Now supports:
- Legacy Verbiste backend
- UniMorph JSON backend (toggleable)
"""

__author__ = "Ars-Linguistica"
__author_email__ = "diao.sekou.nlp@gmail.com"

import os
import joblib
import copy
import json
from collections import OrderedDict
from importlib import resources

from mlconjug3.constants import *
from mlconjug3.verbs import *


class ConjugManager:
    """
    Manager for verb and conjugation data.

    Supports:
    - Legacy Verbiste XML/JSON system
    - UniMorph JSON system (optional toggle)
    """

    # ---------------------------
    # LANGUAGE MAPPING (NEW)
    # ---------------------------
    UNIMORPH_LANG_MAP = {
        "fr": "fra",
        "en": "eng",
        "es": "spa",
        "it": "ita",
        "pt": "por",
        "ro": "ron",
        "de": "deu",
        "nl": "nld",
        "sv": "swe",
        "fi": "fin",
        "pl": "pol",
        "el": "ell",
        "bg": "bul",
        "sl": "slv",
        "da": "dan",
        "no": "nob",
        "nn": "nno",
        "lt": "lit",
        "lv": "lav",
        "af": "afr",
        "slk": "slk",
        "hbs": "hbs",
    }

    def __init__(self, language="default", use_unimorph: bool = False):
        """
        Parameters
        ----------
        language : str
            Language code (fr, en, es, etc.)
        use_unimorph : bool
            If True, uses UniMorph JSON dataset instead of legacy Verbiste
        """

        if language not in LANGUAGES:
            raise ValueError(
                "Unsupported language.\nAllowed: fr, en, es, it, pt, ro."
            )

        self.language = "fr" if language == "default" else language
        self.use_unimorph = use_unimorph

        self.verbs = {}
        self.conjugations = OrderedDict()

        # ---------------------------
        # LOAD BACKEND
        # ---------------------------
        if self.use_unimorph:
            self._load_unimorph()
        else:
            self._load_legacy()

        self.templates = sorted(self.conjugations.keys())

    # ---------------------------
    # UNIMORPH LOADER
    # ---------------------------
    def _load_unimorph(self):
        lang3 = self.UNIMORPH_LANG_MAP.get(self.language)

        if not lang3:
            raise ValueError(f"No UniMorph mapping for language: {self.language}")

        base_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "conjugation_data"
        )

        verbs_path = os.path.join(base_path, f"verbs-{lang3}.json")
        conj_path = os.path.join(base_path, f"conjugations-{lang3}.json")

        with open(verbs_path, encoding="utf-8") as f:
            self.verbs = json.load(f)

        with open(conj_path, encoding="utf-8") as f:
            self.conjugations = json.load(f)

    # ---------------------------
    # LEGACY LOADER
    # ---------------------------
    def _load_legacy(self):
        verbs_file = VERBS_RESOURCE_PATH[self.language]
        self._load_verbs(verbs_file)

        self._allowed_endings = self._detect_allowed_endings()

        conjugations_file = CONJUGATIONS_RESOURCE_PATH[self.language]
        self._load_conjugations(conjugations_file)

    # ---------------------------
    # EXISTING LOGIC (UNCHANGED)
    # ---------------------------
    def _is_real_file(self, path):
        try:
            return os.path.isfile(path)
        except Exception:
            return False

    def _open_resource(self, relative_path):
        return resources.files(RESOURCE_PACKAGE).joinpath(relative_path).open(
            "r", encoding="utf-8"
        )

    def _load_cache(self, file):
        if not self._is_real_file(file):
            return None
        if not file.endswith(".json"):
            raise ValueError(f"Expected .json file, got {file}")

        pkl_file = file + ".pkl"

        if os.path.isfile(pkl_file):
            if os.path.getmtime(file) <= os.path.getmtime(pkl_file):
                return joblib.load(pkl_file)

        return None

    def _save_cache(self, file, data):
        if not self._is_real_file(file):
            return
        try:
            joblib.dump(data, file + ".pkl", compress=("gzip", 3))
        except Exception:
            pass

    def _load_verbs(self, verbs_file):
        cache = self._load_cache(verbs_file)
        if cache:
            self.verbs = cache
            return

        if self._is_real_file(verbs_file):
            with open(verbs_file, encoding="utf-8") as f:
                self.verbs = json.load(f)
        else:
            with self._open_resource(verbs_file) as f:
                self.verbs = json.load(f)

        self._save_cache(verbs_file, self.verbs)

    def _load_conjugations(self, conjugations_file):
        cache = self._load_cache(conjugations_file)
        if cache:
            self.conjugations = cache
            return

        if self._is_real_file(conjugations_file):
            with open(conjugations_file, encoding="utf-8") as f:
                self.conjugations = json.load(f)
        else:
            with self._open_resource(conjugations_file) as f:
                self.conjugations = json.load(f)

        self._save_cache(conjugations_file, self.conjugations)

    # ---------------------------
    # LEGACY LOGIC (UNCHANGED)
    # ---------------------------
    def _detect_allowed_endings(self):
        if self.language == "en":
            return set()

        return {
            verb.split(" ")[0][-2:]
            for verb in self.verbs
            if len(verb) >= 2
        }

    def is_valid_verb(self, verb):
        if self.language == "en":
            return True
        return verb[-2:] in self._allowed_endings

    def get_verb_info(self, verb):
        if verb not in self.verbs:
            return None

        data = self.verbs[verb]
        return VerbInfo(verb, data["root"], data["template"])

    def get_conjug_info(self, template):
        if template not in self.conjugations:
            return None
        return copy.deepcopy(self.conjugations[template])


if __name__ == "__main__":
    pass
