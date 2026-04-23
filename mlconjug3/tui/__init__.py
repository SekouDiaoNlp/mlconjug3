"""
mlconjug3 TUI — Linguistic Laboratory
A beautiful, accessible, educational terminal interface for
verb conjugation and morphological analysis.

Supports: fr, en, es, it, pt, ro
Requires: textual >= 0.47, rich >= 13.0, mlconjug3 >= 3.9
"""
from __future__ import annotations

# Lazy import to avoid pulling in textual at package import time.
# Call run() or import MLConjug3App explicitly when you need the TUI.


def run() -> None:
    """Launch the mlconjug3 TUI."""
    from .app import MLConjug3App
    MLConjug3App().run()


__all__ = ["run"]
