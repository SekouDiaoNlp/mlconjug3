"""
results_table.py

Tree-based conjugation explorer (IMPROVED + FIXED BATCH SUPPORT)
"""

from textual.widgets import Tree, Static
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Tree-based conjugation explorer.
    Now supports multi-verb batch mode correctly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tree = Tree("")
        self._tree.show_root = True

        # 🔥 FIX: batch-aware storage
        self._batch_mode = False
        self._batch_roots = {}

    def compose(self) -> ComposeResult:
        yield self._tree

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

    def _normalize_form(self, verb: str, form: str) -> str:
        if not form:
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
        FIXED:
        - append=True now preserves previous verbs (batch mode)
        """

        badge = self._build_badge(
            mode if mode in ("ML", "RULE") else "RULE",
            confidence
        )
        tree = self._tree

        # -------------------------
        # BATCH MODE ENABLED
        # -------------------------
        if append:
            self._batch_mode = True

            # create or reuse root node per verb
            if verb in self._batch_roots:
                verb_node = self._batch_roots[verb]
                verb_node.children.clear()
            else:
                verb_node = tree.root.add(f"{verb} [{badge}]", expand=False)
                self._batch_roots[verb] = verb_node

        else:
            # normal mode → reset everything
            self._batch_mode = False
            self._batch_roots.clear()

            tree.root.label = f"{verb}  [{badge}]"
            for child in list(tree.root.children):
                child.remove()

            verb_node = tree.root

        # -------------------------
        # BUILD TREE
        # -------------------------
        for mood, tenses in conjugation.items():
            mood_node = verb_node.add(mood.capitalize(), expand=False)

            for tense, persons in tenses.items():
                tense_node = mood_node.add(tense.capitalize(), expand=False)

                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)
                        tense_node.add_leaf(f"{person} ? {clean_form}")
                else:
                    clean_form = self._normalize_form(verb, persons)
                    tense_node.add_leaf(clean_form)

        tree.refresh()
