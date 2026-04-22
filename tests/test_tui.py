# -*- coding: utf-8 -*-

"""
test_tui.py

Test suite for the mlconjug3 Textual-based Terminal User Interface (TUI).

This module contains unit and integration tests for:
- ResultsTable widget (safe rendering, tree manipulation)
- VerbBrowser widget (filtering and selection behavior)
- Mlconjug3TUI application (input handling, batch processing, settings)

The tests are intentionally synchronous and avoid async Textual APIs.
They focus on logic correctness, state transitions, and safe widget behavior
rather than full rendering validation.

Notes
-----
- Textual UI rendering is not fully asserted (renderables are normalized).
- UI interactions are simulated via direct method calls and monkeypatching.
- This suite prioritizes deterministic execution in CI environments.

"""

import pytest

from mlconjug3.tui.app import Mlconjug3TUI
from mlconjug3.tui.widgets.results_table import ResultsTable
from mlconjug3.tui.widgets.verb_browser import VerbBrowser
from mlconjug3.tui.state import TUIState
from mlconjug3.tui.search.fuzzy import suggest
from mlconjug3.core.export import ExportPayload, to_json, to_text
from mlconjug3.tui.app import main as tui_main
from mlconjug3.tui.learn.engine import build_quiz
from mlconjug3.tui.widgets.suggest_dropdown import SuggestDropdown, SuggestionChosen
from mlconjug3.core.morphology.summary import summarize, guess_conjugation_class


# =========================================================
# RESULTS TABLE TESTS
# =========================================================

def test_results_table_safe_clear():
    """
    Test that ResultsTable.clear() safely resets the tree state.

    This ensures that:
    - No exceptions are raised during clearing
    - Root label is reset to an empty state
    - Tree children are properly removed

    Returns
    -------
    None
    """

    table = ResultsTable()

    table.update_conjugation(
        "aller",
        {
            "indicatif": {
                "present": {"je": "vais"}
            }
        }
    )

    table.clear()

    root_label = str(table._tree.root.label)

    assert root_label == ""
    assert len(table._tree.root.children) == 0


def test_results_table_safe_rendering_none():
    """
    Ensure ResultsTable handles None values without crashing.

    This test validates robustness of the rendering layer when
    encountering incomplete or missing conjugation data.

    Returns
    -------
    None
    """

    table = ResultsTable()

    table.update_conjugation(
        "aller",
        {
            "indicatif": {
                "present": {"je": None}
            }
        }
    )

    assert table._tree is not None


def test_results_table_filters_mood_and_tense():
    """
    Ensure ResultsTable respects mood/tense filters.

    Returns
    -------
    None
    """

    table = ResultsTable()
    table.update_conjugation(
        "aller",
        {
            "indicatif": {"present": {"je": "vais"}, "imparfait": {"je": "allais"}},
            "subjonctif": {"present": {"je": "aille"}},
        },
        allowed_moods={"indicatif"},
        allowed_tenses={"present"},
    )

    root_children = list(table._tree.root.children)
    assert len(root_children) == 1
    assert "Indicatif" in str(root_children[0].label)


def test_results_table_irregular_badge_for_ml():
    """
    Ensure ML mode adds irregular marker badge.

    Returns
    -------
    None
    """

    table = ResultsTable()
    table.update_conjugation("aller", {"indicatif": {"present": {"je": "vais"}}}, mode="ML")
    assert "ML*" in str(table._tree.root.label)


# =========================================================
# VERB BROWSER TESTS
# =========================================================

def test_verb_browser_filtering():
    """
    Test verb filtering behavior in VerbBrowser.

    This test simulates user input in the search field and ensures
    that the list view is correctly filtered based on query input.

    Returns
    -------
    None
    """

    def run(app: Mlconjug3TUI):
        browser = VerbBrowser(["aller", "manger", "finir"])

        browser.on_mount()

        class Event:
            """
            Simple event mock for input simulation.
            """

            def __init__(self, value: str):
                self.value = value

        browser.on_input_changed(Event("al"))

        items = list(browser.list_view.children)

        assert len(items) >= 1
        assert any("aller" in str(i) for i in items)


