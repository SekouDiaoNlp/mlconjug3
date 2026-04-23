#!/usr/bin/env python3
"""
mlconjug3-tui — Command-line entry point.

Usage:
    python -m mlconjug3.tui
    python -m mlconjug3.tui --language fr
    python -m mlconjug3.tui --mode research
    python -m mlconjug3.tui --verb être

Options:
    --language LANG   Starting language: fr|en|es|it|pt|ro  (default: fr)
    --mode MODE       Starting mode: simple|learner|research (default: simple)
    --verb VERB       Pre-load this verb on launch
    --high-contrast   Start in high-contrast mode
    --light           Start in light theme
    --no-motion       Start with reduced motion
    --help            Show this help
"""
from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mlconjug3-tui",
        description="mlconjug3 TUI — Linguistic Laboratory",
    )
    parser.add_argument(
        "--language", "-l", default=None,
        choices=["fr", "en", "es", "it", "pt", "ro"],
        help="Starting language",
    )
    parser.add_argument(
        "--mode", "-m", default=None,
        choices=["simple", "learner", "research"],
        help="Starting mode",
    )
    parser.add_argument("--verb", "-v", default=None, help="Pre-load this verb")
    parser.add_argument("--high-contrast", action="store_true",
                        help="Start in high-contrast mode")
    parser.add_argument("--light", action="store_true", help="Start in light theme")
    parser.add_argument("--no-motion", action="store_true",
                        help="Start with reduced motion")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    from mlconjug3.tui.state import UIPreferences
    from mlconjug3.tui.app import MLConjug3App

    prefs = UIPreferences.load()

    if args.high_contrast:
        prefs.theme = "high_contrast"
    elif args.light:
        prefs.theme = "light"
    if args.no_motion:
        prefs.reduced_motion = True
    if args.language:
        prefs.default_language = args.language
    if args.mode:
        prefs.default_mode = args.mode

    app = MLConjug3App()
    app.prefs = prefs
    app.state.language = prefs.default_language
    app.state.mode = prefs.default_mode

    if args.verb:
        app.state.verb = args.verb

    app.run()


if __name__ == "__main__":
    main()
