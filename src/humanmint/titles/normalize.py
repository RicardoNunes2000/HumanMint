"""
Job title normalization for HumanMint.

Core normalization functions to clean and standardize job titles by
removing noise, extra whitespace, and common artifacts.
"""

import re
from functools import lru_cache

from humanmint.constants.titles import (PRESERVE_ABBREVIATIONS, STOPWORDS,
                                        TITLE_ABBREVIATIONS)
from humanmint.text_clean import (normalize_unicode_ascii,
                                  remove_parentheticals, strip_codes_and_ids,
                                  strip_garbage)


def _strip_garbage(text: str) -> str:
    """Remove obvious non-title noise (HTML, SQL comments, corruption markers)."""
    return strip_garbage(text)


def _expand_abbreviations(text: str) -> str:
    """Expand common job title abbreviations."""
    parts = []
    for token in text.split():
        # Strip trailing periods and commas (e.g., "Dir." -> "dir", "Dir.," -> "dir")
        clean_token = token.rstrip(".,").lower()
        if clean_token in PRESERVE_ABBREVIATIONS:
            parts.append(token.rstrip(".,"))
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
    - Dr., Mr., Mrs., Ms., Miss, Rev.
    - "FirstName LastName," patterns (e.g., "John Smith,")
    - PhD, MD, Esq., etc.

    Args:
        text: Input string potentially containing name prefixes or full names.

    Returns:
        str: Text with name prefixes and person names removed.
    """
    # Remove common salutations and credentials at the beginning
    # NOTE: Removed 'Prof' and 'Professor' from this list because they are often
    # valid job titles (e.g., "Professor of History") rather than just honorifics.
    text = re.sub(
        r"\b(?:Dr|Mr|Mrs|Ms|Miss|Rev|Reverend|Sir|Madam|Esq)\.?\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Remove "FirstName LastName," pattern (e.g., "John Smith," or "Jane Doe,")
    # CRITICAL FIX: To avoid matching job titles like "Finance Manager, CPA", only match
    # this pattern if there are 3+ capital words (person names rarely have 3+, but job titles do).
    # This prevents "Finance Manager," from being removed while still catching "Jane Mary Smith,".
    # Only match 3+ word names to avoid false positives on 2-word job titles
    text = re.sub(r"^[A-Z][a-z]*(?:\s+[A-Z][a-z]*){2,}\s*,\s*", "", text)
    # Remove trailing credentials like PhD, MD, etc.
    text = re.sub(
        r"(?:,\s*|\s+)(?:PhD|MD|DDS|DVM|Esq|MBA|MA|BS|BA|CISSP|PMP|RN|LPN|CPA)\.?$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _remove_codes_and_ids(text: str, strip_codes: str = "both") -> str:
    """
    Remove job codes and ID numbers.

    Uses the shared strip_codes_and_ids utility from text_clean module.
    Supports flexible control over which codes to strip.

    Args:
        text: Input string potentially containing codes.
        strip_codes: Which codes to remove ("both", "leading", "trailing", "none").

    Returns:
        str: Text with codes removed based on strip_codes setting.
    """
    return strip_codes_and_ids(text, strip_codes=strip_codes)


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

    Uses shared remove_parentheticals() for core functionality, then applies
    title-specific location/department removal (e.g., "- Downtown").

    Args:
        text: Input string with potential parenthetical content.

    Returns:
        str: Text with parenthetical info removed.
    """
    # Remove content in parentheses using shared utility
    text = remove_parentheticals(text)
    # Remove title-specific location/department info after dashes
    text = re.sub(
        r"\s*-\s*(?:Main|Downtown|Downtown Office|Main Office|HQ|Headquarters)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _normalize_separators(text: str) -> str:
    """Normalize common separators like slashes and ampersands."""
    if re.search(r"\bclerk of the works\b", text, flags=re.IGNORECASE):
        return text
    # Keep slashes as explicit separators, collapse long dash runs to spaces
    text = re.sub(r"\s*/\s*", " / ", text)
    text = re.sub(r"[-\u2013\u2014]+", " ", text)
    text = re.sub(r"\s*&\s*", " & ", text)
    # Collapse recursive/chain phrases like "to the", "of the" into separators,
    # but only when part of multi-role chains (keep small words for core titles)
    text = re.sub(r"\s+to\s+the\s+(?=[A-Za-z])", " / ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+of\s+the\s+(?=[A-Za-z])", " / ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+to\s+(?=[A-Za-z])", " / ", text, flags=re.IGNORECASE)
    # Avoid breaking phrases like "Chief of Police" by only splitting "of" when followed by another "of"/"to" chain
    text = re.sub(r"\s+of\s+(?=(?:Deputy|Assistant|Associate)\b)", " / ", text, flags=re.IGNORECASE)
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
    Handles special cases like "Mc" + capital letter (McDonald, not Mc donald).
    """
    parts = []
    tokens = text.split()
    for i, raw_token in enumerate(tokens):
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

        # Handle "Mc" + capital letter pattern (McDonald, not Mc donald)
        if base_lower == "mc" and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            next_first_char = next_token[0] if next_token else ""
            if next_first_char.isupper():
                # Join "Mc" with next token: "Mc Donald" -> "Mcdonald"
                parts.append("Mc" + next_token.lower() + suffix)
                # Skip the next token since we've absorbed it
                tokens[i + 1] = ""
                continue

        parts.append(token.capitalize() + suffix)

    # Filter out empty tokens that were absorbed
    return " ".join(p for p in parts if p)


@lru_cache(maxsize=4096)
def _normalize_title_cached(raw_title: str, strip_codes: str) -> str:
    """
    Cached core normalization to avoid re-parsing identical inputs.

    This function uses @lru_cache(maxsize=4096) to cache normalization results.
    For batches with repeated job titles (common in organizations), caching avoids
    redundant regex processing.

    Args:
        raw_title: Raw job title string.
        strip_codes: Which codes to remove ("both", "leading", "trailing", "none").

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
    text = _remove_codes_and_ids(text, strip_codes=strip_codes)
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


def normalize_title(raw_title: str, strip_codes: str = "both") -> str:
    """
    Normalize a raw job title by removing noise and standardizing format.

    This function uses @lru_cache internally (maxsize=4096) to cache normalization
    results. For batches with repeated job titles (common in organizations), caching
    avoids redundant regex processing.

    Removes:
    - Name prefixes (e.g., "Dr.", "Mr.")
    - Job codes based on strip_codes parameter
    - Parenthetical info (e.g., "(Finance)", "(Main Office)")
    - Extra whitespace

    To clear the cache if memory is a concern:
        >>> _normalize_title_cached.cache_clear()

    To check cache statistics:
        >>> _normalize_title_cached.cache_info()

    Example:
        >>> normalize_title("Dr. John Smith, CEO")
        "CEO"
        >>> normalize_title("0001 - Director (Finance)")
        "Director"
        >>> normalize_title("4591405 Chief of Police 514134")
        "Chief Of Police"
        >>> normalize_title("  Senior  Manager  ")
        "Senior Manager"

    Args:
        raw_title: Raw job title string.
        strip_codes: Which codes to remove. Options:
            - "both" (default): Remove leading and trailing numeric codes
            - "leading": Remove only leading codes (e.g., "0001 - ")
            - "trailing": Remove only trailing codes (e.g., " 514134")
            - "none": Don't remove any codes

    Returns:
        str: Normalized job title in title case.

    Raises:
        ValueError: If the input is empty or not a string.
    """
    return _normalize_title_cached(raw_title, strip_codes)


def extract_seniority(normalized_title: str) -> str:
    """
    Extract seniority level from a normalized job title.

    Detects common seniority modifiers like Senior, Junior, Lead, Principal, etc.
    Returns the detected seniority level or None if not found.

    Args:
        normalized_title: A normalized job title (typically output from normalize_title).

    Returns:
        str: The seniority level (e.g., "Senior", "Junior", "Lead", "Principal"),
             or None if no seniority modifier is detected.

    Example:
        >>> extract_seniority("Senior Maintenance Technician")
        "Senior"
        >>> extract_seniority("Lead Software Engineer")
        "Lead"
        >>> extract_seniority("Maintenance Technician")
        None
    """
    if not normalized_title or not isinstance(normalized_title, str):
        return None

    title_lower = normalized_title.lower()

    # Explicit blacklists: senior+intern/student/analyst should not gain seniority
    if "senior" in title_lower:
        for blocked in ("intern", "student", "analyst"):
            if blocked in title_lower:
                return None

    # Executive assistant roles are support, not executive
    if "executive assistant" in title_lower or "assistant to the" in title_lower:
        return None

    # Seniority keywords (ordered by specificity - longest first to avoid partial matches)
    seniority_keywords = [
        # C-suite roles
        "chief executive officer",
        "chief operating officer",
        "chief financial officer",
        "chief information officer",
        "chief technology officer",
        "chief marketing officer",
        "chief product officer",
        "chief security officer",
        "chief academic officer",
        "chief risk officer",
        "chief compliance officer",
        "chief information security officer",
        "chief data officer",
        "chief human resources officer",
        "chief legal officer",
        "chief strategy officer",
        "chief quality officer",
        "chief medical officer",
        "chief nursing officer",

        # Executive/Director level
        "executive director",
        "executive vice president",
        "senior vice president",
        "vice president",
        "associate vice president",
        "assistant vice president",
        "deputy director",
        "assistant director",
        "associate director",

        # Principal/Lead roles (longer phrases first)
        "principal engineer",
        "principal architect",
        "principal consultant",
        "principal analyst",
        "principal scientist",
        "principal product manager",
        "principal research scientist",
        "principal investigator",
        "principal counsel",
        "principal manager",

        # Senior roles (longer phrases first)
        "senior engineer",
        "senior architect",
        "senior manager",
        "senior director",
        "senior analyst",
        "senior consultant",
        "senior advisor",
        "senior specialist",
        "senior scientist",
        "senior developer",
        "senior administrator",
        "senior technician",
        "senior associate",
        "senior counsel",
        "senior planner",
        "senior researcher",
        "senior investigator",
        "senior officer",

        # Lead roles (longer phrases first)
        "lead engineer",
        "lead architect",
        "lead developer",
        "lead analyst",
        "lead manager",
        "lead consultant",
        "lead designer",
        "lead scientist",
        "lead investigator",
        "lead researcher",

        # Staff-level individual contributors
        "staff engineer",
        "staff architect",
        "staff scientist",
        "staff analyst",

        # Single-word seniority modifiers (catch-all, in order of hierarchy)
        "chief",
        "executive",
        "director",
        "principal",
        "senior",
        "lead",
        "junior",
        "assistant",
        "associate",
        "entry-level",
    ]

    for keyword in seniority_keywords:
        if title_lower.startswith(keyword):
            # Return the properly capitalized version
            return " ".join(word.capitalize() for word in keyword.split())

    return None
