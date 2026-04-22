"""
mlconjug3.tui.widgets.profile_panel

Unified verb profile panel for exploration and learning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from mlconjug3.core.morphology.summary import VerbMorphologySummary
from mlconjug3.tui.lexicon import VerbLexiconEntry


ConjugationTable = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class VerbProfile:
    """
    Render-ready verb profile payload.
    """

    verb: str
    root: Optional[str]
    template: Optional[str]
    morphology: VerbMorphologySummary
    lexicon: Optional[VerbLexiconEntry]
    predicted: bool
    confidence_score: Optional[float]
    missing_forms: tuple[str, ...]


class ProfilePanel(Vertical):
    """
    Unified verb profile panel (template/root/class + morphology + lexicon hints).
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._profile: Optional[VerbProfile] = None
        self._title = Static("Profile", classes="title")
        self._meta = Static("", id="profile_meta", markup=True)
        self._morph = Static("", id="profile_morph", markup=False)
        self._lex = Static("", id="profile_lex", markup=False)
        self._missing = Static("", id="profile_missing", markup=False)

    def compose(self) -> ComposeResult:
        yield self._title
        yield self._meta
        yield self._morph
        yield self._lex
        yield self._missing

    def set_profile(self, profile: VerbProfile) -> None:
        """
        Update displayed profile.
        """

        self._profile = profile
        tpl = profile.template or "?"
        root = profile.root or "?"
        cls = profile.morphology.conjugation_class or "?"
        irr = "⚡ predicted" if profile.predicted else "rule"
        conf = (
            f"{profile.confidence_score:.2f}"
            if isinstance(profile.confidence_score, float)
            else "?"
        )
        self._meta.update(
            f"[b]{profile.verb}[/b]  "
            f"[#9aa4b2]•[/] [b]🏷[/b] [#9aa4b2]{tpl}[/]  "
            f"[b]🌱[/b] [#9aa4b2]{root}[/]  "
            f"[b]📚[/b] [#9aa4b2]{cls}[/]  "
            f"[#9aa4b2]•[/] [b]{irr}[/b] ([#9aa4b2]{conf}[/])"
        )

        m = profile.morphology
        prod = f"{m.productivity:.2f}" if m.productivity is not None else "?"
        defe = f"{m.defectiveness:.2f}" if m.defectiveness is not None else "?"
        self._morph.update(
            "\n".join(
                [
                    f"Defective: {'yes' if m.defective else 'no'}  Defectiveness: {defe}",
                    f"Productivity: {prod}  Distinct forms: {m.distinct_forms}",
                    f"Filled: {m.filled_cells}  Missing: {m.missing_cells}",
                    f"Moods: {', '.join(m.moods)}",
                    f"Tenses: {', '.join(m.tenses)}",
                ]
            )
        )

        if profile.lexicon is None:
            self._lex.update("Lexicon: (no entry)")
        else:
            e = profile.lexicon
            freq = f"{e.frequency:.2f}" if e.frequency is not None else "?"
            regs = ", ".join(sorted(e.registers)) if e.registers else "?"
            aux = ", ".join(e.auxiliaries) if e.auxiliaries else "?"
            frames = " | ".join(e.valency_frames) if e.valency_frames else "?"
            refl = (
                "yes" if e.reflexive is True else ("no" if e.reflexive is False else "?")
            )
            self._lex.update(
                "\n".join(
                    [
                        f"Transitivity: {e.transitivity or '?'}  Reflexive: {refl}",
                        f"Valency: {frames}",
                        f"Auxiliaries: {aux}",
                        f"Register: {regs}  Frequency: {freq}",
                    ]
                )
            )

        if not profile.missing_forms:
            self._missing.update("Missing forms: (none detected)")
        else:
            self._missing.update(
                "Missing forms:\n" + "\n".join(f"- {x}" for x in profile.missing_forms[:30])
            )

    def clear(self) -> None:
        """
        Clear panel content.
        """
        self._profile = None
        self._meta.update("")
        self._morph.update("")
        self._lex.update("")
        self._missing.update("")