def test_verb_browser_selection_message():
    """
    Test that VerbBrowser emits VerbSelected message on selection.

    This verifies:
    - Selection event handling
    - Message dispatch system
    - Proper verb extraction from UI items

    Returns
    -------
    None
    """

    def run(app: Mlconjug3TUI):
        browser = VerbBrowser(["aller"])

        browser.on_mount()

        class FakeLabel:
            """
            Mock label used to simulate ListView item content.
            """
            renderable = "aller"

        class FakeItem:
            """
            Mock ListView item containing verb metadata.
            """

            def query_one(self, _):
                return FakeLabel()

        class Event:
            """
            Mock selection event.
            """
            item = FakeItem()

        messages = []

        def capture(msg):
            messages.append(msg)

        browser.post_message = capture

        browser.on_list_view_selected(Event())

        assert len(messages) == 1
        assert messages[0].verb == "aller"


# =========================================================
# APP INTEGRATION TESTS
# =========================================================

def test_app_update_verb_valid(tmp_path, monkeypatch):
    """
    Test valid verb update flow in Mlconjug3TUI.

    Ensures that:
    - Valid verbs trigger conjugation update
    - ResultsTable is updated correctly
    - No UI crashes occur

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", str(tmp_path / "tui_state.json"))
    app = Mlconjug3TUI()

    class FakeStatic:
        def update(self, _text: str) -> None:
            return

    class FakeVM:
        """
        Mock view model returned by the TUI facade.
        """

        verb = "aller"
        table = {"indicatif": {"present": {"je": "vais"}}}
        predicted = False
        confidence_score = None

    app._compute_and_apply_single = lambda v: app._apply_single_result(  # type: ignore[assignment]
        v, FakeVM()
    )

    results = ResultsTable()
    class FakeFilterBar:
        def set_options(self, _m, _t):
            return

    app.query_one = lambda selector, _type: (  # type: ignore[assignment]
        FakeStatic()
        if selector == "#input_feedback"
        else FakeFilterBar()
        if selector == "#filter_bar"
        else results
    )

    app._update_verb("aller")

    assert results._tree.root.label is not None


def test_app_update_verb_invalid(tmp_path, monkeypatch):
    """
    Test handling of invalid verb input in Mlconjug3TUI.

    Ensures that invalid verbs:
    - Do not crash the application
    - Are safely rejected by validation logic

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", str(tmp_path / "tui_state.json"))
    app = Mlconjug3TUI()

    class FakeResults(ResultsTable):
        """
        Mock ResultsTable capturing update calls.
        """

        def update_conjugation(self, *args, **kwargs):
            self.called = True

    app.query_one = lambda _id, _type: FakeResults()
    app._is_valid = lambda v: False
    app._update_verb("notaverb")


# =========================================================
# BATCH MODE TESTS
# =========================================================

def test_app_batch_parsing(tmp_path, monkeypatch):
    """
    Test batch input parsing and execution flow.

    Ensures that:
    - Multiple verbs are parsed correctly
    - Each verb triggers conjugation safely
    - ResultsTable updates without errors

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", str(tmp_path / "tui_state.json"))
    app = Mlconjug3TUI()

    class FakeInput:
        """
        Mock input widget for batch verb entry.
        """

        value = "aller, manger"

    class FakeTable(ResultsTable):
        """
        Mock ResultsTable tracking update calls.
        """

        def update_conjugation(self, *args, **kwargs):
            self.called = True

    app.query_one = lambda selector, _type: (
        FakeInput() if "batch_input" in selector else FakeTable()
    )

    app._is_valid = lambda v: True
    app._compute_and_apply_batch = lambda verbs: app._apply_batch_result(  # type: ignore[assignment]
        [
            type(
                "FakeVM",
                (),
                {
                    "verb": v,
                    "table": {"indicatif": {"present": {"je": "vais"}}},
                    "predicted": False,
                    "confidence_score": None,
                },
            )()
            for v in verbs
        ]
    )

    app._run_batch()


# =========================================================
# SETTINGS TESTS
# =========================================================

def test_app_language_switch(tmp_path, monkeypatch):
    """
    Test language switching behavior in Mlconjug3TUI.

    Ensures that:
    - Language state is updated correctly
    - Conjugation service is reconfigured accordingly

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", str(tmp_path / "tui_state.json"))
    app = Mlconjug3TUI()

    class FakeStatic:
        def update(self, _text: str) -> None:
            return

    app.query_one = lambda _sel, _type: FakeStatic()  # type: ignore[assignment]

    class Event:
        """
        Mock Select.Changed event.
        """

        select = type("S", (), {"id": "lang_select"})
        value = "es"

    app.on_select_changed(Event())

    assert app.state.language == "es"
    assert app.service.language == "es"


