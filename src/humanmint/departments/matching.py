"""
Department fuzzy matching for HumanMint.

Strict matching engine prioritizing department_mappings_list as the source of truth.
NO BLS data is used.

Strategy:
1. Garbage Filter: Reject physical locations (Room 101), but allow "Stock Room", "Mail Room".
2. Exact Match: Check Canonical list and Reverse Mappings (O(1)).
3. Two-Pass Fuzzy Matching:
   - Pass 1 (Strict): 90% threshold, no validation.
   - Pass 2 (Lenient): 80% threshold, with semantic tag agreement check only.
"""

import logging
import re
from functools import lru_cache
from typing import Dict, List, Optional, Set

from rapidfuzz import fuzz, process

from humanmint.data.utils import load_package_json_gz
from humanmint.text_clean import extract_tokens

# Import from your provided data_loader
from .data_loader import CANONICAL_DEPARTMENTS_SET, get_mapping_for_original
from .normalize import normalize_department

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & Patterns
# ---------------------------------------------------------------------------

# Keywords that suggest a location/furniture, not a department
_NON_DEPT_KEYWORDS = {
    "building",
    "room",
    "floor",
    "suite",
    "desk",
    "wing",
    "bldg",
    "rm",
    "apt",
    "space",
    "block",
    "lot",
    "cubicle",
    "station",
    "ladder",
}

# Generic container words that clutter fuzzy matching and should be stripped
# These are metadata about what the field represents, not distinctive features
_GENERIC_TOKENS = {
    "department",
    "dept",
    "division",
    "div",
    "bureau",
    "office",
    "agency",
    "city",
    "county",
    "state",
    "government",
    "municipal",
    "commission",
    "board",
    "authority",
}

# Exceptions: "Rooms" that are actually departments
_ALLOWED_ROOM_PREFIXES = {
    "mail",
    "stock",
    "server",
    "control",
    "emergency",
    "waiting",
    "media",
}

