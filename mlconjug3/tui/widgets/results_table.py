"""
results_table.py

Widget responsible for rendering conjugation tables inside the TUI.

Uses Rich Table for consistent formatting with the CLI.
"""

from rich.table import Table
from textual.widget import Widget
from textual.widgets import Static


class ResultsTable(Static):
    """
    Displays conjugation results in a Rich-formatted table.
    """

    def update_conjugation(self, verb: str, conjugation: dict, style: dict = None):
        """
        Render conjugation table for a verb.

        Parameters
        ----------
        verb : str
            Input verb.
        conjugation : dict
            Nested conjugation structure.
        style : dict, optional
            Styling options (optional CLI compatibility).
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
                        table.add_row(
                            mood, tense, str(person), form
                        )
                else:
                    table.add_row(mood, tense, "", persons)

                table.add_section()

        self.update(table)
