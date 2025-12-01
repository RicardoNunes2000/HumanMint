"""
Shared text cleaning utilities for HumanMint.

These helpers provide lightweight, cross-domain normalization that can be
applied before field-specific logic (names, titles, departments, emails).
"""

from __future__ import annotations

import re
import unicodedata

_CORRUPTION_MARKERS = r"(?:TEMP|CORRUPTED|TEST|DEBUG|ADMIN|USER)"
_LEADING_CODE_PATTERN = re.compile(r"^[0-9]{3,}[\s\-]*")
_TRAILING_CODE_PATTERN = re.compile(r"\s+[0-9]{3,}$")


def extract_tokens(text: str, exclude: set[str] | None = None) -> set[str]:
    """
    Extract alphanumeric tokens from text.

    Splits on whitespace, filters to alphanumeric-only tokens, and optionally
    excludes a specific set of tokens. Much faster than regex-based extraction.

    Args:
        text: Text to extract tokens from.
        exclude: Optional set of tokens to exclude (e.g., generic terms).

    Returns:
        Set of alphanumeric tokens.

    Example:
        >>> extract_tokens("Public Works Department")
        {'public', 'works', 'department'}
        >>> extract_tokens("IT Support", exclude={'it', 'support'})
        set()
    """
    tokens = set()
    for token in text.split():
        # Extract only alphanumeric characters from each word
        clean = ''.join(c for c in token if c.isalnum())
        if clean:
            tokens.add(clean)

    if exclude:
        tokens = {t for t in tokens if t not in exclude}

    return tokens


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


def remove_parentheticals(text: str) -> str:
    """
    Remove all parenthetical segments from text, treating them as metadata/noise.

    Matches patterns like:
    - (Finance), (Main Office), (HQ)
    - Any text within parentheses

    Args:
        text: Input string potentially containing parenthetical content.

    Returns:
        str: Text with parenthetical segments removed.

    Example:
        >>> remove_parentheticals("Director (Finance)")
        "Director"
        >>> remove_parentheticals("Officer (Downtown)")
        "Officer"
    """
    return re.sub(r"\([^)]*\)", " ", text)


def strip_codes_and_ids(text: str, strip_codes: str = "both") -> str:
    """
    Remove leading and/or trailing numeric codes and ID numbers from text.

    Useful for cleaning department names and job titles that may have internal
    database codes prepended or appended.

    Matches patterns like:
    - 000171 - Supervisor (leading code with dash)
    - 4591405 Public Works (leading code with space)
    - Supervisor 010100 (trailing code)
    - 010100 - Manager - 514134 (both leading and trailing)

    Args:
        text: Input string potentially containing numeric codes.
        strip_codes: Which codes to remove. Options:
            - "both" (default): Remove leading and trailing codes
            - "leading": Remove only leading codes (e.g., "000171 - ")
            - "trailing": Remove only trailing codes (e.g., " 514134")
            - "none": Don't remove any codes

    Returns:
        str: Text with codes removed based on strip_codes setting.

    Example:
        >>> strip_codes_and_ids("4591405 Public Works 514134")
        "Public Works"
        >>> strip_codes_and_ids("001 - Police Officer", strip_codes="leading")
        "Police Officer"
        >>> strip_codes_and_ids("Manager 299", strip_codes="trailing")
        "Manager"
    """
    if strip_codes == "both":
        text = _LEADING_CODE_PATTERN.sub("", text)
        text = _TRAILING_CODE_PATTERN.sub("", text)
    elif strip_codes == "leading":
        text = _LEADING_CODE_PATTERN.sub("", text)
    elif strip_codes == "trailing":
        text = _TRAILING_CODE_PATTERN.sub("", text)
    # strip_codes == "none" does nothing
    return text
