"""
Department name normalization for HumanMint.

Core normalization functions to clean and standardize department names by
removing noise, extra whitespace, and common artifacts.
"""

import re
from functools import lru_cache

from humanmint.text_clean import normalize_unicode_ascii, strip_garbage, strip_codes_and_ids, remove_parentheticals

_PHONE_PATTERN = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
_EXT_PATTERN = re.compile(r"\b(?:ext|x|extension)[\s.]*\d+\b", flags=re.IGNORECASE)
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
    return remove_parentheticals(text)


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


def _remove_codes_and_ids(text: str, strip_codes: str = "both") -> str:
    """
    Remove department codes and ID numbers.

    Uses the shared strip_codes_and_ids utility from text_clean module.
    Supports flexible control over which codes to strip.

    Args:
        text: Input string potentially containing codes.
        strip_codes: Which codes to remove ("both", "leading", "trailing", "none").

    Returns:
        str: Text with codes removed based on strip_codes setting.
    """
    return strip_codes_and_ids(text, strip_codes=strip_codes)


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
def _normalize_department_cached(raw_dept: str, strip_codes: str) -> str:
    """
    Cached core normalization to avoid re-parsing identical inputs.

    This function uses @lru_cache(maxsize=4096) to cache normalization results.
    For batches with repeated department names (common in contact data), caching
    avoids redundant regex processing.

    Args:
        raw_dept: Raw department name string.
        strip_codes: Which codes to remove ("both", "leading", "trailing", "none").

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
    text = _remove_codes_and_ids(text, strip_codes=strip_codes)
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

    # Deduplicate consecutive repeated tokens BEFORE acronym restoration
    # This ensures "IT IT" becomes "Information Technology" (singular) after expansion
    # Also handles multi-word duplicates like "Information Technology Information Technology"
    tokens = text.split()
    deduped = []
    i = 0
    while i < len(tokens):
        # Check if current token sequence repeats
        token_window = []
        j = i
        # Build a window of consecutive identical sequences
        while j < len(tokens):
            token_window.append(tokens[j])
            # If we've built a reasonable window, check if it repeats
            if len(token_window) > 0 and j + len(token_window) < len(tokens):
                is_repeat = True
                for k in range(len(token_window)):
                    if j + 1 + k >= len(tokens) or tokens[j + 1 + k].lower() != token_window[k].lower():
                        is_repeat = False
                        break
                if is_repeat:
                    # Found a repeat - add the window once and skip the repeat
                    deduped.extend(token_window)
                    i = j + 1 + len(token_window)
                    break
            j += 1
        else:
            # No repeat found - just add the token
            if i < len(tokens):
                deduped.append(tokens[i])
            i += 1

    text = ' '.join(deduped)

    text = _restore_acronyms(text)

    return text


def normalize_department(raw_dept: str, strip_codes: str = "both") -> str:
    """
    Normalize a raw department name by removing noise and standardizing format.

    This function uses @lru_cache internally (maxsize=4096) to cache normalization
    results. For batches with repeated department names (common in contact data),
    caching avoids redundant regex processing.

    Removes:
    - Phone numbers and extensions (e.g., "850-123-1234 ext 200")
    - Department codes based on strip_codes parameter
    - Extra whitespace
    - Non-alphanumeric characters beyond ampersands and hyphens

    To clear the cache if memory is a concern:
        >>> _normalize_department_cached.cache_clear()

    To check cache statistics:
        >>> _normalize_department_cached.cache_info()

    Example:
        >>> normalize_department("000171 - Supervisor 850-123-1234 ext 200")
        "Supervisor"
        >>> normalize_department("Public Works 850-123-1234")
        "Public Works"
        >>> normalize_department("Public Works 514134", strip_codes="both")
        "Public Works"
        >>> normalize_department("4591405 Public Works 514134", strip_codes="none")
        "4591405 Public Works 514134"

    Args:
        raw_dept: Raw department name string.
        strip_codes: Which codes to remove. Options:
            - "both" (default): Remove leading and trailing numeric codes
            - "leading": Remove only leading codes (e.g., "000171 - ")
            - "trailing": Remove only trailing codes (e.g., " 514134")
            - "none": Don't remove any codes

    Returns:
        str: Normalized department name in title case.

    Raises:
        ValueError: If the input is empty or not a string.
    """
    return _normalize_department_cached(raw_dept, strip_codes)
