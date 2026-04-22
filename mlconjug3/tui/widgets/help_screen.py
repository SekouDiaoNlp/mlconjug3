"""
mlconjug3.tui.widgets.help_screen

In-app help modal for the Textual TUI.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen[None]):
    """
    Modal help screen listing key shortcuts and navigation hints.
    """

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Vertical {
        width: 80%;
        max-width: 84;
        border: round #2a3244;
        padding: 1 2;
        background: #11172a;
    }

    Screen.theme-light HelpScreen > Vertical {
        background: #ffffff;
        border: round #c7d2fe;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Help", classes="title")
            yield Static(
                "\n".join(
                    [
                        "[b]?[/b]  Help",
                        "[b]f[/b]  Toggle favorite",
                        "[b]t[/b]  Toggle theme (Light/Dark)",
                        "[b]d[/b]  Toggle density (Compact/Spacious)",
                        "",
                        "[b]Esc[/b]  Close",
                        "",
                        "Tip: Use Tab / Shift+Tab to move focus, and Enter to select.",
                    ]
                ),
                markup=True,
                classes="muted",
            )

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)

