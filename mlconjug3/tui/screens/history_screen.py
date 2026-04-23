from textual.screen import Screen
from textual.widgets import Static
from textual.app import ComposeResult


class HistoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("History screen (TODO)")
