"""
results_table.py

Fixed batch-safe renderer for mlconjug3 TUI.

Fixes:
- no string concatenation of Rich objects
- proper multi-table rendering
- stable batch accumulation
"""

from rich.table import Table
from rich.console import Group
from textual.widgets import Static


class ResultsTable(Static):
    """
    Displays conjugation results safely for:
    - single verb mode
    - batch mode (multi-table view)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tables = []

    def update_conjugation(self, verb: str, conjugation: dict, append: bool = False):
        """
        Render conjugation safely.

        Parameters
        ----------
        verb : str
        conjugation : dict
        append : bool
        """

        table = Table(
            title=f"Conjugation of '{verb}'",
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

        # ---------------------------
        # SINGLE vs BATCH MODE
        # ---------------------------
        if append:
            self._tables.append(table)
            self.update(Group(*self._tables))
        else:
            self._tables = [table]
            self.update(table)