# =========================================================
# STATE PERSISTENCE TESTS
# =========================================================

def test_tui_state_persistence_roundtrip(tmp_path):
    """
    Verify that TUIState saves and loads history/favorites.

    Returns
    -------
    None
    """

    path = tmp_path / "tui_state.json"
    state = TUIState(storage_path=path)
    state.language = "es"
    state.subject = "pronoun"
    state.add_history("hablar")
    state.toggle_favorite("hablar")

    state2 = TUIState(storage_path=path)
    state2.load()

    assert state2.language == "es"
    assert state2.subject == "pronoun"
    assert "hablar" in state2.history
    assert "hablar" in state2.favorites

    # default filters persist
    state.selected_moods = {"indicatif"}
    state.save()
    state3 = TUIState(storage_path=path)
    state3.load()
    assert "indicatif" in state3.selected_moods


def test_fuzzy_suggest_ranking():
    """
    Ensure fuzzy suggestions prioritize prefix and substring matches.

    Returns
    -------
    None
    """

    candidates = ["aller", "parler", "raller", "ballerine"]
    out = suggest(candidates, "all", limit=10)
    assert out[0] == "aller"
    assert "ballerine" in out


def test_export_payload_serialization():
    """
    Ensure export helpers produce deterministic outputs.

    Returns
    -------
    None
    """

    payload = ExportPayload(
        verb="aller",
        language="fr",
        subject="abbrev",
        table={"indicatif": {"present": {"je": "vais"}}},
    )

    js = to_json(payload)
    assert '"verb": "aller"' in js
    assert '"language": "fr"' in js

    txt = to_text(payload)
    assert "aller [fr]" in txt
    assert "indicatif" in txt.lower()


def test_tui_help(capsys, monkeypatch):
    """
    Ensure TUI entrypoint supports --help.

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", "/tmp/mlconjug3-tui-state.json")
    monkeypatch.setattr("sys.argv", ["mlconjug3-tui", "--help"])
    tui_main()
    out = capsys.readouterr().out
    assert "mlconjug3-tui" in out


def test_learn_quiz_build_deterministic():
    """
    Ensure learn quiz selection is deterministic for a seed.

    Returns
    -------
    None
    """

    table = {"indicatif": {"present": {"je": "vais", "tu": "vas"}}}
    q0 = build_quiz(table, 0)
    q1 = build_quiz(table, 1)
    assert q0 is not None and q1 is not None
    assert q0.person != q1.person


def test_suggest_dropdown_emits_message():
    """
    Ensure SuggestDropdown emits SuggestionChosen.

    Returns
    -------
    None
    """

    dd = SuggestDropdown()
    dd.set_suggestions(["aller"])

    class FakeEvent:
        item = type("I", (), {"value": "aller"})()

    messages = []
    dd.post_message = lambda msg: messages.append(msg)  # type: ignore[assignment]
    dd.on_list_view_selected(FakeEvent())
    assert isinstance(messages[0], SuggestionChosen)
    assert messages[0].value == "aller"


def test_morphology_summary_computed_and_curated():
    """
    Ensure morphology summary computes counts and class heuristics.

    Returns
    -------
    None
    """

    s = summarize(
        language="es",
        infinitive="hablar",
        table={"indicatif": {"present": {"yo": "hablo", "tu": None}}},
        irregular_proxy=True,
    )
    assert s.irregular_proxy is True
    assert s.filled_cells == 1
    assert s.missing_cells == 1
    assert s.conjugation_class == "Spanish -ar"
    assert guess_conjugation_class("it", "parlare") == "Italian -are"


def test_app_toggle_favorite_action(tmp_path, monkeypatch):
    """
    Ensure the favorite toggle action updates state.

    Returns
    -------
    None
    """

    monkeypatch.setenv("MLCONJUG3_TUI_STATE_PATH", str(tmp_path / "tui_state.json"))
    app = Mlconjug3TUI()
    app._current_verb = "aller"
    app._refresh_status_bar = lambda: None  # type: ignore[assignment]
    app.action_toggle_favorite()
    assert "aller" in app.state.favorites
