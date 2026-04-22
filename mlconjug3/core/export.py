"""
mlconjug3.core.export

Export helpers shared by CLI and TUI interfaces.

The TUI needs lightweight export without coupling UI widgets to file formats.
This module provides deterministic serialization of conjugation tables.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


ConjugationTable = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ExportPayload:
    """
    Structured export payload for a conjugation result.

    Attributes
    ----------
    verb:
        Verb being exported.
    language:
        Language code.
    subject:
        Subject display mode.
    table:
        Conjugation table (mood -> tense -> forms).
    """

    verb: str
    language: str
    subject: str
    table: ConjugationTable


def to_json(payload: ExportPayload) -> str:
    """
    Serialize payload to JSON.

    Parameters
    ----------
    payload:
        Export payload to serialize.

    Returns
    -------
    str
        JSON string.
    """

    obj = {
        "verb": payload.verb,
        "language": payload.language,
        "subject": payload.subject,
        "conjugation": payload.table,
    }
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def to_text(payload: ExportPayload) -> str:
    """
    Serialize payload to a human-readable text block.

    Parameters
    ----------
    payload:
        Export payload.

    Returns
    -------
    str
        Plain text rendering.
    """

    lines: list[str] = []
    lines.append(f"{payload.verb} [{payload.language}] ({payload.subject})")
    for mood, tenses in payload.table.items():
        lines.append("")
        lines.append(str(mood).upper())
        if isinstance(tenses, Mapping):
            for tense, persons in tenses.items():
                lines.append(f"  {str(tense)}")
                if isinstance(persons, Mapping):
                    for person, form in persons.items():
                        lines.append(f"    {person}: {form}")
                else:
                    lines.append(f"    {persons}")
        else:
            lines.append(f"  {tenses}")
    lines.append("")
    return "\n".join(lines)