# Regex to catch "Room 101", "Bldg C", "Suite 500"
_LOCATION_PATTERN = re.compile(
    r"\b(room|floor|bldg|suite|ste|rm|apt|unit|wing)\s*[\d#A-Z]", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Data Initialization
# ---------------------------------------------------------------------------

_SEMANTIC_CACHE: Dict[str, str] = {}
_FUZZY_CANDIDATES: List[str] = []
_CANDIDATE_TO_CANONICAL: Dict[str, str] = {}


def _ensure_data_loaded():
    """Lazy load semantic tokens and build fuzzy candidate lists."""
    global _SEMANTIC_CACHE, _FUZZY_CANDIDATES, _CANDIDATE_TO_CANONICAL

    if not _SEMANTIC_CACHE:
        try:
            data = load_package_json_gz("semantic_tokens.json.gz")
            if isinstance(data, dict):
                _SEMANTIC_CACHE = {k.lower(): v for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load semantic_tokens.json.gz: {e}")
            _SEMANTIC_CACHE = {}

    if not _FUZZY_CANDIDATES:
        # IMPORTANT: Only fuzzy match against the 67 canonical department names,
        # NOT against all 5914 variations in the mappings file.
        # Using variations causes false positives (e.g., "City Manager's Office"
        # matches "County Managers Office" which maps to "County Manager").
        from .data_loader import get_canonical_departments

        candidates = {}
        for canonical in get_canonical_departments():
            candidates[canonical.lower()] = canonical

        _CANDIDATE_TO_CANONICAL = candidates
        _FUZZY_CANDIDATES = list(candidates.keys())


# ---------------------------------------------------------------------------
# Helper Logic
# ---------------------------------------------------------------------------


def _strip_generic_tokens(text: str) -> str:
    """
    Remove generic container words that don't contribute to fuzzy matching.

    These words (department, county, city, etc.) are metadata about what the field
    represents, not distinctive features of the department itself. Stripping them
    improves fuzzy matching by reducing noise.

    Example:
        >>> _strip_generic_tokens("Public Works Department")
        "Public Works"
        >>> _strip_generic_tokens("Parks and Recreation Bureau")
        "Parks and Recreation"

    Args:
        text: Input text (should already be lowercase).

    Returns:
        str: Text with generic tokens removed, normalized to single spaces.
    """
    tokens = text.split()
    filtered = [t for t in tokens if t.lower() not in _GENERIC_TOKENS]
    result = " ".join(filtered).strip()
    return result if result else text  # Return original if nothing left


def is_likely_non_department(text: str) -> bool:
    """
    Detects if a string is likely a physical location (Room, Suite).
    Handles exceptions like 'Stock Room' or 'Mail Room'.
    """
    if not text:
        return False
    if text in CANONICAL_DEPARTMENTS_SET:
        return False

    text_lower = text.lower()

    # 1. Regex Pattern Check (e.g., "Room 404")
    if _LOCATION_PATTERN.search(text_lower):
        return True

    # 2. Keyword Check
    tokens = extract_tokens(text_lower)

    # Check if we have a "Room" word
    intersection = tokens.intersection(_NON_DEPT_KEYWORDS)
    if intersection:
        # If it contains a "Room" word, check if it's an allowed exception
        if not tokens.isdisjoint(_ALLOWED_ROOM_PREFIXES):
            return False  # It IS a department (Stock Room)

        # If it has digits + a location word -> Garbage
        if any(ch.isdigit() for ch in text_lower):
            return True

        # If it is JUST "Room" or "Suite" -> Garbage
        if len(tokens) == 1:
            return True

    return False


def _get_all_semantic_tags(text: str) -> Set[str]:
    """Get all semantic tags from text (excluding GENERIC and NULL)."""
    tokens = extract_tokens(text)
    tags = set()
    for token in tokens:
        if token in _SEMANTIC_CACHE:
            tag = _SEMANTIC_CACHE[token]
            if tag not in ("GENERIC", "NULL"):
                tags.add(tag)
    return tags


def _have_semantic_agreement(tags1: Set[str], tags2: Set[str]) -> bool:
    """
    Check if two sets of semantic tags agree.

    Rules:
    - If both have tags: they must overlap (at least one tag in common)
    - If both are empty: agree (untagged, generic terms)
    - If only one has tags: agree (one side is likely generic/untagged like "Maintenance")

    This is lenient because canonical department names may not be tagged if they're
    generic terms, and the fuzzy score should be the primary signal.

    Args:
        tags1: First set of semantic tags.
        tags2: Second set of semantic tags.

    Returns:
        bool: True if tags agree, False if they conflict.
    """
    # If both are empty, they agree (both untagged/generic)
    if not tags1 and not tags2:
        return True

    # If only one has tags, agree (one side is likely generic/untagged)
    if not tags1 or not tags2:
        return True

    # Both have tags - they must overlap
    return bool(tags1.intersection(tags2))


# ---------------------------------------------------------------------------
# Core Matching Engine
# ---------------------------------------------------------------------------


def _find_best_match_strict(search_name: str) -> Optional[str]:
    """
    Strict pass: 90% fuzzy threshold, no validation.

    Returns best match if fuzzy similarity >= 90%, otherwise None.
    """
    search_lower = search_name.lower()

    if len(search_lower) < 3:
        return None

    # Strip generic tokens to avoid noise in fuzzy matching
    search_clean = _strip_generic_tokens(search_lower)

    result = process.extractOne(
        search_clean,
        _FUZZY_CANDIDATES,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=90.0,
    )

    if not result:
        return None

    candidate_key, _score, _ = result
    canonical_match = _CANDIDATE_TO_CANONICAL.get(candidate_key)

    if not canonical_match:
        return None

    # Require semantic agreement even on the strict pass to block obvious hallucinations
    input_tags = _get_all_semantic_tags(search_lower)
    candidate_tags = _get_all_semantic_tags(candidate_key)
    if not _have_semantic_agreement(input_tags, candidate_tags):
        return None

    return canonical_match


def _find_best_match_lenient(search_name: str) -> Optional[str]:
    """
    Lenient pass: 70% fuzzy threshold with semantic agreement check.

    Returns best match if:
    1. Fuzzy score >= 70%
    2. Semantic tags agree (both tagged and overlap, OR both untagged)

    This catches cases like "Library – Youth Programs" → "Library"
    where strict fuzzy matching fails but semantic context is clear.
    """
    search_lower = search_name.lower()

    if len(search_lower) < 3:
        return None

    # Strip generic tokens to avoid noise in fuzzy matching
    search_clean = _strip_generic_tokens(search_lower)

    result = process.extractOne(
        search_clean,
        _FUZZY_CANDIDATES,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=70.0,
    )

    if not result:
        return None

    candidate_key, _score, _ = result
    canonical_match = _CANDIDATE_TO_CANONICAL.get(candidate_key)

    if not canonical_match:
        return None

    # Check semantic agreement
    input_tags = _get_all_semantic_tags(search_lower)
    candidate_tags = _get_all_semantic_tags(candidate_key)

    if not _have_semantic_agreement(input_tags, candidate_tags):
        return None

    return canonical_match


def _find_best_match_partial(search_name: str) -> Optional[str]:
    """
    Partial pass: Use token_set_ratio for cases where fuzzy matching fails.

    Returns best match if fuzzy score >= 60% using token_set_ratio,
    which handles extra words better than token_sort_ratio.

    This catches cases like "Food Service High School Cafeteria" → "Food Service"
    where location-specific noise prevents standard fuzzy matching.
    """
    search_lower = search_name.lower()

    if len(search_lower) < 3:
        return None

    # Strip generic tokens to avoid noise in fuzzy matching
    search_clean = _strip_generic_tokens(search_lower)

    result = process.extractOne(
        search_clean,
        _FUZZY_CANDIDATES,
        scorer=fuzz.token_set_ratio,
        score_cutoff=60.0,
    )

    if not result:
        return None

    candidate_key, _score, _ = result
    canonical_match = _CANDIDATE_TO_CANONICAL.get(candidate_key)

    if not canonical_match:
        return None

    # Check semantic agreement (lenient - only reject if both have conflicting tags)
    input_tags = _get_all_semantic_tags(search_lower)
    candidate_tags = _get_all_semantic_tags(candidate_key)

    if not _have_semantic_agreement(input_tags, candidate_tags):
        return None

    return canonical_match


@lru_cache(maxsize=4096)
def _find_best_match_normalized(search_name: str, threshold: float) -> Optional[str]:
    """
    Find best canonical department match using three-pass approach.

    Pass 1 (Strict): 90% token_sort_ratio threshold, no validation.
    Pass 2 (Lenient): 70% token_sort_ratio threshold, semantic agreement required.
    Pass 3 (Partial): 60% token_set_ratio threshold for cases with extra words.

    Returns the first match found, or None if no pass succeeds.

    Args:
        search_name: Normalized department name.
        threshold: Not used (kept for backward compatibility).

    Returns:
        Optional[str]: Canonical department name, or None if no match found.
    """
    _ensure_data_loaded()

    # 1. GARBAGE FILTER
    if is_likely_non_department(search_name):
        return None

    search_lower = search_name.lower()

    # 2. EXACT MATCH (O(1))
    if search_name in CANONICAL_DEPARTMENTS_SET:
        return search_name

    exact_map = get_mapping_for_original(search_name)
    if exact_map:
        return exact_map

    # 3. PASS 1: Strict (90% token_sort, no validation)
    match = _find_best_match_strict(search_lower)
    if match:
        return match

    # 4. PASS 2: Lenient (70% token_sort + semantic agreement)
    match = _find_best_match_lenient(search_lower)
    if match:
        return match

    # 5. PASS 3: Partial (60% token_set for extra words, semantic agreement)
    match = _find_best_match_partial(search_lower)
    if match:
        return match

    # 6. No match found
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_best_match(
    dept_name: str, threshold: float = 0.6, normalize: bool = True
) -> Optional[str]:
    """
    Find the best canonical department match using two-pass approach.

    Returns None if no match found (caller should handle as appropriate).

    Args:
        dept_name: Raw or normalized department name.
        threshold: Ignored (kept for backward compatibility).
        normalize: If True, normalize input before matching. Default True.

    Returns:
        Optional[str]: Canonical department name, or None if no match found.

    Raises:
        ValueError: If department name is invalid.
    """
    if not dept_name:
        raise ValueError("Department name cannot be empty")

    search_name = normalize_department(dept_name) if normalize else dept_name
    if search_name and search_name.lower() in {"empty", "tbd", "n/a", "na"}:
        return None
    return _find_best_match_normalized(search_name, threshold)


def find_all_matches(
    dept_name: str, threshold: float = 0.6, top_n: int = 3, normalize: bool = True
) -> list[str]:
    """Returns top N matches, skipping semantic validation."""
    _ensure_data_loaded()
    search_name = normalize_department(dept_name) if normalize else dept_name

    if is_likely_non_department(search_name):
        return []

    score_cutoff = threshold * 100
    matches = process.extract(
        search_name.lower(),
        _FUZZY_CANDIDATES,
        scorer=fuzz.token_sort_ratio,
        limit=top_n,
        score_cutoff=score_cutoff,
    )

    results = []
    seen = set()
    for m in matches:
        candidate_key = m[0]
        canonical = _CANDIDATE_TO_CANONICAL.get(candidate_key)
        if canonical and canonical not in seen:
            results.append(canonical)
            seen.add(canonical)

    return results


def match_departments(
    dept_names: list[str], threshold: float = 0.6, normalize: bool = True
) -> dict[str, Optional[str]]:
    """
    Match multiple departments.

    Args:
        dept_names: List of raw department names.
        threshold: Ignored (kept for backward compatibility).
        normalize: If True, normalize inputs before matching.

    Returns:
        dict: Mapping of input names to canonical names (or None if no match).
    """
    result = {}
    for dept in dept_names:
        try:
            match = find_best_match(dept, threshold=threshold, normalize=normalize)
            result[dept] = match
        except ValueError:
            result[dept] = None
    return result


def get_similarity_score(dept1: str, dept2: str) -> float:
    """
    Get normalized similarity score between two department names (0.0 to 1.0).

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
