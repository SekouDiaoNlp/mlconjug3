from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult


class CompareInputScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Compare screen (TODO)")
