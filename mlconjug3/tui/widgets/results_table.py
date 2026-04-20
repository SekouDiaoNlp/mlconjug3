"""
results_table.py

Tree-based conjugation explorer (IMPROVED VERSION)
"""

from textual.widgets import Tree, Static
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Tree-based conjugation explorer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FIX: empty root label (no "No verb loaded")
        self._tree = Tree("")
        self._tree.show_root = True

    def compose(self) -> ComposeResult:
        yield self._tree

    def clear(self):
        """
        Clear the tree safely.
        """
        self._tree.root.label = ""
        for child in list(self._tree.root.children):
            child.remove()
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
        badge = self._build_badge(mode, confidence)
        tree = self._tree

        # Reset root
        tree.root.label = f"{verb}  [{badge}]"

        for child in list(tree.root.children):
            child.remove()

        for mood, tenses in conjugation.items():
            mood_node = tree.root.add(mood.capitalize(), expand=False)

            for tense, persons in tenses.items():
                tense_node = mood_node.add(tense.capitalize(), expand=False)

                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)

                        # LEAF NODE → no expand arrow
                        node = tense_node.add_leaf(f"{person} → {clean_form}")

                else:
                    clean_form = self._normalize_form(verb, persons)
                    tense_node.add_leaf(clean_form)

        tree.refresh()
