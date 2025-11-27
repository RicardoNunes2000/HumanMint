"""
Department fuzzy matching for HumanMint.

Fuzzy matching engine to find the best canonical department match for
normalized department names using multi-strategy similarity scoring.

Strategy:
1. Check if already canonical (O(1))
2. Check CSV mappings for exact match (O(1) with cache)
3. Check for substring match with canonicals (O(n))
4. Fall back to multi-scorer fuzzy matching with rapidfuzz:
   a. token_set_ratio (handles extra words like "Polce Department")
   b. token_sort_ratio (handles word reordering)
   c. partial_ratio with lowered threshold (catches typos like "Polce" -> "Police")
"""

import re
from functools import lru_cache
from typing import Optional
from rapidfuzz import fuzz, process
from .data_loader import CANONICAL_DEPARTMENTS, CANONICAL_DEPARTMENTS_SET
from .normalize import normalize_department

# Cache for CSV mappings to avoid repeated file reads
_mapping_cache = None
_canonical_lowers = [(c, c.lower()) for c in CANONICAL_DEPARTMENTS]

# Keywords that indicate non-department data (building names, locations, etc.)
_NON_DEPARTMENT_KEYWORDS = {
    "building",
    "room",
    "floor",
    "suite",
    "office",
    "desk",
    "wing",
    "unit",
    "bldg",
    "rm",
    "apt",
    "space",
    "block",
    "section",
    "area",
    "zone",
    "lot",
}

_COMMON_ABBREVIATIONS = {
    "it": "Information Technology",
    "is": "Information Technology",
    "hr": "Human Resources",
    "pw": "Public Works",
    "dpw": "Public Works",
    "rec": "Parks & Recreation",
    "parks": "Parks & Recreation",
    "pd": "Police",
    "fd": "Fire",
    "em": "Emergency Management",
    "fin": "Finance",
    "eng": "Engineering",
}

# Regex pattern for location-like inputs (e.g., "Room 101", "Building 5A", "Suite 200")
_LOCATION_PATTERN = r"(room|floor|building|suite|office|bldg|rm|apt)\s*\d"


def _is_likely_non_department(text: str) -> bool:
    """
    Detect if input looks like a building/location rather than a department.

    Returns True if the text contains:
    - Location keywords (Room, Building, Suite, etc.)
    - Location patterns (Room 101, Building 5A, etc.)
    - Very short keywords that are unlikely to be departments

    Args:
        text: Normalized department text to check.

    Returns:
        True if text appears to be a location/building name, False otherwise.
    """
    if not text:
        return False

    # If already canonical, do not flag as location-only noise
    if text in CANONICAL_DEPARTMENTS_SET:
        return False

    text_lower = text.lower()
    has_digit = any(ch.isdigit() for ch in text_lower)

    # Check for location pattern (Room 101, Building 5, etc.)
    if re.search(_LOCATION_PATTERN, text_lower, re.IGNORECASE):
        return True

    # Check for non-department keywords
    words = text_lower.split()
    for word in words:
        cleaned = word.rstrip(".,;-")
        if cleaned in {"room", "suite", "desk", "rm", "apt"}:
            return True
        if cleaned in _NON_DEPARTMENT_KEYWORDS and has_digit:
            return True

    return False


# Exposed wrapper for reuse in other modules without touching the private cache
def is_likely_non_department(text: str) -> bool:
    """Public-facing helper to detect location-like inputs."""
    return _is_likely_non_department(text)


def _get_mapping_cache():
    """Lazy-load and cache CSV mappings."""
    global _mapping_cache
    if _mapping_cache is None:
        # Load full mappings dict for fast lookups
        from .data_loader import load_mappings

        _mapping_cache = {}
        # Build reverse mapping: original_name -> canonical
        all_mappings = load_mappings()
        for canonical, originals in all_mappings.items():
            for original in originals:
                _mapping_cache[original.lower()] = canonical
    return _mapping_cache


