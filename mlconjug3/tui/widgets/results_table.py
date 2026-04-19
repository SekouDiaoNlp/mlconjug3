"""
results_table.py

Rich-based conjugation table renderer.
"""

from rich.table import Table
from textual.widgets import Static


class ResultsTable(Static):
    """
    Displays conjugation results in a Rich table.
    """

    def update_conjugation(self, verb: str, conjugation: dict):
        table = Table(title=f"Conjugation: {verb}", show_header=True)

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

        self.update(table)

    def update_batch(self, data: dict):
        table = Table(title="Batch Conjugation", show_header=True)

        table.add_column("Verb")
        table.add_column("Mood")
        table.add_column("Tense")
        table.add_column("Person")
        table.add_column("Form")

        for verb, conjugation in data.items():
            for mood, tenses in conjugation.items():
                for tense, persons in tenses.items():
                    if isinstance(persons, dict):
                        for person, form in persons.items():
                            table.add_row(verb, mood, tense, str(person), form)
                    else:
                        table.add_row(verb, mood, tense, "", persons)

        self.update(table)
