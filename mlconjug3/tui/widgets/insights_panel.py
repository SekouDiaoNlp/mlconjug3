"""
mlconjug3.tui.widgets.insights_panel

Insights panel for surfacing morphology metadata.
"""

from __future__ import annotations

from typing import Any, Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from mlconjug3.core.morphology.summary import VerbMorphologySummary


class InsightsPanel(Vertical):
    """
    Render a morphology summary as a compact panel.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._summary: Optional[VerbMorphologySummary] = None
        self._view = Static("", id="insights_text")

    def compose(self) -> ComposeResult:
        yield Static("Insights", classes="title")
        yield self._view

    def set_summary(
        self,
        summary: VerbMorphologySummary,
        *,
        verb_root: Optional[str] = None,
        verb_template: Optional[str] = None,
    ) -> None:
        """
        Update the displayed summary.
        """

        self._summary = summary
        prod = (
            f"{summary.productivity:.2f}" if summary.productivity is not None else "?"
        )
        defe = (
            f"{summary.defectiveness:.2f}" if summary.defectiveness is not None else "?"
        )
        conj = summary.conjugation_class or "?"
        tpl = verb_template or "?"
        root = verb_root or "?"
        irr = "yes" if summary.irregular_proxy else "no"
        defective = "yes" if summary.defective else "no"
        trans = summary.transitivity or "?"
        text = (
            f"Template: {tpl}\n"
            f"Root: {root}\n"
            f"Class: {conj}\n"
            f"Irregular(proxy): {irr}\n"
            f"Defective: {defective}  Defectiveness: {defe}\n"
            f"Transitivity: {trans}\n"
            f"Moods: {', '.join(summary.moods)}\n"
            f"Tenses: {', '.join(summary.tenses)}\n"
            f"Persons: {', '.join(summary.persons)}\n"
            f"Distinct forms: {summary.distinct_forms}\n"
            f"Filled: {summary.filled_cells}  Missing: {summary.missing_cells}\n"
            f"Productivity: {prod}\n"
        )
        self._view.update(text)
