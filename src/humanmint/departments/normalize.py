"""
Department name normalization for HumanMint.

Core normalization functions to clean and standardize department names by
removing noise, extra whitespace, and common artifacts.
"""

import re
from functools import lru_cache


_PHONE_PATTERN = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
_EXT_PATTERN = re.compile(r"\b(?:ext|x|extension)[\s.]*\d+\b", flags=re.IGNORECASE)
_CODE_PATTERN = re.compile(r"^[0-9]{3,}[\s\-]*")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_SYMBOL_WRAPPER_PATTERN = re.compile(r"[#|]+")
_SEPARATOR_PATTERN = re.compile(r"-+")
_SLASH_PATTERN = re.compile(r"\s*/\s*")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_CONTACT_PATTERNS = (
    r"\breach\s+(?:me|us)\s+at\b",
    r"\bcontact\s+(?:me|us)\b",
    r"\bemail\b",
    r"\be-mail\b",
    r"\bphone\b",
    r"\btel\b",
    r"\bcell\b",
)


def _strip_html(text: str) -> str:
    """Remove simple HTML tags that leak into free-text fields."""
    return _HTML_TAG_PATTERN.sub(" ", text)


def _remove_phone_numbers(text: str) -> str:
    """
    Remove phone numbers and extensions from text.

    Matches patterns like:
    - 850-123-1234
    - (850) 123-1234
    - ext 200, x200, extension 200
    - 850.123.1234

    Args:
        text: Input string potentially containing phone numbers.

    Returns:
        str: Text with phone numbers and extensions removed.
    """
    # Remove various phone formats
    text = _PHONE_PATTERN.sub('', text)
    # Remove extensions (ext, x, extension)
    text = _EXT_PATTERN.sub('', text)
    return text


def _remove_emails(text: str) -> str:
    """Strip email addresses embedded inside department values."""
    return _EMAIL_PATTERN.sub('', text)


def _strip_symbol_wrappers(text: str) -> str:
    """Replace noisy wrapper symbols (e.g., ###CODE###) with spaces."""
    return _SYMBOL_WRAPPER_PATTERN.sub(' ', text)


def _normalize_separators(text: str) -> str:
    """Turn common separators (----) into single spaces while keeping slashes."""
    text = _SLASH_PATTERN.sub(" / ", text)
    return _SEPARATOR_PATTERN.sub(' ', text)


def _remove_codes_and_ids(text: str) -> str:
    """
    Remove department codes and ID numbers.

    Matches patterns like:
    - 000171 - Supervisor
    - 010100 - Administration
    - [any number with leading zeros or dashes]

    Args:
        text: Input string potentially containing codes.

    Returns:
        str: Text with codes removed.
    """
    # Remove leading numeric codes with dashes (e.g., "000171 - ", "010100 - ")
    return _CODE_PATTERN.sub('', text)


def _remove_contact_phrases(text: str) -> str:
    """
    Drop trailing contact directives like 'reach me at' or 'call'.

    These phrases often show up when phone/email data is accidentally
    stored in the department column.
    """
    lowered = text.lower()
    for pattern in _CONTACT_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            text = text[:match.start()]
            lowered = text.lower()
    return text


def _remove_extra_whitespace(text: str) -> str:
    """
    Normalize whitespace and remove leading/trailing spaces.

    Args:
        text: Input string with potential whitespace issues.

    Returns:
        str: Text with normalized whitespace.
    """
    # Trim obvious separator noise that can be left behind after stripping
    text = text.strip(" -_,.;:")
    # Replace multiple spaces with single space
    text = _WHITESPACE_PATTERN.sub(' ', text)
    return text.strip(" -_,.;:")


@lru_cache(maxsize=4096)
def normalize_department(raw_dept: str) -> str:
    """
    Normalize a raw department name by removing noise and standardizing format.

    Removes:
    - Phone numbers and extensions (e.g., "850-123-1234 ext 200")
    - Department codes (e.g., "000171 - ", "010100 - ")
    - Extra whitespace
    - Non-alphanumeric characters beyond ampersands and hyphens

    Example:
        >>> normalize_department("000171 - Supervisor 850-123-1234 ext 200")
        "Supervisor"
        >>> normalize_department("Public Works 850-123-1234")
        "Public Works"
        >>> normalize_department("  City  Clerk  ")
        "City Clerk"

    Args:
        raw_dept: Raw department name string.

    Returns:
        str: Normalized department name in title case.

    Raises:
        ValueError: If the input is empty after normalization.
    """
    if not raw_dept:
        raise ValueError("Department name cannot be empty")

    # Apply normalization steps in sequence
    text = _strip_html(raw_dept)
    text = _remove_phone_numbers(text)
    text = _remove_emails(text)
    text = _strip_symbol_wrappers(text)
    text = _normalize_separators(text)
    text = _remove_contact_phrases(text)
    text = _remove_codes_and_ids(text)
    text = _remove_extra_whitespace(text)

    if not text:
        raise ValueError(f"Department name became empty after normalization: '{raw_dept}'")

    # Title case for consistency
    text = text.title()

    return text
