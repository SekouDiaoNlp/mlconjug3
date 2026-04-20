from typing import Any, Dict, Optional
from textual.widgets import Static, Tree
from textual.app import ComposeResult


class ResultsTable(Static):
    """
    Type stub for ResultsTable widget.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def compose(self) -> ComposeResult: ...

    def _safe_form(self, value: Any) -> str: ...

    def clear(self) -> None: ...

    def _build_badge(self, mode: str, confidence: Optional[float]) -> str: ...

    def _normalize_form(self, verb: str, form: Any) -> str: ...

    def update_conjugation(
        self,
        verb: str,
        conjugation: Dict[str, Any],
        append: bool = False,
        confidence: Optional[float] = None,
        mode: str = "RULE",
    ) -> None: ...
