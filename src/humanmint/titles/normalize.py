"""
Job title normalization for HumanMint.

Core normalization functions to clean and standardize job titles by
removing noise, extra whitespace, and common artifacts.
"""

import re
from functools import lru_cache

from humanmint.constants.titles import (
    PRESERVE_ABBREVIATIONS,
    STOPWORDS,
    TITLE_ABBREVIATIONS,
)
from humanmint.text_clean import normalize_unicode_ascii, strip_garbage


def _strip_garbage(text: str) -> str:
    """Remove obvious non-title noise (HTML, SQL comments, corruption markers)."""
    return strip_garbage(text)


def _expand_abbreviations(text: str) -> str:
    """Expand common job title abbreviations."""
    parts = []
    for token in text.split():
        # Strip trailing periods (e.g., "Dir." -> "dir")
        clean_token = token.rstrip(".").lower()
        if clean_token in PRESERVE_ABBREVIATIONS:
            parts.append(token.rstrip("."))
        elif clean_token in TITLE_ABBREVIATIONS:
            expanded = TITLE_ABBREVIATIONS[clean_token]
            # Preserve common shorthand like "ops" alongside expansion
            if clean_token == "ops":
                parts.append(f"{expanded} ops")
            else:
                parts.append(expanded)
        else:
            parts.append(token)
    return " ".join(parts)


def _remove_name_prefixes(text: str) -> str:
    """
    Remove common name prefixes, person names, and credentials from text.

    Matches patterns like:
    - Dr., Mr., Mrs., Ms., Miss, Prof., Rev.
    - "FirstName LastName," patterns (e.g., "John Smith,")
    - PhD, MD, Esq., etc.

    Args:
        text: Input string potentially containing name prefixes or full names.

    Returns:
        str: Text with name prefixes and person names removed.
    """
    # Remove common salutations and credentials at the beginning
    text = re.sub(
        r"\b(?:Dr|Mr|Mrs|Ms|Miss|Prof|Professor|Rev|Reverend|Sir|Madam|Esq)\.?\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove "FirstName LastName," pattern (e.g., "John Smith," or "Jane Doe,")
    # Matches: word(s) followed by comma
    text = re.sub(r"^[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s*,\s*", "", text)
    # Remove trailing credentials like PhD, MD, etc.
    text = re.sub(
        r",?\s*(?:PhD|MD|DDS|DVM|Esq|MBA|MA|BS|BA|CISSP|PMP|RN|LPN|CPA)\.?$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _remove_codes_and_ids(text: str) -> str:
    """
    Remove job codes and ID numbers.

    Matches patterns like:
    - 0001 - Director
    - 001234 - Manager
    - [any number with leading zeros or dashes]

    Args:
        text: Input string potentially containing codes.

    Returns:
        str: Text with codes removed.
    """
    # Remove leading numeric codes with dashes (e.g., "0001 - ", "001234 - ")
    text = re.sub(r"^[0-9]{3,}[\s\-]*", "", text)
    return text


def _remove_extra_whitespace(text: str) -> str:
    """
    Normalize whitespace and remove leading/trailing spaces.

    Args:
        text: Input string with potential whitespace issues.

    Returns:
        str: Text with normalized whitespace.
    """
    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    # Strip leading and trailing whitespace
    text = text.strip()
    return text


def _remove_parenthetical_info(text: str) -> str:
    """
    Remove parenthetical information (e.g., department, location).

    Matches patterns like:
    - Director (Finance)
    - Manager (Main Office)
    - Officer - Downtown

    Args:
        text: Input string with potential parenthetical content.

    Returns:
        str: Text with parenthetical info removed.
    """
    # Remove content in parentheses
    text = re.sub(r"\s*\([^)]*\)", "", text)
    # Remove content after dashes (for location/department info)
    text = re.sub(
        r"\s*-\s*(?:Main|Downtown|Downtown Office|Main Office|HQ|Headquarters)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _normalize_separators(text: str) -> str:
    """Normalize common separators like slashes and ampersands."""
    # Keep slashes as explicit separators, collapse long dash runs to spaces
    text = re.sub(r"\s*/\s*", " / ", text)
    text = re.sub(r"[-\u2013\u2014]+", " ", text)
    text = re.sub(r"\s*&\s*", " & ", text)
    return text


def _strip_trailing_dept_tokens(text: str) -> str:
    """Remove trailing department acronyms (e.g., PW, DPW, HR) that leak into titles."""
    tokens = text.split()
    if not tokens:
        return text
    trailing = tokens[-1].lower().strip(".")
    noisy = {"dept"}
    if trailing in noisy and len(tokens) > 1:
        tokens = tokens[:-1]
    return " ".join(tokens)


def _smart_title_case(text: str, preserve_caps: set[str]) -> str:
    """
    Title-case while keeping stopwords lowercase and short abbreviations uppercase.
    """
    parts = []
    for raw_token in text.split():
        token = raw_token
        suffix = ""
        if token.endswith("."):
            token = token.rstrip(".")
            suffix = "."

        base_upper = token.upper()
        base_lower = token.lower()

        if base_upper in preserve_caps:
            parts.append(base_upper + suffix)
            continue

        if base_lower in STOPWORDS:
            parts.append(base_lower + suffix)
            continue

        parts.append(token.capitalize() + suffix)

    return " ".join(parts)


@lru_cache(maxsize=4096)
def normalize_title(raw_title: str) -> str:
    """
    Normalize a raw job title by removing noise and standardizing format.

    This function uses @lru_cache(maxsize=4096) to cache normalization results.
    For batches with repeated job titles (common in organizations), caching avoids
    redundant regex processing.

    To clear the cache if memory is a concern:
        >>> normalize_title.cache_clear()

    To check cache statistics:
        >>> normalize_title.cache_info()

    Removes:
    - Name prefixes (e.g., "Dr.", "Mr.")
    - Job codes (e.g., "0001 - ")
    - Parenthetical info (e.g., "(Finance)", "(Main Office)")
    - Extra whitespace

    Example:
        >>> normalize_title("Dr. John Smith, CEO")
        "CEO"
        >>> normalize_title("0001 - Director (Finance)")
        "Director"
        >>> normalize_title("  Senior  Manager  ")
        "Senior Manager"

    Args:
        raw_title: Raw job title string.

    Returns:
        str: Normalized job title in title case.

    Raises:
        ValueError: If the input is empty or not a string.
    """
    if not isinstance(raw_title, str):
        raise ValueError(f"Job title must be a string, got {type(raw_title).__name__}")

    if not raw_title:
        raise ValueError("Job title cannot be empty")

    # Apply normalization steps in sequence
    text = _strip_garbage(raw_title)
    text = _remove_name_prefixes(text)
    text = _remove_codes_and_ids(text)
    text = _normalize_separators(text)
    text = _remove_parenthetical_info(text)
    text = _expand_abbreviations(text)
    text = _strip_trailing_dept_tokens(text)
    text = _remove_extra_whitespace(text)

    # Normalize Unicode accents to ASCII
    text = normalize_unicode_ascii(text)

    # Remember abbreviations that were originally uppercase (e.g., IT, PW, HR)
    preserve_caps = {match.group(0) for match in re.finditer(r"\b[A-Z]{2,4}\b", text)}

    if not text:
        raise ValueError(f"Job title became empty after normalization: '{raw_title}'")

    # Title case for consistency, preserving stopwords/abbreviations
    text = _smart_title_case(text, preserve_caps)

    return text
