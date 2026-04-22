# theme.py
"""
theme.py

Centralized design system for mlconjug3 TUI.

Defines:
- Semantic colors
- Accessibility variants
- Reusable style tokens
"""

from __future__ import annotations

# -------------------------
# COLOR SYSTEM (WCAG-aware)
# -------------------------

class Colors:
    # Base
    BG_DARK = "#1a1b26"
    BG_LIGHT = "#f5f7fa"

    FG_PRIMARY = "#e6edf3"
    FG_MUTED = "#9aa4b2"

    # Brand
    PRIMARY = "#7aa2ff"       # calm blue
    SECONDARY = "#bb9af7"     # soft purple

    # Semantic
    SUCCESS = "#9ece6a"
    ERROR = "#f7768e"
    WARNING = "#e0af68"
    INFO = "#7dcfff"

    # Special
    IRREGULAR = "#ff9e64"
    HIGHLIGHT = "#2ac3de"

    # Accessibility (high contrast)
    HC_BG = "#000000"
    HC_FG = "#ffffff"


# -------------------------
# EMOJI SYSTEM (UX LAYER)
# -------------------------

class Emojis:
    VERB = "✨"
    SEARCH = "🔍"
    LEARN = "🧠"
    WARNING = "⚠️"
    SUCCESS = "✅"
    ERROR = "❌"
    FAVORITE = "⭐"
    HISTORY = "🕘"
    FILTER = "🎛️"
    EXPORT = "📤"
    COMPARE = "⚖️"
    BOOK = "📘"


# -------------------------
# STYLE TOKENS
# -------------------------

class Styles:
    TITLE = "bold"
    SUBTITLE = "bold"
    MUTED = "dim"

    PANEL = "round"
    PANEL_FOCUS = "heavy"

    SPACING_COMPACT = 0
    SPACING_SPACIOUS = 1


# -------------------------
# THEMES
# -------------------------

THEMES = {
    "dark": {
        "background": Colors.BG_DARK,
        "foreground": Colors.FG_PRIMARY,
    },
    "light": {
        "background": Colors.BG_LIGHT,
        "foreground": "#1a1b26",
    },
    "high_contrast": {
        "background": Colors.HC_BG,
        "foreground": Colors.HC_FG,
    },
}
