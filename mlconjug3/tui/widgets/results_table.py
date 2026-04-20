"""
results_table.py

Tree-based conjugation explorer widget for mlconjug3 TUI.

This widget renders hierarchical conjugation data in a safe,
interactive tree structure using Textual's Tree component.

It is designed to:
- Prevent runtime crashes caused by malformed conjugation data
- Render both rule-based and ML-based conjugation outputs
- Support batch and single-verb visualization modes
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from textual.widgets import Tree, Static
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Tree-based conjugation explorer widget.

    This widget displays conjugation data in a hierarchical tree format:
    mood → tense → persons/forms.

    It supports:
    - Single verb display mode
    - Batch verb accumulation mode
    - Safe rendering of incomplete or malformed data
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the ResultsTable widget.

        Parameters
        ----------
        *args : Any
            Positional arguments passed to Static.
        **kwargs : Any
            Keyword arguments passed to Static.
        """
        super().__init__(*args, **kwargs)

        self._tree: Tree = Tree("")
        self._tree.show_root = True

        self._batch_mode: bool = False
        self._batch_roots: Dict[str, Tree.Node] = {}

    # -------------------------
    # LIFECYCLE
    # -------------------------
    def compose(self) -> ComposeResult:
        """
        Compose the widget layout.

        Yields
        ------
        ComposeResult
            The tree widget used for rendering conjugation data.
        """
        yield self._tree

    # -------------------------
    # SAFE UTILITIES
    # -------------------------
    def _safe_form(self, value: Any) -> str:
        """
        Safely convert a conjugation form into a displayable string.

        This method ensures that None or invalid values do not crash
        the Tree renderer.

        Parameters
        ----------
        value : Any
            Raw conjugation form value.

        Returns
        -------
        str
            Sanitized string representation of the value.
        """
        if value is None:
            return "?"

        if isinstance(value, str):
            value = value.strip()
            return value if value else "?"

        return str(value)

    def clear(self) -> None:
        """
        Clear the tree content and reset internal state.
        """
        self._tree.root.label = ""

        for child in list(self._tree.root.children):
            child.remove()

        self._batch_roots.clear()
        self._tree.refresh()

    def _build_badge(self, mode: str, confidence: Optional[float]) -> str:
        """
        Build a mode badge for display in the tree root label.

        Parameters
        ----------
        mode : str
            Conjugation mode ("ML" or "RULE").
        confidence : float, optional
            ML confidence score if available.

        Returns
        -------
        str
            Formatted badge string.
        """
        if mode == "ML":
            if confidence is not None:
                return f"ML ({confidence:.2f})"
            return "ML"
        return "RULE"

    def _normalize_form(self, verb: str, form: Any) -> str:
        """
        Normalize conjugated forms by removing duplicated verb roots.

        Parameters
        ----------
        verb : str
            Base infinitive verb.
        form : Any
            Raw conjugated form.

        Returns
        -------
        str
            Normalized conjugated form.
        """
        form = self._safe_form(form)

        if form == "?":
            return form

        if form.startswith(verb + verb):
            return form[len(verb):]

        if len(verb) > 3 and form.startswith(verb[:3] * 2):
            return form[len(verb[:3]):]

        return form

    # -------------------------
    # MAIN API
    # -------------------------
    def update_conjugation(
        self,
        verb: str,
        conjugation: Dict[str, Any],
        append: bool = False,
        confidence: Optional[float] = None,
        mode: str = "RULE",
    ) -> None:
        """
        Render conjugation data into the tree view.

        Parameters
        ----------
        verb : str
            Infinitive verb being displayed.
        conjugation : dict
            Nested conjugation structure:
            {mood -> tense -> person -> form}
        append : bool, optional
            If True, adds to batch view instead of replacing.
        confidence : float, optional
            ML confidence score if available.
        mode : str, optional
            Conjugation mode ("ML" or "RULE").

        Returns
        -------
        None
        """
        badge: str = self._build_badge(mode, confidence)
        tree: Tree = self._tree

        # -------------------------
        # BATCH MODE
        # -------------------------
        if append:
            self._batch_mode = True

            if verb in self._batch_roots:
                verb_node = self._batch_roots[verb]
                verb_node.children.clear()
            else:
                verb_node = tree.root.add(f"{verb} [{badge}]", expand=False)
                self._batch_roots[verb] = verb_node

        else:
            self._batch_mode = False
            self._batch_roots.clear()

            tree.root.label = f"{verb}  [{badge}]"

            for child in list(tree.root.children):
                child.remove()

            verb_node = tree.root

        # -------------------------
        # TREE BUILDING
        # -------------------------
        for mood, tenses in (conjugation or {}).items():
            mood_node = verb_node.add(str(mood).capitalize(), expand=False)

            for tense, persons in (tenses or {}).items():
                tense_node = mood_node.add(str(tense).capitalize(), expand=False)

                # CASE 1: dict structure
                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)
                        clean_form = self._safe_form(clean_form)

                        tense_node.add_leaf(f"{person} ? {clean_form}")

                # CASE 2: string fallback
                else:
                    clean_form = self._normalize_form(verb, persons)
                    clean_form = self._safe_form(clean_form)

                    tense_node.add_leaf(clean_form)

        tree.refresh()