@lru_cache(maxsize=4096)
def _find_best_match_normalized(
    search_name: str,
    threshold: float,
) -> Optional[str]:
    """Cached core matcher for already-normalized names."""
    search_name_lower = search_name.lower()

    parts = [p for p in search_name_lower.split() if p]
    for part in parts:
        token = part.strip(".")
        if token.isdigit():
            continue
        if token in _COMMON_ABBREVIATIONS:
            return _COMMON_ABBREVIATIONS[token]
        # Only look at the leading meaningful token for abbreviation shortcuts
        break

    # Early rejection: if input looks like a building/location, don't force-match
    # This prevents "Harbor Building 04B" from matching to "Budget"
    if _is_likely_non_department(search_name):
        return None

    # Check if already canonical (O(1))
    if search_name in CANONICAL_DEPARTMENTS_SET:
        return search_name

    # Strategy 1: Check CSV mappings for exact match (O(1) with cache)
    try:
        mapping_cache = _get_mapping_cache()
        if search_name_lower in mapping_cache:
            return mapping_cache[search_name_lower]
    except Exception:
        # If mapping cache fails, continue to other strategies
        pass

    # Strategy 2: Check for substring match with canonical departments
    # e.g., "Fire Department" contains "Fire", "Water Utilities" contains "Water"
    matches = []
    for canonical, canonical_lower in _canonical_lowers:
        if canonical_lower in search_name_lower or search_name_lower in canonical_lower:
            # Score: how early in the search string does this appear? (prefer early matches)
            # and prefer longer canonical names for specificity
            position = search_name_lower.find(canonical_lower)
            score = (
                -position,
                len(canonical),
            )  # Negative position = earlier = higher score
            matches.append((score, canonical))

    if matches:
        # Return the best match (earliest appearance, then longest)
        return max(matches, key=lambda x: x[0])[1]

    # Strategy 3: Find close matches using rapidfuzz (fallback)
    # Try multiple scoring strategies to find the best match
    score_cutoff = threshold * 100

    # First try token_set_ratio (better for extra words like "Polce Department")
    result = process.extractOne(
        search_name,
        CANONICAL_DEPARTMENTS,
        scorer=fuzz.token_set_ratio,
        score_cutoff=score_cutoff,
    )
    if result and result[1] >= score_cutoff:  # Verify score meets threshold
        return result[0]

    # If token_set_ratio fails, try token_sort_ratio
    result = process.extractOne(
        search_name,
        CANONICAL_DEPARTMENTS,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=score_cutoff,
    )
    if result and result[1] >= score_cutoff:  # Verify score meets threshold
        return result[0]

    # If still no match, try with a slightly lower threshold using partial_ratio
    # This catches typos better (e.g., "Polce" -> "Police")
    # But only if the match quality is genuinely good (at least 65%)
    lower_cutoff = max(score_cutoff - 15, 65)  # At least 65% match for fallback
    result = process.extractOne(
        search_name,
        CANONICAL_DEPARTMENTS,
        scorer=fuzz.partial_ratio,
        score_cutoff=lower_cutoff,
    )
    if result and result[1] >= lower_cutoff:  # Verify score meets lower threshold
        return result[0]

    return None


