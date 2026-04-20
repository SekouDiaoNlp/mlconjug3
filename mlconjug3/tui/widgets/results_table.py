"""
results_table.py

Improved renderer with:
- RULE vs ML detection
- Confidence display
- Clean verb form normalization (FIX for prefix bug)
"""

from rich.table import Table
from rich.console import Group
from textual.widgets import Static


class ResultsTable(Static):
    """
    Displays conjugation results safely for:
    - single verb mode
    - batch mode
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tables = []

    # -----------------------------
    # BADGE SYSTEM
    # -----------------------------
    def _build_badge(self, mode: str, confidence: float = None) -> str:
        if mode == "ML":
            if confidence is not None:
                return f"🧠 ML ({confidence:.2f})"
            return "🧠 ML"
        return "📘 RULE"

    # -----------------------------
    # FIX: FORM NORMALIZATION
    # -----------------------------
    def _normalize_form(self, verb: str, form: str) -> str:
        """
        Prevents duplicated infinitive prefixes caused by mixed backend behavior.
        """
        if not form:
            return form

        # If form already contains verb twice at start, fix it
        if form.startswith(verb + verb):
            return form[len(verb):]

        # If form redundantly repeats root pattern (common ML edge case)
        if len(verb) > 3 and form.startswith(verb[:3] * 2):
            return form[len(verb[:3]):]

        return form

    # -----------------------------
    # MAIN RENDER METHOD
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
        title = f"Conjugation of '{verb}'   [{badge}]"

        table = Table(title=title, show_header=True)

        table.add_column("Mood")
        table.add_column("Tense")
        table.add_column("Person")
        table.add_column("Form")

        for mood, tenses in conjugation.items():
            for tense, persons in tenses.items():

                if isinstance(persons, dict):
                    for person, form in persons.items():
                        clean_form = self._normalize_form(verb, form)
                        table.add_row(mood, tense, str(person), clean_form)
                else:
                    clean_form = self._normalize_form(verb, persons)
                    table.add_row(mood, tense, "", clean_form)

                table.add_section()

        if append:
            self._tables.append(table)
            self.update(Group(*self._tables))
        else:
            self._tables = [table]
            self.update(table)
