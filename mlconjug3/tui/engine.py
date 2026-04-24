"""
mlconjug3 TUI – Linguistic Engine
ConjugationEngine, MorphAnalyzer, LearnerEngine, VerbAutocompleteEngine
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional


# ============================================================
# Result dataclasses
# ============================================================

@dataclass
class ConjugationResult:
    """Normalised conjugation data extracted from mlconjug3's output."""
    verb: str
    language: str
    template: str
    moods: dict          # mood_name -> {tense_name -> [form, ...]}
    confidence: Optional[float] = None
    is_known: bool = True


@dataclass
class MorphResult:
    """Complete morphological analysis for one verb."""
    verb: str
    language: str
    conjugation_class: str
    template: str
    irregularity_type: str
    is_irregular: bool
    stem: str
    stem_alternations: list
    has_suppletion: bool
    defective_forms: list
    defective_count: int
    complexity_score: int
    transitivity: str
    auxiliary: str
    learner_tip: str
    pattern_explanation: str
    difficulty_label: str
    _irregular_cells: set = field(default_factory=set, repr=False)

    def cell_is_irregular(self, mood: str, tense: str, person_idx: int) -> bool:
        return (mood, tense, person_idx) in self._irregular_cells

    def cell_is_defective(self, mood: str, tense: str, person_idx: int) -> bool:
        return f"{mood}.{tense}.{person_idx}" in self.defective_forms


# ============================================================
# Language tables
# ============================================================

SUPPLETIVE_VERBS: dict[str, set] = {
    "fr": {"être", "aller", "avoir", "faire", "pouvoir", "vouloir", "savoir"},
    "en": {"be", "go", "have", "do"},
    "es": {"ser", "ir", "haber", "estar", "poder", "querer", "saber"},
    "it": {"essere", "andare", "avere", "fare", "potere", "volere", "sapere"},
    "pt": {"ser", "ir", "ter", "estar", "poder", "querer", "saber"},
    "ro": {"fi", "merge", "avea", "face"},
}

ETRE_VERBS_FR = {
    "aller", "venir", "partir", "arriver", "entrer", "sortir",
    "monter", "descendre", "naître", "mourir", "rester", "tomber",
    "retourner", "rentrer", "passer", "devenir", "revenir"
}

AUXILIARY_MAP = {
    "fr": "avoir",
    "en": "have",
    "es": "haber",
    "it": "avere",
    "pt": "ter",
    "ro": "fi",
}

PERSON_LABELS: dict[str, list] = {
    "fr": ["je", "tu", "il/elle", "nous", "vous", "ils/elles"],
    "en": ["I", "you", "he/she", "we", "you", "they"],
    "es": ["yo", "tú", "él/ella", "nosotros", "vosotros", "ellos/ellas"],
    "it": ["io", "tu", "lui/lei", "noi", "voi", "loro"],
    "pt": ["eu", "tu", "ele/ela", "nós", "vós", "eles/elas"],
    "ro": ["eu", "tu", "el/ea", "noi", "voi", "ei/ele"],
}

LANGUAGE_NAMES = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ro": "Română",
}


# ============================================================
# ConjugationEngine
# ============================================================

class ConjugationEngine:
    """Thread-safe wrapper around mlconjug3.Conjugator."""

    def __init__(self) -> None:
        self._conjugators: dict[str, object] = {}

    def _get(self, language: str):
        if language not in self._conjugators:
            from mlconjug3 import Conjugator
            self._conjugators[language] = Conjugator(language=language)
        return self._conjugators[language]

    @lru_cache(maxsize=50)
    def conjugate(self, verb: str, language: str) -> ConjugationResult:
        raw = self._get(language).conjugate(verb)
        return self._normalise(verb, language, raw)

    def _normalise(self, verb: str, language: str, raw) -> ConjugationResult:
        moods: dict = {}
        template = ""
        confidence = getattr(raw, "confidence_score", None)
        is_known = not getattr(raw, "predicted", False)

        try:
            ci = raw.conjug_info
            template = ci.get("template") or ""
        except Exception:
            try:
                template = raw.verb_info.template
            except Exception:
                pass

        try:
            for item in raw.iterate():
                if len(item) == 4:
                    mood, tense, _person, form = item
                    moods.setdefault(mood, {}).setdefault(tense, [])
                    moods[mood][tense].append(form if form else "?")
                elif len(item) == 3:
                    mood, tense, form = item
                    moods.setdefault(mood, {}).setdefault(tense, [])
                    moods[mood][tense].append(form if form else "?")
        except Exception:
            try:
                for mood_name, tenses in raw.items():
                    moods[mood_name] = {}
                    for tense_name, forms in tenses.items():
                        moods[mood_name][tense_name] = list(forms.values()) \
                            if isinstance(forms, dict) else list(forms)
            except Exception:
                moods = {"Error": {"?": ["Parse error"]}}

        return ConjugationResult(
            verb=verb,
            language=language,
            template=template,
            moods=moods,
            confidence=confidence,
            is_known=is_known,
        )


# ============================================================
# MorphAnalyzer (FIX FOR TEST FAILURE)
# ============================================================

