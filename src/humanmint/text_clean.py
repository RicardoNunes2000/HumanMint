"""
Shared text cleaning utilities for HumanMint.

These helpers provide lightweight, cross-domain normalization that can be
applied before field-specific logic (names, titles, departments, emails).
"""

from __future__ import annotations

import re
import unicodedata

_CORRUPTION_MARKERS = r"(?:TEMP|CORRUPTED|TEST|DEBUG|ADMIN|USER)"


def strip_garbage(text: str) -> str:
    """Remove obvious non-field noise such as HTML, SQL comments, corruption markers, and semicolon tails."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"--.*?(?:\n|$)", " ", text)
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r";.*", " ", text)
    text = re.sub(rf"^#+\s*{_CORRUPTION_MARKERS}\s*#+\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(rf"^\s*\[{_CORRUPTION_MARKERS}\]\s*", "", text, flags=re.IGNORECASE)
    return text


def normalize_unicode_ascii(text: str, keep_accents: bool = False) -> str:
    """
    Normalize Unicode text to ASCII-friendly form by stripping accents and harmonizing punctuation.

    Args:
        text: Input string.
        keep_accents: If True, preserve diacritics (no combining-character strip).
    """
    if not text:
        return text

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    decomposed = unicodedata.normalize("NFKD", text)
    if keep_accents:
        return unicodedata.normalize("NFC", decomposed)
    return "".join(c for c in decomposed if not unicodedata.combining(c))
