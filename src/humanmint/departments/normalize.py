"""
Department name normalization for HumanMint.

Core normalization functions to clean and standardize department names by
removing noise, extra whitespace, and common artifacts.
"""

import re
from functools import lru_cache

from humanmint.text_clean import normalize_unicode_ascii, strip_garbage

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
_APOSTROPHE_PATTERN = re.compile(r"[’‘]")
_ACRONYMS = {"IT", "HR", "GIS", "OEM", "DPW", "PW"}
_DEPT_META_PATTERN = re.compile(r"\s*\((?:ref#?|id|ticket)\s*[^)]*\)$", re.IGNORECASE)
_ABBREVIATIONS = {
    "strt": "street",
    "st": "street",
    "rd": "road",
    "ave": "avenue",
    "blvd": "boulevard",
    "hwy": "highway",
    "dept": "department",
    "dpt": "department",
    "div": "division",
    "sec": "section",
    "dist": "district",
    "ctr": "center",
    "ctrs": "centers",
    "comm": "commission",
    "commn": "commission",
    "maint": "maintenance",
    "mnt": "maintenance",
    "ops": "operations",
    "op": "operations",
    "svc": "service",
    "svcs": "services",
    "svs": "services",
    "mgmt": "management",
    "mgmt.": "management",
    "admin": "administration",
    "adm": "administration",
    "assist": "assistant",
    "asst": "assistant",
    "ast": "assistant",
    "env": "environmental",
    "envr": "environmental",
    "pw": "public works",
    "pd": "police department",
    "fd": "fire department",
    "hr": "human resources",
    "it": "information technology",
    "trans": "transportation",
    "transp": "transportation",
    "trns": "transportation",
    "traf": "traffic",
    "eng": "engineering",
    "engr": "engineering",
    "rec": "recreation",
    "parks": "parks",
    "prks": "parks",
    "commdev": "community development",
    "cdev": "community development",
    "econdev": "economic development",
    "edc": "economic development",
    "util": "utilities",
    "utils": "utilities",
    "wtr": "water",
    "swr": "sewer",
    "fin": "finance",
    "acct": "accounting",
    "proc": "procurement",
    "prc": "procurement",
    "bldg": "building",
    "bld": "building",
    "insp": "inspection",
    "inspec": "inspection",
    "plng": "planning",
    "plan": "planning",
    "zng": "zoning",
    "dev": "development",
    "edu": "education",
    "ed": "education",
    "comms": "communications",
    "commu": "communications",
    "health": "health",
    "hlth": "health",
    "ph": "public health",
}


def _strip_garbage(text: str) -> str:
    """Remove obvious non-department noise (HTML, SQL comments, corruption markers)."""
    return strip_garbage(text)


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
    text = _PHONE_PATTERN.sub("", text)
    # Remove extensions (ext, x, extension)
    text = _EXT_PATTERN.sub("", text)
    return text


def _remove_emails(text: str) -> str:
    """Strip email addresses embedded inside department values."""
    return _EMAIL_PATTERN.sub("", text)


def _strip_symbol_wrappers(text: str) -> str:
    """Replace noisy wrapper symbols (e.g., ###CODE###) with spaces."""
    return _SYMBOL_WRAPPER_PATTERN.sub(" ", text)


def _normalize_separators(text: str) -> str:
    """Turn common separators (----) into single spaces while keeping slashes."""
    text = _SLASH_PATTERN.sub(" / ", text)
    return _SEPARATOR_PATTERN.sub(" ", text)


def _normalize_apostrophes(text: str) -> str:
    """Normalize curly apostrophes to ASCII for consistent casing."""
    return _APOSTROPHE_PATTERN.sub("'", text)


def _remove_parentheticals(text: str) -> str:
    """Remove all parenthetical segments, treating them as metadata/noise."""
    return re.sub(r"\([^)]*\)", " ", text)


def _expand_abbreviations(text: str) -> str:
    """
    Expand common abbreviations in department names.

    Example:
        >>> _expand_abbreviations("Strt Maint")
        "Street Maintenance"
    """
    parts = []
    for token in text.split():
        stripped = token.strip(",.;:")
        lower = stripped.lower()
        if lower in _ABBREVIATIONS:
            expanded = _ABBREVIATIONS[lower]
            rebuilt = token.replace(stripped, expanded)
            parts.append(rebuilt)
        else:
            parts.append(token)
    return " ".join(parts)


def _restore_acronyms(text: str) -> str:
    """Re-uppercase known acronyms after title-casing."""
    parts = []
    for token in text.split():
        stripped = token.strip(",.;:")
        core = stripped.upper()
        if core in _ACRONYMS:
            rebuilt = token.replace(stripped, core)
            parts.append(rebuilt)
        else:
            parts.append(token)
    return " ".join(parts)


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
    return _CODE_PATTERN.sub("", text)


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
            text = text[: match.start()]
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
    text = _WHITESPACE_PATTERN.sub(" ", text)
    return text.strip(" -_,.;:")


@lru_cache(maxsize=4096)
def normalize_department(raw_dept: str) -> str:
    """
    Normalize a raw department name by removing noise and standardizing format.

    This function uses @lru_cache(maxsize=4096) to cache normalization results.
    For batches with repeated department names (common in contact data), caching
    avoids redundant regex processing.

    Removes:
    - Phone numbers and extensions (e.g., "850-123-1234 ext 200")
    - Department codes (e.g., "000171 - ", "010100 - ")
    - Extra whitespace
    - Non-alphanumeric characters beyond ampersands and hyphens

    To clear the cache if memory is a concern:
        >>> normalize_department.cache_clear()

    To check cache statistics:
        >>> normalize_department.cache_info()

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
        ValueError: If the input is empty or not a string.
    """
    if not isinstance(raw_dept, str):
        raise ValueError(f"Department name must be a string, got {type(raw_dept).__name__}")

    if not raw_dept:
        raise ValueError("Department name cannot be empty")

    # Apply normalization steps in sequence
    text = _strip_garbage(raw_dept)
    text = _strip_html(text)
    text = _normalize_apostrophes(text)
    text = _remove_phone_numbers(text)
    text = _remove_emails(text)
    text = _strip_symbol_wrappers(text)
    text = _normalize_separators(text)
    text = _remove_contact_phrases(text)
    text = _remove_codes_and_ids(text)
    text = _remove_parentheticals(text)
    text = _remove_extra_whitespace(text)
    text = _DEPT_META_PATTERN.sub("", text).strip()
    text = normalize_unicode_ascii(text)

    if not text:
        raise ValueError(
            f"Department name became empty after normalization: '{raw_dept}'"
        )

    # Expand abbreviations before title-casing
    text = _expand_abbreviations(text)

    # Title case for consistency
    text = text.title()
    # Fix common apostrophe casing artifacts after title()
    text = text.replace("'S", "'s")
    text = _restore_acronyms(text)

    return text