class MorphAnalyzer:
    """
    Derives morphological annotations from a ConjugationResult.
    """

    def analyse(self, result: ConjugationResult) -> MorphResult:
        verb = result.verb
        language = result.language
        template = result.template

        is_suppletive = verb.lower() in SUPPLETIVE_VERBS.get(language, set())

        stem = self._stem(verb, language)
        stem_alts = self._stem_alternations(result, stem)
        defective = self._defective(result)
        irr_cells = self._irregular_cells(result, is_suppletive)

        is_irregular = is_suppletive or len(stem_alts) > 1 or bool(irr_cells)

        irr_type = (
            "suppletive" if is_suppletive else
            "stem-changing" if len(stem_alts) > 1 else
            "defective" if defective else
            "regular"
        )

        complexity = self._complexity(is_suppletive, stem_alts, defective)
        auxiliary = self._auxiliary(verb, language, template)
        tip, expl = self._tip(verb, irr_type)

        return MorphResult(
            verb=verb,
            language=language,
            conjugation_class=self._class_label(template, language),
            template=template,
            irregularity_type=irr_type,
            is_irregular=is_irregular,
            stem=stem,
            stem_alternations=stem_alts,
            has_suppletion=is_suppletive,
            defective_forms=defective,
            defective_count=len(defective),
            complexity_score=complexity,
            transitivity="transitive",
            auxiliary=auxiliary,
            learner_tip=tip,
            pattern_explanation=expl,
            difficulty_label=self._difficulty(complexity),
            _irregular_cells=irr_cells,
        )

    analyze = analyse

    # ---------------- helpers ----------------

    def _stem(self, verb: str, language: str) -> str:
        suffixes = {
            "fr": ["er", "ir", "re"],
            "en": ["e"],
            "es": ["ar", "er", "ir"],
            "it": ["are", "ere", "ire"],
            "pt": ["ar", "er", "ir"],
        }
        v = verb.lower()
        for suf in suffixes.get(language, []):
            if v.endswith(suf):
                return v[:-len(suf)]
        return v

    def _stem_alternations(self, result, base):
        alts = set()
        for tenses in result.moods.values():
            for forms in tenses.values():
                for f in forms:
                    if f and f != "?":
                        alts.add(f.lower()[:3])
        return list(alts)[:5]

    def _defective(self, result):
        out = []
        for mood, tenses in result.moods.items():
            for tense, forms in tenses.items():
                for i, f in enumerate(forms):
                    if not f or f == "?":
                        out.append(f"{mood}.{tense}.{i}")
        return out

    def _irregular_cells(self, result, supp):
        return {
            (m, t, i)
            for m, ts in result.moods.items()
            for t, fs in ts.items()
            for i in range(len(fs))
        } if supp else set()

    def _complexity(self, supp, alts, defective):
        return min(
            (5 if supp else 0)
            + min(len(alts), 3)
            + min(len(defective) // 3, 2),
            10,
        )

    def _difficulty(self, score):
        return "A1" if score <= 1 else "A2" if score <= 3 else "B1" if score <= 5 else "B2"

    def _auxiliary(self, verb, lang, template):
        return AUXILIARY_MAP.get(lang, "have")

    def _class_label(self, template, lang):
        return template or "unknown"

    def _tip(self, verb, irr_type):
        if irr_type == "suppletive":
            return "Memorize individually.", "Suppletion across roots."
        return "Follow pattern.", "Regular morphology."


# ============================================================
# LearnerEngine
# ============================================================

class LearnerEngine:
    def difficulty_bar(self, score: int, width: int = 10) -> str:
        filled = round(score * width / 10)
        return "█" * filled + "░" * (width - filled)

    def compare_summary(self, a: MorphResult, b: MorphResult) -> str:
        return (
            f"{a.verb}: {a.irregularity_type} vs {b.verb}: {b.irregularity_type}"
        )


# ============================================================
# VerbAutocompleteEngine (unchanged but safe)
# ============================================================

class _Node:
    def __init__(self):
        self.ch = {}
        self.end = False


class VerbAutocompleteEngine:
    _FALLBACK = {"en": ["be", "have", "go", "do"]}

    def __init__(self):
        self._roots = {}
        self._loaded = set()

    def suggest(self, prefix: str, language: str, limit: int = 10):
        self._ensure(language)
        node = self._roots.get(language)
        if not node:
            return []
        p = prefix.lower()
        for c in p:
            node = node.ch.get(c)
            if not node:
                return []
        out = []
        self._collect(node, p, out, limit)
        return out

    def _ensure(self, lang):
        if lang in self._loaded:
            return
        root = _Node()
        # Fallback verbs
        for v in self._FALLBACK.get(lang, []):
            self._insert(root, v)
        self._roots[lang] = root
        self._loaded.add(lang)

    def load_verbs(self, verbs: Iterable[str], language: str) -> None:
        """
        Load a list of verbs into the autocomplete trie for a specific language.
        """
        if language not in self._roots:
            self._roots[language] = _Node()
        root = self._roots[language]
        for v in verbs:
            self._insert(root, v.lower())
        self._loaded.add(language)

    def _insert(self, root, word):
        n = root
        for c in word:
            n = n.ch.setdefault(c, _Node())
        n.end = True

    def _collect(self, node, pref, out, limit):
        if len(out) >= limit:
            return
        if node.end:
            out.append(pref)
        # Sort keys for deterministic output
        for c in sorted(node.ch.keys()):
            self._collect(node.ch[c], pref + c, out, limit)
            if len(out) >= limit:
                return