def find_best_match(
    dept_name: str,
    threshold: float = 0.6,
    normalize: bool = True,
) -> Optional[str]:
    """
    Find the best canonical department match for a given department name.

    Uses difflib.get_close_matches to find fuzzy matches against the canonical
    department list. If the input is not already normalized, it will be
    normalized first.

    Example:
        >>> find_best_match("Public Works 850-123-1234")
        "Public Works"
        >>> find_best_match("PW Dept", threshold=0.6)
        "Public Works"
        >>> find_best_match("Nonexistent Dept", threshold=0.6)
        None

    Args:
        dept_name: Department name to match (raw or normalized).
        threshold: Minimum similarity score (0.0 to 1.0). Defaults to 0.6.
        normalize: Whether to normalize the input first. Defaults to True.

    Returns:
        Optional[str]: Best matching canonical department name, or None if no
                      match exceeds the threshold.

    Raises:
        ValueError: If dept_name is empty.
        ValueError: If threshold is not between 0.0 and 1.0.
    """
    if not dept_name:
        raise ValueError("Department name cannot be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    # Normalize the input if requested
    search_name = normalize_department(dept_name) if normalize else dept_name
    return _find_best_match_normalized(search_name, threshold)


def find_all_matches(
    dept_name: str,
    threshold: float = 0.6,
    top_n: int = 3,
    normalize: bool = True,
) -> list[str]:
    """
    Find all canonical department matches above a similarity threshold.

    Returns multiple matches ranked by similarity score, useful for
    interactive selection or validation.

    Example:
        >>> find_all_matches("Public Works", threshold=0.5, top_n=3)
        ["Public Works", "Public Safety"]

    Args:
        dept_name: Department name to match (raw or normalized).
        threshold: Minimum similarity score (0.0 to 1.0). Defaults to 0.6.
        top_n: Maximum number of matches to return. Defaults to 3.
        normalize: Whether to normalize the input first. Defaults to True.

    Returns:
        list[str]: List of matching canonical department names, ranked by
                   similarity. Empty list if no matches exceed the threshold.

    Raises:
        ValueError: If dept_name is empty.
        ValueError: If threshold is not between 0.0 and 1.0.
    """
    if not dept_name:
        raise ValueError("Department name cannot be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    # Normalize the input if requested
    search_name = normalize_department(dept_name) if normalize else dept_name

    # Check if already canonical
    if search_name in CANONICAL_DEPARTMENTS_SET:
        return [search_name]

    # Find all close matches
    score_cutoff = threshold * 100
    matches = process.extract(
        search_name,
        CANONICAL_DEPARTMENTS,
        scorer=fuzz.token_sort_ratio,
        limit=top_n,
        score_cutoff=score_cutoff,
    )
    return [m[0] for m in matches]


def match_departments(
    dept_names: list[str],
    threshold: float = 0.6,
    normalize: bool = True,
) -> dict[str, Optional[str]]:
    """
    Match multiple department names to their canonical equivalents.

    Processes a list of raw or normalized department names and returns a
    mapping of original names to their best matches. Useful for batch
    processing.

    Example:
        >>> match_departments(["Public Works", "PW Dept", "Unknown"])
        {
            "Public Works": "Public Works",
            "PW Dept": "Public Works",
            "Unknown": None
        }

    Args:
        dept_names: List of department names to match.
        threshold: Minimum similarity score (0.0 to 1.0). Defaults to 0.6.
        normalize: Whether to normalize inputs first. Defaults to True.

    Returns:
        dict[str, Optional[str]]: Mapping of input names to canonical matches
                                  (None if no match found).

    Raises:
        ValueError: If threshold is not between 0.0 and 1.0.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    result = {}
    for dept in dept_names:
        try:
            match = find_best_match(dept, threshold=threshold, normalize=normalize)
            result[dept] = match
        except ValueError:
            # If normalization fails, record as no match
            result[dept] = None

    return result


def get_similarity_score(dept1: str, dept2: str) -> float:
    """
    Calculate similarity score between two department names.

    Uses rapidfuzz token_sort_ratio to compute a similarity ratio between
    0.0 (completely different) and 1.0 (identical).

    Example:
        >>> get_similarity_score("Public Works", "Public Works")
        1.0
        >>> get_similarity_score("Public Works", "Public Safety")
        0.615...

    Args:
        dept1: First department name.
        dept2: Second department name.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    if not dept1 or not dept2:
        return 0.0

    score = fuzz.token_sort_ratio(dept1.lower(), dept2.lower())
    return score / 100.0
