"""
Name normalization for HumanMint.

Core name parsing, capitalization normalization, and noise removal.
Builds on top of the nameparser library for robust name parsing.
"""

import re
from functools import lru_cache
from typing import Dict, Optional

from nameparser import HumanName

from humanmint.constants.names import PLACEHOLDER_NAMES, TITLE_PREFIXES, US_SUFFIXES
from humanmint.text_clean import normalize_unicode_ascii, strip_garbage

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
    - HTML/SQL/corruption markers
    - Zero-width characters
    - Email addresses
    - Phone numbers
    - Parenthetical content (comments, status)
    - Excessive punctuation
    - Leading/trailing whitespace
    - Quote markers
    """
    if not raw:
        return ""

    # Remove invisible characters from copy/paste (ZWSP, BOM, etc.)
    raw = re.sub(r"[\u200b-\u200d\ufeff]", "", raw)

    # Strip generic garbage (HTML, SQL comments, corruption markers)
    raw = strip_garbage(raw)

    # Remove email addresses (anything that looks like user@domain)
    raw = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "", raw)

    # Remove phone patterns (basic: digits with separators)
    raw = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "", raw)
    # Remove short local numbers that sneak into names (e.g., 555-0202)
    raw = re.sub(r"\b\d{3}[-.]?\d{4}\b", "", raw)

    # Remove parenthetical content (notes, status, etc.)
    raw = re.sub(r"\([^)]*\)", "", raw)

    # Normalize quotes and strip quoted nicknames while preserving content
    raw = raw.translate(
        str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "`": "'", "´": "'"})
    )
    raw = re.sub(r"'([^']+)'", r"\1", raw)

    # Remove excessive punctuation (multiple periods become single space)
    raw = re.sub(r"\.{2,}", ".", raw)

    # Remove trailing/embedded credentials (professional certs, degrees) not part of legal name
    raw = re.sub(
        r"(?:,|\s)+(?:PMP|CPA|SHRM-?CP|SHRM-?SCP|RN-?BC?|MPA|MPH|MBA|JD|PHD|PH\.?D|ED\.?D|EDD|ED\.?S|EDS|MD|M\.?D\.?|DO|DDS|DVM|PE|CISSP|LCSW)\b\.?",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    # Strip leading rank/title tokens that belong to job titles, not names
    raw = re.sub(
        r"^(battalion chief|chief|captain|capt|cpt|lieutenant|lt|sergeant|sgt|officer|marshal|commander)\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    return raw.strip()


def _strip_ranks_and_badges(text: str) -> str:
    """Remove common rank prefixes and badge/ID numbers that leak into name fields."""
    text = re.sub(
        r"\b(?:sgt|sergeant|capt|captain|cpt|lt|lieutenant|officer|ofc|deputy|det|detective|sheriff|chief|cpl|corporal|gov|governor|sen|senator|rep|representative)\.?\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"#\s*\d+\b", "", text)
    text = re.sub(r"\bbadge\s*\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bid\s*\d+\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,'-")


def _normalize_unicode(text: str) -> str:
    """Normalize accents and punctuation while preserving diacritics when possible."""
    if not text:
        return ""
    try:
        import ftfy  # type: ignore

        text = ftfy.fix_text(text)
    except Exception:
        pass
    return normalize_unicode_ascii(text, keep_accents=True)


def _strip_title_prefixes(text: str) -> str:
    """Remove leading honorifics/titles (Dr, Mr, Ms, etc.)."""
    if not text:
        return text
    tokens = [t for t in text.split() if t]
    while tokens and tokens[0].lower().strip(".,") in TITLE_PREFIXES:
        tokens = tokens[1:]
    return " ".join(tokens)


def _normalize_capitalization(text: str) -> str:
    """
    Normalize capitalization in a name.
    """
    if not text:
        return ""

    # Handle short prefix apostrophe names like D'Angelo, L'Oreal
    if re.match(r"^[A-Za-z]'[A-Za-z].*", text):
        head, tail = text.split("'", 1)
        return f"{head.upper()}'{tail.capitalize()}"

    # Handle hyphenated names (e.g., Mary-Jane, Johnson-Smith)
    if "-" in text:
        parts = text.split("-")
        return "-".join(_normalize_capitalization(p) for p in parts)

    # Handle Scottish/Irish prefixes (Mc, Mac, O')
    if text.lower().startswith("mc") and len(text) > 2:
        return "Mc" + text[2].upper() + text[3:].lower()

    if text.lower().startswith("o'") and len(text) > 2:
        return "O'" + text[2].upper() + text[3:].lower()

    return text.capitalize()


def _extract_middle_parts(middle: str) -> Optional[str]:
    """Clean and normalize middle names/initials."""
    if not middle:
        return None

    middle = middle.replace(".", " ").strip()
    parts = [p.strip() for p in middle.split() if p.strip()]

    if not parts:
        return None

    normalized = []
    for part in parts:
        if len(part) == 1:
            normalized.append(part.upper())
        else:
            normalized.append(_normalize_capitalization(part))

    return " ".join(normalized) if normalized else None


def _detect_suffix(last: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Extract suffix from last name if present."""
    if not last:
        return last, None

    parts = last.split()
    if parts and parts[-1].lower().rstrip(".") in US_SUFFIXES:
        suffix = parts[-1].rstrip(".")
        remaining_last = " ".join(parts[:-1])
        return (remaining_last if remaining_last else ""), suffix.lower()

    return last, None


