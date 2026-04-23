"""
mlconjug3 TUI — State Management
AppState, UIPreferences, SessionStore
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path


CONFIG_DIR   = Path.home() / ".mlconjug3"
PREFS_FILE   = CONFIG_DIR / "preferences.json"
SESSION_FILE = CONFIG_DIR / "session.json"

SUPPORTED_LANGUAGES = ["fr", "en", "es", "it", "pt", "ro"]
LANGUAGE_NAMES = {
    "fr": "Français",
    "en": "English",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ro": "Română",
}
MODES = ["simple", "learner", "research"]


# ─── AppState ────────────────────────────────────────────────────────────────

@dataclass
class AppState:
    """Live runtime state (not persisted between sessions)."""
    verb: str = ""
    language: str = "fr"
    mode: str = "simple"          # simple | learner | research
    compare_verb: str = ""
    compare_active: bool = False
    side_panel_visible: bool = True
    last_error: str = ""


# ─── UIPreferences ───────────────────────────────────────────────────────────

@dataclass
class UIPreferences:
    """
    User preferences — persisted to ~/.mlconjug3/preferences.json.
    All fields have safe defaults so a missing/corrupt file is harmless.
    """
    theme: str = "dark"                  # dark | light | high_contrast
    reduced_motion: bool = False
    colorblind_mode: str = "none"        # none | deuteranopia | protanopia
    default_language: str = "fr"
    default_mode: str = "simple"
    show_confidence: bool = True
    show_learner_tips: bool = True
    history_limit: int = 100

    @classmethod
    def load(cls) -> "UIPreferences":
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if PREFS_FILE.exists():
            try:
                data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
                known = {k: v for k, v in data.items()
                         if k in cls.__dataclass_fields__}
                return cls(**known)
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        PREFS_FILE.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ─── SessionStore ─────────────────────────────────────────────────────────────

@dataclass
class SessionStore:
    """
    Search history + bookmarks — persisted to ~/.mlconjug3/session.json.
    History entries: {"verb": str, "language": str, "ts": int}
    Bookmark entries: {"verb": str, "language": str}
    """
    history:       list = field(default_factory=list)
    bookmarks:     list = field(default_factory=list)
    compare_pairs: list = field(default_factory=list)

    @classmethod
    def load(cls) -> "SessionStore":
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
                return cls(
                    history=data.get("history", []),
                    bookmarks=data.get("bookmarks", []),
                    compare_pairs=data.get("compare_pairs", []),
                )
            except Exception:
                pass
        return cls()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(
            json.dumps(
                {"history": self.history,
                 "bookmarks": self.bookmarks,
                 "compare_pairs": self.compare_pairs},
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def add_history(self, verb: str, language: str) -> None:
        self.history = [
            h for h in self.history
            if not (h["verb"] == verb and h["language"] == language)
        ]

        self.history.insert(0, {
            "verb": verb,
            "language": language,
            "ts": int(time.time()),
        })

        limit = 100  # fallback safe default (no UI coupling here)
        self.history = self.history[:limit]
        self.save()

    def toggle_bookmark(self, verb: str, language: str) -> bool:
        """Returns True if newly bookmarked, False if removed."""
        existing = [
            b for b in self.bookmarks
            if b["verb"] == verb and b["language"] == language
        ]
        if existing:
            self.bookmarks = [
                b for b in self.bookmarks
                if not (b["verb"] == verb and b["language"] == language)
            ]
            self.save()
            return False
        self.bookmarks.insert(0, {"verb": verb, "language": language})
        self.save()
        return True

    def is_bookmarked(self, verb: str, language: str) -> bool:
        return any(
            b["verb"] == verb and b["language"] == language
            for b in self.bookmarks
        )

    def recent_verbs(self, limit: int = 20) -> list:
        return self.history[:limit]
