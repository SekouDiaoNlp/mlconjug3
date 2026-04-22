import os


TUI_STRUCTURE = {
    "mlconjug3/tui": [
        "__init__.py",
        "app.py",
        "state.py",
        "theme.py",
    ],
    "mlconjug3/tui/screens": [
        "__init__.py",
        "conjugate.py",
        "batch.py",
        "explorer.py",
        "settings.py",
    ],
    "mlconjug3/tui/widgets": [
        "__init__.py",
        "verb_input.py",
        "results_table.py",
        "verb_list.py",
        "status_bar.py",
    ],
    "mlconjug3/core": [
        "__init__.py",
        "conjugation_service.py",
        "export.py",
    ],
}


APP_SKELETONS = {
    "mlconjug3/tui/app.py": '''from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane

class MlConjug3TUI(App):
    """Main TUI application for mlconjug3."""

    CSS_PATH = "theme.tcss"

    def compose(self) -> ComposeResult:
        yield Header()

        with TabbedContent():
            with TabPane("Conjugate"):
                yield

            with TabPane("Batch"):
                yield

            with TabPane("Explorer"):
                yield

            with TabPane("Settings"):
                yield

        yield Footer()


if __name__ == "__main__":
    MlConjug3TUI().run()
''',

    "mlconjug3/tui/state.py": '''"""
Shared application state for TUI.
Keeps language, subject format, and cached results.
"""

class TUIState:
    def __init__(self):
        self.language = "fr"
        self.subject = "abbrev"
        self.cache = {}
''',

    "mlconjug3/core/conjugation_service.py": '''"""
Core service layer shared between CLI and TUI.
"""

from mlconjug3.mlconjug import Conjugator


class ConjugationService:
    def __init__(self, language="fr", subject="abbrev"):
        self.language = language
        self.subject = subject
        self.conjugator = Conjugator(language)

    def set_language(self, language):
        self.language = language
        self.conjugator = Conjugator(language)

    def conjugate(self, verbs):
        return self.conjugator.conjugate(verbs, self.subject)
''',

    "mlconjug3/tui/theme.py": '''"""
Placeholder for TUI styling (Textual CSS).
"""

THEME = """
Screen {
    background: #0f111a;
    color: white;
}

TabPane {
    padding: 1;
}
"""
''',
}


def create_structure():
    for folder, files in TUI_STRUCTURE.items():
        os.makedirs(folder, exist_ok=True)
        for file in files:
            path = os.path.join(folder, file)
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# {file}\n")

    for path, content in APP_SKELETONS.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    print("✅ mlconjug3 TUI structure created successfully")


if __name__ == "__main__":
    create_structure()
