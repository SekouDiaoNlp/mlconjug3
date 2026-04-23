from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import UIPreferences


@dataclass
class ColorPalette:
    name: str

    irregular_fg: str
    irregular_style: str
    irregular_symbol: str

    defective_fg: str
    defective_style: str

    mood_indicative: str
    mood_subjunctive: str
    mood_conditional: str
    mood_imperative: str
    mood_participle: str

    border: str
    header_bg: str
    header_fg: str
    panel_bg: str

    badge_irregular: str
    badge_regular: str
    badge_research: str


PALETTES: dict[str, ColorPalette] = {
    "dark": ColorPalette(
        name="dark",
        irregular_fg="#e3b341",
        irregular_style="bold",
        irregular_symbol=" ?",
        defective_fg="#484f58",
        defective_style="italic",
        mood_indicative="#58a6ff",
        mood_subjunctive="#bc8cff",
        mood_conditional="#79c0ff",
        mood_imperative="#ffa657",
        mood_participle="#7ee787",
        border="#30363d",
        header_bg="#161b22",
        header_fg="#c9d1d9",
        panel_bg="#0d1117",
        badge_irregular="#e3b341",
        badge_regular="#3fb950",
        badge_research="#bc8cff",
    ),
    "light": ColorPalette(
        name="light",
        irregular_fg="#b36200",
        irregular_style="bold",
        irregular_symbol=" ?",
        defective_fg="#8c959f",
        defective_style="italic",
        mood_indicative="#0969da",
        mood_subjunctive="#8250df",
        mood_conditional="#0969da",
        mood_imperative="#cf4a02",
        mood_participle="#1a7f37",
        border="#d0d7de",
        header_bg="#f6f8fa",
        header_fg="#24292f",
        panel_bg="#ffffff",
        badge_irregular="#b36200",
        badge_regular="#1a7f37",
        badge_research="#8250df",
    ),
    "high_contrast": ColorPalette(
        name="high_contrast",
        irregular_fg="#ffff00",
        irregular_style="bold underline",
        irregular_symbol=" [!]",
        defective_fg="#808080",
        defective_style="italic",
        mood_indicative="#00ffff",
        mood_subjunctive="#ff80ff",
        mood_conditional="#80ffff",
        mood_imperative="#ffaa00",
        mood_participle="#80ff80",
        border="#ffffff",
        header_bg="#000000",
        header_fg="#ffffff",
        panel_bg="#000000",
        badge_irregular="#ffff00",
        badge_regular="#00ff00",
        badge_research="#ff80ff",
    ),
    "deuteranopia": ColorPalette(
        name="deuteranopia",
        irregular_fg="#2277ff",
        irregular_style="bold underline",
        irregular_symbol=" [~]",
        defective_fg="#888888",
        defective_style="italic",
        mood_indicative="#2277ff",
        mood_subjunctive="#ff8800",
        mood_conditional="#55aaff",
        mood_imperative="#ffaa44",
        mood_participle="#8844ff",
        border="#444444",
        header_bg="#1a1a2e",
        header_fg="#e0e0e0",
        panel_bg="#0f0f1a",
        badge_irregular="#2277ff",
        badge_regular="#8844ff",
        badge_research="#ff8800",
    ),
    "protanopia": ColorPalette(
        name="protanopia",
        irregular_fg="#1199dd",
        irregular_style="bold underline",
        irregular_symbol=" [~]",
        defective_fg="#888888",
        defective_style="italic",
        mood_indicative="#1199dd",
        mood_subjunctive="#dd9900",
        mood_conditional="#44aaee",
        mood_imperative="#ddaa33",
        mood_participle="#9944dd",
        border="#444444",
        header_bg="#1a1a2e",
        header_fg="#e0e0e0",
        panel_bg="#0f0f1a",
        badge_irregular="#1199dd",
        badge_regular="#9944dd",
        badge_research="#dd9900",
    ),
}


class A11yManager:
    def __init__(self, prefs: "UIPreferences") -> None:
        self.prefs = prefs
        self._palette = self._resolve()

    def _resolve(self) -> ColorPalette:
        if self.prefs.colorblind_mode != "none":
            return PALETTES.get(self.prefs.colorblind_mode, PALETTES["dark"])
        return PALETTES.get(self.prefs.theme, PALETTES["dark"])

    def refresh(self) -> None:
        self._palette = self._resolve()

    @property
    def palette(self) -> ColorPalette:
        return self._palette

    def mood_color(self, mood: str) -> str:
        p = self._palette
        m = mood.lower()

        if "indic" in m:
            return p.mood_indicative
        if "subj" in m:
            return p.mood_subjunctive
        if "cond" in m:
            return p.mood_conditional
        if "imperat" in m:
            return p.mood_imperative
        if "part" in m or "gerund" in m:
            return p.mood_participle

        return p.mood_indicative
