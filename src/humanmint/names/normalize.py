"""
Name normalization for HumanMint.

Core name parsing, capitalization normalization, and noise removal.
Builds on top of the nameparser library for robust name parsing.
"""

import html
import re
from functools import lru_cache
from typing import Dict, Optional

from nameparser import HumanName

from humanmint.constants.names import (
    CORPORATE_TERMS,
    CREDENTIAL_SUFFIXES,
    PLACEHOLDER_NAMES,
    ROMAN_NUMERALS,
    TITLE_PREFIXES,
    US_SUFFIXES,
)
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


def _fix_common_ocr_errors(text: str) -> str:
    """Correct common digit-as-letter OCR errors within alphabetic words."""
    def _replace(match: re.Match[str]) -> str:
        word = match.group(0)
        if not re.search(r"[A-Za-z]", word):
            return word
        return word.replace("0", "o")

    return re.sub(r"\w+", _replace, text)


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

    # Decode HTML entities and normalize non-breaking spaces up front
    raw = html.unescape(raw)
    raw = raw.replace("\u00a0", " ")
    raw = _fix_common_ocr_errors(raw)

    # Strip leading list numbering/bullets (e.g., "1. Alice", "12) Bob")
    raw = re.sub(r"^\s*\d+[\.\)]\s*", "", raw)

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

    # If string contains "c/o" or "care of", keep the portion after it
    care_of_match = re.search(r"\b(?:c/o|care of)\b", raw, flags=re.IGNORECASE)
    if care_of_match:
        remainder = raw[care_of_match.end() :].strip(" ,.-")
        raw = remainder or raw

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
        r"(?:,|\s)+(?:PMP|CPA|SHRM-?CP|SHRM-?SCP|RN-?BC?|MPA|MPH|MBA|JD|PHD|PH\.?D|ED\.?D|EDD|ED\.?S|EDS|MD|M\.?D\.?|DO|DDS|DVM|PE|CISSP|LCSW|ESQ|ESQUIRE)\b\.?",
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

    # Strip leading/trailing stray punctuation/brackets left by SQL injection/artifacts
    raw = re.sub(r"^[\s\"'\)\(\[\]]+", "", raw)
    raw = re.sub(r"[\s\"'\)\(\[\];:]+$", "", raw)
    raw = re.sub(r"[()'\"]+$", "", raw)

    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _strip_ranks_and_badges(text: str) -> str:
    """Remove common rank prefixes and badge/ID numbers that leak into name fields."""
    text = re.sub(
        r"\b(?:sgt|sergeant|capt|captain|cpt|lt|lieutenant|officer|ofc|deputy|det|detective|sheriff|chief|cpl|corporal|gov|governor|sen|senator|rep|representative|council\s*member|councilmember|councilman|councilwoman|council)\.?\b",
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
    # Preserve accents for accurate name rendering
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
    if not parts:
        return last, None

    suffix_candidate = parts[-1].lower().rstrip(".")
    remaining_last = " ".join(parts[:-1])

    # Professional/credential suffixes are stripped out of standardized names
    if suffix_candidate in CREDENTIAL_SUFFIXES:
        return (remaining_last if remaining_last else ""), None

    if suffix_candidate in US_SUFFIXES:
        return (remaining_last if remaining_last else ""), suffix_candidate

    return last, None


def _looks_like_corporate(text: str) -> bool:
    """Heuristic: detect corporate indicators in the string."""
    if not text:
        return False

    text_lower = text.lower()
    for term in CORPORATE_TERMS:
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, text_lower):
            return True
    return False


def _select_best_segment(text: str) -> str:
    """
    When delimiters are present, pick the segment most likely to be the person's name.
    Handles formats like "Title - Last, First" or "Dept | Smith, Jane".
    """
    if not text:
        return text

    if not re.search(r"[|:]|- ", text):
        return text

    segments = [
        seg.strip(" ,")
        for seg in re.split(r"\s*[|:]\s+|-\s+", text)
        if seg and seg.strip(" ,")
    ]
    if not segments:
        return text

    best_seg = segments[0]
    best_score = -10
    for seg in segments:
        score = 0
        tokens = [t for t in seg.split() if t]
        if "," in seg:
            score += 3
        if len(tokens) >= 2:
            score += 2
        if len(tokens) >= 3:
            score += 1
        if _looks_like_corporate(seg):
            score -= 3
        if re.match(r"^[A-Za-z]+,\s*[A-Za-z]+", seg):
            score += 2
        if score > best_score:
            best_seg = seg
            best_score = score

    return best_seg


def _normalize_hyphenated_last(last: str) -> str:
    """Handle hyphenated last names correctly."""
    if "-" not in last:
        return _normalize_capitalization(last)

    parts = last.split("-")
    return "-".join(_normalize_capitalization(p) for p in parts)


def _empty() -> Dict[str, Optional[str]]:
    """Return empty/invalid name result."""
    return _EMPTY_NAME.copy()


def _dedupe_trailing_duplicate_first(cleaned: str) -> str:
    """
    Drop trailing duplicated first names like "Jane Doe, Jane".

    These often come from copy/paste or CSV join issues. The pattern we want to fix is:
    "<first> <last>, <first>" where the comma section is just a repeat of the leading first token.
    """
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    if len(parts) >= 2:
        left_first = parts[0].split()[0].lower() if parts[0] else ""
        trailing = parts[-1].lower()
        if left_first and trailing == left_first:
            # Remove the duplicated trailing first token
            return ", ".join(parts[:-1])
    return cleaned


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

    cleaned = _select_best_segment(cleaned)
    cleaned = _dedupe_trailing_duplicate_first(cleaned)

    if _looks_like_corporate(cleaned):
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

    suffix_tokens = []
    if parsed.suffix:
        suffix_tokens = [tok for tok in re.split("[\\s,]+", parsed.suffix) if tok]
    suffix = None
    for token in suffix_tokens:
        candidate = token.lower().rstrip(".")
        if candidate in CREDENTIAL_SUFFIXES:
            continue
        suffix = candidate
        break

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
        # Use uppercase for roman numerals, capitalize for others
        suffix_display = ROMAN_NUMERALS.get(suffix, suffix.capitalize())
        full_parts.append(suffix_display)
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
