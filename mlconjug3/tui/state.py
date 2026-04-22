"""
state.py

Global state container for the mlconjug3 TUI application.

This module defines a lightweight state manager used across the
Textual-based terminal UI. It tracks user preferences, navigation
history, and interactive session data such as favorites.

The state object is intentionally simple and framework-agnostic,
allowing it to be safely reused across UI components without coupling.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Deque, Set, Any, Optional


@dataclass(frozen=True, slots=True)
class TUIStateSnapshot:
    """
    Serializable snapshot of TUI state.

    Attributes
    ----------
    language:
        Language code.
    subject:
        Subject output mode.
    history:
        Recent verbs, newest first.
    favorites:
        Favorite verbs.
    learn_streak:
        Current learning streak.
    learn_best_streak:
        Best learning streak achieved.
    learn_seed:
        Seed used to pick quiz items deterministically.
    selected_moods:
        Selected moods for global filtering.
    selected_tenses:
        Selected tenses for global filtering.
    """

    language: str
    subject: str
    history: list[str]
    favorites: list[str]
    learn_streak: int
    learn_best_streak: int
    learn_seed: int
    selected_moods: list[str]
    selected_tenses: list[str]


class TUIState:
    """
    Shared application state for the mlconjug3 TUI.

    This class acts as a centralized in-memory store for:
    - User-selected language
    - Conjugation display mode (subject format)
    - Recently accessed verbs (history)
    - Favorite verbs

    It is designed to be lightweight and mutable, with no persistence
    layer by default.
    """

    def __init__(self, *, storage_path: Optional[Path] = None) -> None:
        """
        Initialize the TUI state container with default values.

        Parameters
        ----------
        storage_path:
            Optional explicit path for persistence. When not provided, a default
            path under `~/.config/mlconjug3/tui_state.json` is used.
        """

        self._storage_path: Path = storage_path or self.default_storage_path()
        self.language: str = "fr"
        self.subject: str = "abbrev"

        self.history: Deque[str] = deque(maxlen=50)
        self.favorites: Set[str] = set()
        self.learn_streak: int = 0
        self.learn_best_streak: int = 0
        self.learn_seed: int = 0
        self.selected_moods: Set[str] = set()
        self.selected_tenses: Set[str] = set()

    @staticmethod
    def default_storage_path() -> Path:
        """
        Return the default persistence path.

        Returns
        -------
        pathlib.Path
            Default state file path.
        """

        override = os.environ.get("MLCONJUG3_TUI_STATE_PATH")
        if override:
            return Path(override).expanduser()
        return Path("~/.config/mlconjug3/tui_state.json").expanduser()

    @property
    def storage_path(self) -> Path:
        """
        Persistence path used for load/save.

        Returns
        -------
        pathlib.Path
            Storage path.
        """

        return self._storage_path

    def snapshot(self) -> TUIStateSnapshot:
        """
        Capture a serializable snapshot of the current state.

        Returns
        -------
        TUIStateSnapshot
            Snapshot of language, subject, history, and favorites.
        """

        return TUIStateSnapshot(
            language=self.language,
            subject=self.subject,
            history=list(self.history),
            favorites=sorted(self.favorites),
            learn_streak=self.learn_streak,
            learn_best_streak=self.learn_best_streak,
            learn_seed=self.learn_seed,
            selected_moods=sorted(self.selected_moods),
            selected_tenses=sorted(self.selected_tenses),
        )

    def apply_snapshot(self, snapshot: TUIStateSnapshot) -> None:
        """
        Apply a snapshot to this state instance.

        Parameters
        ----------
        snapshot:
            Snapshot to apply.
        """

        self.language = snapshot.language
        self.subject = snapshot.subject

        self.history.clear()
        for verb in snapshot.history[: self.history.maxlen]:
            self.history.append(verb)

        self.favorites = set(snapshot.favorites)
        self.learn_streak = snapshot.learn_streak
        self.learn_best_streak = snapshot.learn_best_streak
        self.learn_seed = snapshot.learn_seed
        self.selected_moods = set(snapshot.selected_moods)
        self.selected_tenses = set(snapshot.selected_tenses)

    def load(self) -> None:
        """
        Load state from disk if the storage file exists.
        """

        path = self.storage_path
        if not path.is_file():
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        snapshot = self._snapshot_from_json(data)
        if snapshot is None:
            return
        self.apply_snapshot(snapshot)

    def save(self) -> None:
        """
        Persist state to disk.

        Writes are performed atomically (write temp file then replace).
        """

        path = self.storage_path
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._snapshot_to_json(self.snapshot())
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(path)

    def _snapshot_to_json(self, snapshot: TUIStateSnapshot) -> dict[str, Any]:
        """
        Convert snapshot into a JSON-serializable structure.

        Parameters
        ----------
        snapshot:
            Snapshot to serialize.

        Returns
        -------
        dict[str, Any]
            JSON-friendly payload.
        """

        return {
            "version": 1,
            "language": snapshot.language,
            "subject": snapshot.subject,
            "history": snapshot.history,
            "favorites": snapshot.favorites,
            "learn_streak": snapshot.learn_streak,
            "learn_best_streak": snapshot.learn_best_streak,
            "learn_seed": snapshot.learn_seed,
            "selected_moods": snapshot.selected_moods,
            "selected_tenses": snapshot.selected_tenses,
        }

    def _snapshot_from_json(self, data: Any) -> Optional[TUIStateSnapshot]:
        """
        Parse snapshot from JSON data.

        Parameters
        ----------
        data:
            JSON-decoded data.

        Returns
        -------
        TUIStateSnapshot | None
            Snapshot when parsing succeeds, else None.
        """

        if not isinstance(data, dict):
            return None

        language = data.get("language")
        subject = data.get("subject")
        history = data.get("history")
        favorites = data.get("favorites")
        learn_streak = data.get("learn_streak", 0)
        learn_best_streak = data.get("learn_best_streak", 0)
        learn_seed = data.get("learn_seed", 0)
        selected_moods = data.get("selected_moods", [])
        selected_tenses = data.get("selected_tenses", [])

        if not isinstance(language, str) or not isinstance(subject, str):
            return None
        if not isinstance(history, list) or not isinstance(favorites, list):
            return None
        if not all(isinstance(v, str) for v in history):
            return None
        if not all(isinstance(v, str) for v in favorites):
            return None
        if not isinstance(learn_streak, int) or not isinstance(learn_best_streak, int):
            return None
        if not isinstance(learn_seed, int):
            return None
        if not isinstance(selected_moods, list) or not all(
            isinstance(v, str) for v in selected_moods
        ):
            return None
        if not isinstance(selected_tenses, list) or not all(
            isinstance(v, str) for v in selected_tenses
        ):
            return None

        return TUIStateSnapshot(
            language=language,
            subject=subject,
            history=history,
            favorites=favorites,
            learn_streak=learn_streak,
            learn_best_streak=learn_best_streak,
            learn_seed=learn_seed,
            selected_moods=selected_moods,
            selected_tenses=selected_tenses,
        )

    def add_history(self, verb: str) -> None:
        """
        Add a verb to the recent history list.

        The history is stored as a bounded deque (max length 50),
        ensuring old entries are automatically discarded.

        Parameters
        ----------
        verb : str
            The verb to record in history.
        """
        if verb:
            self.history.appendleft(verb)
            self.save()

    def toggle_favorite(self, verb: str) -> None:
        """
        Toggle the favorite status of a verb.

        If the verb is already marked as favorite, it will be removed.
        Otherwise, it will be added to the favorites set.

        Parameters
        ----------
        verb : str
            The verb to toggle in the favorites collection.
        """
        if verb in self.favorites:
            self.favorites.remove(verb)
        else:
            self.favorites.add(verb)
        self.save()