def _normalize_hyphenated_last(last: str) -> str:
    """Handle hyphenated last names correctly."""
    if "-" not in last:
        return _normalize_capitalization(last)

    parts = last.split("-")
    return "-".join(_normalize_capitalization(p) for p in parts)


def _empty() -> Dict[str, Optional[str]]:
    """Return empty/invalid name result."""
    return _EMPTY_NAME.copy()


def _validate_name_quality(
    first: Optional[str], last: Optional[str], middle: Optional[str]
) -> bool:
    """
    Validate name quality based on component presence and content.

    A name is considered valid if:
    - Has both first AND last names with at least 2 chars each and alphabetic content
    - Has only first name with at least 2 chars and alphabetic content
    - Has only last name (less common but acceptable)

    A name is invalid if:
    - Single character components
    - No alphabetic characters
    - Only first OR last is a single letter/number

    Args:
        first: First name component
        last: Last name component
        middle: Middle name component (not required)

    Returns:
        True if name passes validation, False otherwise
    """
    # Both first and last names present - strict validation
    if first and last:
        first_valid = len(first) >= 2 and any(c.isalpha() for c in first)
        last_valid = len(last) >= 2 and any(c.isalpha() for c in last)
        return first_valid and last_valid

    # Only first name - must be substantial
    if first and not last:
        return len(first) >= 2 and any(c.isalpha() for c in first)

    # Only last name - less common but acceptable if substantial
    if last and not first:
        return len(last) >= 2 and any(c.isalpha() for c in last)

    # No first or last name
    return False


def normalize_name(raw: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Normalize a name into structured components.
    """
    if not raw or not isinstance(raw, str):
        return _empty()

    cleaned = _strip_noise(raw).strip()
    if not cleaned:
        return _empty()

    cleaned = _normalize_unicode(cleaned)
    if not cleaned:
        return _empty()

    cleaned = _strip_title_prefixes(cleaned)
    cleaned = _strip_ranks_and_badges(cleaned)
    if not cleaned:
        return _empty()

    if cleaned.lower() in PLACEHOLDER_NAMES:
        return _empty()

    result = _normalize_name_cached(cleaned)
    return result.copy()


@lru_cache(maxsize=4096)
def _normalize_name_cached(cleaned: str) -> Dict[str, Optional[str]]:
    """
    Cached core normalization to avoid re-parsing identical names.

    This function uses @lru_cache(maxsize=4096) to cache results of name parsing.
    For large batches of names with duplicates, this significantly improves performance.

    To clear the cache if memory is a concern:
        >>> _normalize_name_cached.cache_clear()

    To check cache statistics:
        >>> _normalize_name_cached.cache_info()
    """
    tokens_original = cleaned.split()
    parsed = HumanName(cleaned)

    first = parsed.first.strip() if parsed.first else None
    middle = parsed.middle.strip() if parsed.middle else None
    last = parsed.last.strip() if parsed.last else None
    suffix = parsed.suffix.strip() if parsed.suffix else None

    if not first and not last:
        return _EMPTY_NAME

    if not first and last:
        first = tokens_original[0] if tokens_original else last
        last = tokens_original[-1] if len(tokens_original) > 1 else None

    # If still no last name but first contains a hyphen, split into first/last parts
    if first and not last and "-" in first:
        part_first, part_last = first.split("-", 1)
        first = _normalize_capitalization(part_first)
        last = _normalize_capitalization(part_last)

    first = _normalize_capitalization(first)
    if last:
        last = _normalize_hyphenated_last(last)

    middle = _extract_middle_parts(middle) if middle else None

    if not suffix:
        last, extracted_suffix = _detect_suffix(last)
        suffix = extracted_suffix

    if suffix:
        suffix = suffix.lower().rstrip(".")

    canonical_parts = [first.lower()]
    if middle:
        canonical_parts.append(middle.lower())
    if last:
        canonical_parts.append(last.lower())
    if suffix:
        canonical_parts.append(suffix.lower())
    canonical = " ".join(canonical_parts)

    full_parts = [first]
    if middle:
        full_parts.append(middle)
    if last:
        full_parts.append(last)
    if suffix:
        full_parts.append(suffix.capitalize())
    full = " ".join(full_parts)

    # Validate name quality
    is_valid = _validate_name_quality(first, last, middle)

    return {
        "first": first,
        "middle": middle,
        "last": last,
        "suffix": suffix,
        "full": full,
        "canonical": canonical,
        "is_valid": is_valid,
    }
