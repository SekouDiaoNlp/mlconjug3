from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen[None]):
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
                        "f  Toggle favorite",
                        "t  Toggle theme (Light/Dark)",
                        "d  Toggle density (Compact/Spacious)",
                        "",
                        "Esc  Close",
                        "",
                        "Tip: Use Tab / Shift+Tab to move focus, Enter to select.",
                    ]
                ),
                markup=True,
                classes="muted",
            )

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
