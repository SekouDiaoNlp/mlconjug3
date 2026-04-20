"""
results_table.py

Tree-based conjugation explorer (ROBUST + CRASH-SAFE VERSION)
"""

from textual.widgets import Tree, Static
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Tree-based conjugation explorer.

    FIXES:
    - Prevents NoneType crashes in Textual Tree
    - Safe rendering for ML + rule-based conjugation outputs
    - Handles missing / incomplete linguistic data gracefully
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tree = Tree("")
        self._tree.show_root = True

        self._batch_mode = False
        self._batch_roots = {}

    def compose(self) -> ComposeResult:
        yield self._tree

    # -----------------------------
    # SAFE HELPERS
    # -----------------------------
    def _safe_form(self, value):
        """
        Ensures Tree never receives None or invalid values.
        """
        if value is None:
            return "—"

        if isinstance(value, str):
            value = value.strip()
            return value if value else "—"

        return str(value)

    def clear(self):
        self._tree.root.label = ""

        for child in list(self._tree.root.children):
            child.remove()

        self._batch_roots.clear()
        self._tree.refresh()

    # -----------------------------
    def _build_badge(self, mode: str, confidence: float = None) -> str:
        if mode == "ML":
            if confidence is not None:
                return f"ML ({confidence:.2f})"
            return "ML"
        return "RULE"

    def _normalize_form(self, verb: str, form: str):
        """
        Keeps original logic but ensures safe output.
        """
        form = self._safe_form(form)

        if form == "—":
            return form

        if form.startswith(verb + verb):
            return form[len(verb):]

        if len(verb) > 3 and form.startswith(verb[:3] * 2):
            return form[len(verb[:3]):]

        return form

    # -----------------------------
    def update_conjugation(
        self,
        verb: str,
        conjugation: dict,
        append: bool = False,
        confidence: float = None,
        mode: str = "RULE",
    ):
        """
        SAFE TREE RENDERING:
        - Never allows None into Textual Tree nodes
        - Prevents crash when ML returns incomplete conjugations
        """

        badge = self._build_badge(mode, confidence)
        tree = self._tree

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
        # TREE BUILDING (SAFE)
        # -------------------------
        for mood, tenses in (conjugation or {}).items():
            mood_node = verb_node.add(str(mood).capitalize(), expand=False)

            for tense, persons in (tenses or {}).items():
                tense_node = mood_node.add(str(tense).capitalize(), expand=False)

                # CASE: dict (standard)
                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)
                        clean_form = self._safe_form(clean_form)

                        tense_node.add_leaf(f"{person} ? {clean_form}")

                # CASE: string or fallback
                else:
                    clean_form = self._normalize_form(verb, persons)
                    clean_form = self._safe_form(clean_form)

                    tense_node.add_leaf(clean_form)

        tree.refresh()
