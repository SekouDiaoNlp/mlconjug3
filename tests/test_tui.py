from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from mlconjug3.tui.engine import ConjugationEngine, ConjugationResult, MorphAnalyzer, LearnerEngine, VerbAutocompleteEngine
from mlconjug3.tui.state import AppState, UIPreferences, SessionStore
from mlconjug3.tui.a11y import A11yManager, PALETTES


# =====================================================================
# ConjugationEngine
# =====================================================================

def test_conjugation_engine_returns_result():
    eng = ConjugationEngine()
    r = eng.conjugate("parler", "fr")

    assert isinstance(r, ConjugationResult)
    assert r.verb == "parler"
    assert r.language == "fr"
    assert r.is_known is True


def test_moods_populated():
    eng = ConjugationEngine()
    r = eng.conjugate("parler", "fr")

    assert "Indicatif" in r.moods
    assert "Présent" in r.moods["Indicatif"]


def test_forms_list():
    eng = ConjugationEngine()
    r = eng.conjugate("parler", "fr")

    # In mlconjug3, some forms might have pronouns or not depending on config
    # We just check if the list has the expected length or contains the base form
    forms = r.moods["Indicatif"]["Présent"]
    assert len(forms) >= 6
    assert any("parle" in f for f in forms)


def test_lru_cache():
    eng = ConjugationEngine()
    assert eng.conjugate("parler", "fr") is eng.conjugate("parler", "fr")


# =====================================================================
# MorphAnalyzer
# =====================================================================

@pytest.fixture
def morph():
    eng = ConjugationEngine()
    ma = MorphAnalyzer()
    return lambda v="parler", l="fr": ma.analyse(eng.conjugate(v, l))


def test_regular_type(morph):
    m = morph()
    assert m.irregularity_type == "regular"
    assert m.is_irregular is False


def test_regular_stem(morph):
    assert morph().stem == "parl"


def test_regular_auxiliary(morph):
    assert morph().auxiliary == "avoir"


def test_suppletive_etre(morph):
    m = morph("être")

    assert m.has_suppletion
    assert m.is_irregular
    assert m.irregularity_type == "suppletive"
    assert m.complexity_score >= 5


def test_suppletive_cells(morph):
    m = morph("être")
    # être is suppletive, so all its cells should be marked as irregular by my engine logic
    assert m.cell_is_irregular("Indicatif", "Présent", 0)


# =====================================================================
# LearnerEngine
# =====================================================================

def test_difficulty_bar():
    le = LearnerEngine()
    bar = le.difficulty_bar(5, width=10)
    assert "█" in bar
    assert "░" in bar
    assert len(bar) == 10


def test_compare_summary():
    eng = ConjugationEngine()
    ma = MorphAnalyzer()
    le = LearnerEngine()

    a = ma.analyse(eng.conjugate("parler", "fr"))
    b = ma.analyse(eng.conjugate("être", "fr"))

    summary = le.compare_summary(a, b)
    assert "parler" in summary
    assert "être" in summary


# =====================================================================
# VerbAutocompleteEngine
# =====================================================================

def test_autocomplete_basic():
    ac = VerbAutocompleteEngine()
    # Populate with some verbs
    ac.load_verbs(["parler", "partir", "manger"], "fr")

    suggestions = ac.suggest("par", "fr")
    assert "parler" in suggestions
    assert "partir" in suggestions
    assert "manger" not in suggestions


def test_autocomplete_limit():
    ac = VerbAutocompleteEngine()
    ac.load_verbs(["parler", "partir", "paraitre"], "fr")

    assert len(ac.suggest("par", "fr", limit=2)) == 2


def test_autocomplete_no_match():
    ac = VerbAutocompleteEngine()
    ac.load_verbs(["parler"], "fr")

    assert ac.suggest("zzz", "fr") == []


# =====================================================================
# UIPreferences
# =====================================================================

def test_ui_defaults():
    p = UIPreferences()

    assert p.theme == "dark"
    assert p.default_language == "fr"
    assert p.reduced_motion is False


def test_ui_save_load(tmp_path):
    with patch("mlconjug3.tui.state.PREFS_FILE", tmp_path / "prefs.json"):
        with patch("mlconjug3.tui.state.CONFIG_DIR", tmp_path):
            p = UIPreferences(theme="light", reduced_motion=True, default_language="es")
            p.save()

            p2 = UIPreferences.load()
            assert p2.theme == "light"
            assert p2.reduced_motion is True
            assert p2.default_language == "es"


# =====================================================================
# SessionStore
# =====================================================================

def test_session_history(tmp_path):
    with patch("mlconjug3.tui.state.SESSION_FILE", tmp_path / "session.json"):
        with patch("mlconjug3.tui.state.CONFIG_DIR", tmp_path):
            s = SessionStore()
            s.add_history("parler", "fr")

            assert s.history[0]["verb"] == "parler"
            assert s.history[0]["language"] == "fr"


def test_session_bookmark(tmp_path):
    with patch("mlconjug3.tui.state.SESSION_FILE", tmp_path / "session.json"):
        with patch("mlconjug3.tui.state.CONFIG_DIR", tmp_path):
            s = SessionStore()
            assert s.toggle_bookmark("être", "fr") is True
            assert s.is_bookmarked("être", "fr") is True
            assert s.toggle_bookmark("être", "fr") is False
            assert s.is_bookmarked("être", "fr") is False


# =====================================================================
# A11yManager
# =====================================================================

def test_a11y_palettes_exist():
    for name in ["dark", "light", "high_contrast", "deuteranopia", "protanopia"]:
        assert name in PALETTES


def test_a11y_palette_switching():
    p1 = UIPreferences(theme="dark")
    a1 = A11yManager(p1)
    assert a1.palette.name == "dark"

    p2 = UIPreferences(theme="light")
    a2 = A11yManager(p2)
    assert a2.palette.name == "light"


def test_a11y_colorblind_override():
    p = UIPreferences(colorblind_mode="deuteranopia")
    a = A11yManager(p)
    assert a.palette.name == "deuteranopia"
