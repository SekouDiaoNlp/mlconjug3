"""
results_table.py

Tree-based conjugation explorer (FIXED VERSION)
"""

from textual.widgets import Tree, Static
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Tree-based conjugation explorer.

    Structure:
        Verb
         ├── Mood
         │    ├── Tense
         │    │    ├── Person → Form
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # IMPORTANT FIX: do NOT use "tree"
        self._tree = Tree("No verb loaded")
        self._tree.show_root = True

    def compose(self) -> ComposeResult:
        yield self._tree

    # -----------------------------
    # BADGE SYSTEM
    # -----------------------------
    def _build_badge(self, mode: str, confidence: float = None) -> str:
        if mode == "ML":
            if confidence is not None:
                return f"ML ({confidence:.2f})"
            return "ML"
        return "RULE"

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    def _normalize_form(self, verb: str, form: str) -> str:
        if not form:
            return form

        if form.startswith(verb + verb):
            return form[len(verb):]

        if len(verb) > 3 and form.startswith(verb[:3] * 2):
            return form[len(verb[:3]):]

        return form

    # -----------------------------
    # MAIN RENDER
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
        # Properly clear existing nodes (Textual-safe)
        for child in list(tree.root.children):
            child.remove()

        for mood, tenses in conjugation.items():
            mood_node = tree.root.add(mood.capitalize(), expand=False)

            for tense, persons in tenses.items():
                tense_node = mood_node.add(tense.capitalize(), expand=False)

                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)
                        tense_node.add(f"{person} → {clean_form}")

                else:
                    clean_form = self._normalize_form(verb, persons)
                    tense_node.add(clean_form)

        tree.refresh()
