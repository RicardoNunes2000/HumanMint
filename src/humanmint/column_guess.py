"""Shared column guessing utilities for pandas accessor and CLI."""

from __future__ import annotations

from typing import Iterable, Optional

# Common column name guesses for heuristic detection
COLUMN_GUESSES = {
    "email": ["email", "e-mail", "mail", "contact_email", "work_email"],
    "phone": ["phone", "cell", "mobile", "fax", "contact_phone", "telephone"],
    "name": ["name", "full_name", "contact_name", "person", "employee"],
    "department": ["dept", "department", "division", "bureau", "team"],
    "title": ["title", "job_title", "position", "role"],
}


def guess_column(
    columns: Iterable[str], explicit: Optional[str], guesses: list[str], allowed: Optional[set[str]] = None
) -> Optional[str]:
    """Return explicit column if provided, otherwise first heuristic match."""
    if explicit:
        return explicit
    for col in columns:
        if allowed and col not in allowed:
            continue
        lower = col.lower()
        if any(guess in lower for guess in guesses):
            return col
    return None
