"""
Name normalization for HumanMint.

Core name parsing, capitalization normalization, and noise removal.
Builds on top of the nameparser library for robust name parsing.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Dict, Optional
from nameparser import HumanName


# US suffixes that should be recognized and extracted
US_SUFFIXES = {
    "jr",
    "sr",
    "ii",
    "iii",
    "iv",
    "v",
    "esq",
    "phd",
    "md",
    "dds",
    "dvm",
    "jd",
    "ma",
    "ms",
    "ba",
    "bs",
    "mba",
}

# Title prefixes to strip
TITLE_PREFIXES = {
    "mr",
    "mrs",
    "ms",
    "miss",
    "dr",
    "prof",
    "professor",
    "sir",
    "dame",
    "hon",
    "admiral",
    "rev",
    "reverend",
}

PLACEHOLDER_NAMES = {
    "unknown",
    "tbd",
    "n/a",
    "na",
    "n\\a",
    "staff",
    "occupant",
    "none",
}

_EMPTY_NAME: Dict[str, Optional[str]] = {
    "first": None,
    "middle": None,
    "last": None,
    "suffix": None,
    "full": None,
    "canonical": None,
    "is_valid": False,
}


def _strip_noise(raw: str) -> str:
    """
    Remove common noise from name strings.

    Removes:
    - HTML tags
    - Zero-width characters
    - Email addresses
    - Phone numbers
    - Parenthetical content (comments, status)
    - Excessive punctuation
    - Leading/trailing whitespace
    - Quote markers

    Args:
        raw: Raw name string.

    Returns:
        Cleaned name string.
    """
    if not raw:
        return ""

    # Remove invisible characters from copy/paste (ZWSP, BOM, etc.)
    raw = re.sub(r'[\u200b-\u200d\ufeff]', '', raw)

    # Strip simple HTML/markup tags that sometimes leak from CRM exports
    raw = re.sub(r"<[^>]+>", " ", raw)

    # Remove email addresses (anything that looks like user@domain)
    raw = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', raw)

    # Remove phone patterns (basic: digits with separators)
    raw = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', raw)
    # Remove short local numbers that sneak into names (e.g., 555-0202)
    raw = re.sub(r'\b\d{3}[-.]?\d{4}\b', '', raw)

    # Remove parenthetical content (notes, status, etc.)
    # But preserve some useful parens like "(Ret.)" as separate analysis
    raw = re.sub(r'\([^)]*\)', '', raw)

    # Normalize quoted nicknames by keeping content and stripping the quote marks
    raw = re.sub(r'[\"“”]', "'", raw)
    raw = re.sub(r"'([^']+)'", r"\1", raw)
    raw = re.sub(r"[’‘]([^’‘]+)[’‘]", r"\1", raw)

    # Remove excessive punctuation (multiple periods become single space)
    raw = re.sub(r'\.{2,}', '.', raw)

    # Strip leading/trailing whitespace
    raw = raw.strip()

    return raw


def _normalize_unicode(text: str) -> str:
    """
    Remove diacritics and normalize Unicode for US context.

    Converts non-ASCII characters to ASCII equivalents:
    - "Andr?a" ? "Andrea"
    - "Jos?" ? "Jose"
    - "L?pez?Mart?nez" ? "Lopez-Martinez" (? becomes -)
    - "Caf?" ? "Cafe"

    This is the default behavior for a US-focused library. Non-ASCII names
    are normalized to ASCII for consistency and database compatibility.

    Args:
        text: Text potentially containing Unicode/accented characters.

    Returns:
        Normalized text with diacritics removed and Unicode punctuation replaced.
    """
    if not text:
        return text

    # Decompose characters into base + combining marks (? ? e + ?)
    decomposed = unicodedata.normalize('NFKD', text)

    # Remove combining characters (the ?, `, ^, etc.)
    without_accents = ''.join(
        c for c in decomposed if not unicodedata.combining(c)
    )

    # Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        '\u2013': '-',    # en-dash ? hyphen
        '\u2014': '-',    # em-dash ? hyphen
        '\u2026': '...',  # ellipsis ? three dots
        '\u2018': "'",    # left single quote ? apostrophe
        '\u2019': "'",    # right single quote ? apostrophe
        '\u201c': '"',    # left double quote ? quote
        '\u201d': '"',    # right double quote ? quote
    }

    result = without_accents
    for unicode_char, ascii_char in replacements.items():
        result = result.replace(unicode_char, ascii_char)

    return result

def _normalize_capitalization(text: str) -> str:
    """
    Normalize capitalization in a name.

    Converts:
    - "JOHN SMITH" → "John Smith"
    - "joHN deLuca" → "John Deluca"
    - "mary-jane" → "Mary-Jane"

    Preserves:
    - Already-correct capitalization
    - Internal capitals (McSomething, O'Brien patterns)
    - Hyphenated names

    Args:
        text: Name or name part to capitalize.

    Returns:
        Properly capitalized text.
    """
    if not text:
        return ""

    # Handle hyphenated names (e.g., Mary-Jane, Johnson-Smith)
    if "-" in text:
        parts = text.split("-")
        return "-".join(_normalize_capitalization(p) for p in parts)

    # Handle Scottish/Irish prefixes (Mc, Mac, O')
    # These should preserve capital: McMillan, O'Brien
    if text.lower().startswith("mc") and len(text) > 2:
        return "Mc" + text[2].upper() + text[3:].lower()

    if text.lower().startswith("mac") and len(text) > 3:
        return "Mac" + text[3].upper() + text[4:].lower()

    if text.lower().startswith("o'") and len(text) > 2:
        return "O'" + text[2].upper() + text[3:].lower()

    # Handle standard capitalization
    return text.capitalize()


def _extract_middle_parts(middle: str) -> Optional[str]:
    """
    Clean and normalize middle names/initials.

    Handles:
    - "John Andrew Smith" → "John Andrew"
    - "J A Smith" → "J A"
    - "J. A. Smith" → "J A"
    - "J.A.P. Smith" → "J A P"

    Args:
        middle: Raw middle name string.

    Returns:
        Normalized middle name(s) or initials, or None if empty.
    """
    if not middle:
        return None

    # Remove periods and clean up
    middle = middle.replace(".", " ").strip()

    # Split on spaces and filter empty parts
    parts = [p.strip() for p in middle.split() if p.strip()]

    if not parts:
        return None

    # If parts are single letters, keep them as initials
    # Otherwise, capitalize normally
    normalized = []
    for part in parts:
        if len(part) == 1:
            normalized.append(part.upper())
        else:
            normalized.append(_normalize_capitalization(part))

    return " ".join(normalized) if normalized else None


def _detect_suffix(last: str) -> tuple[str, Optional[str]]:
    """
    Extract suffix from last name if present.

    Detects US suffixes like Jr, Sr, II, III, Esq, PhD, etc.

    Args:
        last: Last name string.

    Returns:
        Tuple of (last_name_without_suffix, suffix_or_none).
    """
    if not last:
        return last, None

    parts = last.split()

    # Check last word against known suffixes
    if parts and parts[-1].lower().rstrip(".") in US_SUFFIXES:
        suffix = parts[-1].rstrip(".")
        remaining_last = " ".join(parts[:-1])
        return remaining_last if remaining_last else "", suffix.lower()

    return last, None


def _normalize_hyphenated_last(last: str) -> str:
    """
    Handle hyphenated last names correctly.

    Ensures both parts are capitalized:
    - "mary-jane Smith" → "Mary-Jane"
    - "johnson-SMITH" → "Johnson-Smith"

    Args:
        last: Last name, possibly hyphenated.

    Returns:
        Normalized hyphenated last name.
    """
    if "-" not in last:
        return _normalize_capitalization(last)

    parts = last.split("-")
    return "-".join(_normalize_capitalization(p) for p in parts)


def _empty() -> Dict[str, Optional[str]]:
    """Return empty/invalid name result."""
    return _EMPTY_NAME.copy()


def normalize_name(raw: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Normalize a name into structured components.

    Parses full names and returns:
    - Individual components (first, middle, last, suffix)
    - Normalized capitalization
    - Canonical full name for deduplication

    Args:
        raw: Raw name string (e.g., "Mr. John Andrew Smith, Jr.").

    Returns:
        Dict with keys:
        - first: First name
        - middle: Middle name(s) or initials
        - last: Last name
        - suffix: Suffix (Jr, Sr, PhD, etc.)
        - full: Full name with suffix (e.g., "John Andrew Smith Jr")
        - canonical: Canonical form for matching (e.g., "john andrew smith jr")
        - is_valid: Whether parsing succeeded

    Examples:
        >>> normalize_name("Mr. John Andrew Smith, Jr.")
        {
            "first": "John",
            "middle": "Andrew",
            "last": "Smith",
            "suffix": "jr",
            "full": "John Andrew Smith Jr",
            "canonical": "john andrew smith jr",
            "is_valid": True
        }

        >>> normalize_name("JANE MARIE DOE")
        {
            "first": "Jane",
            "middle": "Marie",
            "last": "Doe",
            "suffix": None,
            "full": "Jane Marie Doe",
            "canonical": "jane marie doe",
            "is_valid": True
        }
    """
    if not raw or not isinstance(raw, str):
        return _empty()

    # Strip noise
    cleaned = _strip_noise(raw).strip()
    if not cleaned:
        return _empty()

    # Normalize Unicode (remove accents, convert special punctuation)
    cleaned = _normalize_unicode(cleaned)
    if not cleaned:
        return _empty()

    # Skip placeholder names
    if cleaned.lower() in PLACEHOLDER_NAMES:
        return _empty()

    result = _normalize_name_cached(cleaned)
    return result.copy()


@lru_cache(maxsize=4096)
def _normalize_name_cached(cleaned: str) -> Dict[str, Optional[str]]:
    """Cached core normalization to avoid re-parsing identical names."""
    parsed = HumanName(cleaned)

    # Extract components
    first = parsed.first.strip() if parsed.first else None
    middle = parsed.middle.strip() if parsed.middle else None
    last = parsed.last.strip() if parsed.last else None
    suffix = parsed.suffix.strip() if parsed.suffix else None

    # Validate: must have at least one name component
    # If only one component provided, treat as last name (single name support)
    if not first and not last:
        return _EMPTY_NAME

    # If only last name exists (no first), move it to first for single-name support
    if not first and last:
        first = last
        last = None

    # Normalize capitalization
    first = _normalize_capitalization(first)
    if last:
        last = _normalize_hyphenated_last(last)

    # Clean up middle names/initials
    middle = _extract_middle_parts(middle) if middle else None

    # Extract suffix from last name if not already detected by nameparser
    if not suffix:
        last, extracted_suffix = _detect_suffix(last)
        suffix = extracted_suffix

    # Normalize suffix
    if suffix:
        suffix = suffix.lower().rstrip(".")

    # Build canonical form (lowercase, no spaces around punctuation)
    canonical_parts = [first.lower()]
    if middle:
        canonical_parts.append(middle.lower())
    if last:
        canonical_parts.append(last.lower())
    if suffix:
        canonical_parts.append(suffix.lower())
    canonical = " ".join(canonical_parts)

    # Build full display name
    full_parts = [first]
    if middle:
        full_parts.append(middle)
    if last:
        full_parts.append(last)
    if suffix:
        full_parts.append(suffix.capitalize())
    full = " ".join(full_parts)

    return {
        "first": first,
        "middle": middle,
        "last": last,
        "suffix": suffix,
        "full": full,
        "canonical": canonical,
        "is_valid": True,
    }
