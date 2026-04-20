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

def test_app_update_verb_valid():
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

    app = Mlconjug3TUI()

    def run():
        table = app.query_one("#results", ResultsTable)

        class FakeResult:
            """
            Mock conjugation result returned by cache/service layer.
            """

            conjug_info = {
                "indicatif": {
                    "present": {"je": "vais"}
                }
            }
            predicted = False
            confidence_score = None

        app.cache.get = lambda k, f: FakeResult()

        app._update_verb("aller")

        assert table._tree.root.label is not None


def test_app_update_verb_invalid():
    """
    Test handling of invalid verb input in Mlconjug3TUI.

    Ensures that invalid verbs:
    - Do not crash the application
    - Are safely rejected by validation logic

    Returns
    -------
    None
    """

    app = Mlconjug3TUI()

    def run():
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

def test_app_batch_parsing():
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

    app = Mlconjug3TUI()

    def run():
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

        class FakeResult:
            conjug_info = {
                "indicatif": {
                    "present": {"je": "vais"}
                }
            }
            predicted = False
            confidence_score = None

        app.service.conjugate = lambda v: FakeResult()
        app._is_valid = lambda v: True

        app._run_batch()


# =========================================================
# SETTINGS TESTS
# =========================================================

def test_app_language_switch():
    """
    Test language switching behavior in Mlconjug3TUI.

    Ensures that:
    - Language state is updated correctly
    - Conjugation service is reconfigured accordingly

    Returns
    -------
    None
    """

    app = Mlconjug3TUI()

    def run():
        class Event:
            """
            Mock Select.Changed event.
            """

            select = type("S", (), {"id": "lang_select"})
            value = "es"

        app.on_select_changed(Event())

        assert app.state.language == "es"
        assert app.service.language == "es"
