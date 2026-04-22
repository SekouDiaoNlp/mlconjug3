"""
options.py

Shared option constants for CLI and TUI interfaces.

Attributes
----------
LANGUAGE_OPTIONS : tuple[tuple[str, str], ...]
    Human label + language code pairs used by interface selectors.
SUBJECT_OPTIONS : tuple[tuple[str, str], ...]
    Human label + subject style pairs for conjugation output.
EXPORT_FORMATS : set[str]
    Allowed output format identifiers for CLI export.
"""

LANGUAGE_OPTIONS = (
    ("French", "fr"),
    ("English", "en"),
    ("Spanish", "es"),
    ("Italian", "it"),
    ("Portuguese", "pt"),
    ("Romanian", "ro"),
)

SUBJECT_OPTIONS = (
    ("Abbrev", "abbrev"),
    ("Pronoun", "pronoun"),
)

EXPORT_FORMATS = {"json", "csv"}
