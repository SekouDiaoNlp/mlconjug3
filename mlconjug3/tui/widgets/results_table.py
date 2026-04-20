"""
results_table.py

Improved renderer with optional ML metadata support.
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

    def update_conjugation(
        self,
        verb: str,
        conjugation: dict,
        append: bool = False,
        confidence: float = None,
        mode: str = "RULE",
    ):
        """
        Render conjugation safely.

        Parameters
        ----------
        verb : str
        conjugation : dict
        append : bool
        confidence : float (optional ML confidence)
        mode : str ("RULE" | "ML")
        """

        title = f"Conjugation of '{verb}'"

        # -------------------------
        # ML / RULE BADGE
        # -------------------------
        if mode == "ML" and confidence is not None:
            title += f"  ⚠ ML ({confidence})"
        else:
            title += "  ✓ RULE"

        table = Table(
            title=title,
            show_header=True,
        )

        table.add_column("Mood")
        table.add_column("Tense")
        table.add_column("Person")
        table.add_column("Form")

        for mood, tenses in conjugation.items():
            for tense, persons in tenses.items():

                if isinstance(persons, dict):
                    for person, form in persons.items():
                        table.add_row(mood, tense, str(person), form)
                else:
                    table.add_row(mood, tense, "", persons)

                table.add_section()

        # -------------------------
        # RENDER MODE
        # -------------------------
        if append:
            self._tables.append(table)
            self.update(Group(*self._tables))
        else:
            self._tables = [table]
            self.update(table)


