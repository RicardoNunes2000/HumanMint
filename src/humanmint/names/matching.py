"""
Name matching and comparison for HumanMint.

Implements nickname detection, canonicalization, and fuzzy name matching.
Uses the nicknames library for canonical nickname mappings and rapidfuzz for fuzzy scoring.
"""

from typing import Dict, Optional

from nicknames import NickNamer
from rapidfuzz import fuzz

from .normalize import normalize_name

# Global nickname mapper (lazy-loaded)
_nicknames_mapper: Optional[NickNamer] = None


def _get_nickname_mapper() -> NickNamer:
    """Lazy-load and cache the nickname mapper."""
    global _nicknames_mapper
    if _nicknames_mapper is None:
        _nicknames_mapper = NickNamer()
    return _nicknames_mapper


def detect_nickname(first_name: str) -> Optional[str]:
    """
    Detect if a first name is a nickname, and return canonical form.

    Args:
        first_name: First name to check.

    Returns:
        Canonical name if first_name is a nickname, None otherwise.

    Examples:
        >>> detect_nickname("Bob")
        "Robert"

        >>> detect_nickname("Bill")
        "William"

        >>> detect_nickname("John")
        None  # John is canonical, not a nickname
    """
    if not first_name:
        return None

    nn = _get_nickname_mapper()
    canonicals = nn.canonicals_of(first_name)

    # Return the first canonical if found
    if canonicals:
        return next(iter(canonicals))

    return None


def get_nickname_variants(canonical_name: str) -> set[str]:
    """
    Get all known nicknames for a canonical name.

    Args:
        canonical_name: Canonical first name.

    Returns:
        Set of known nicknames (empty if none found).

    Examples:
        >>> get_nickname_variants("Robert")
        {"bob", "rob", "bobby", "bert", ...}

        >>> get_nickname_variants("Elizabeth")
        {"liz", "beth", "betty", "liza", ...}
    """
    if not canonical_name:
        return set()

    nn = _get_nickname_mapper()
    return nn.nicknames_of(canonical_name)


def get_name_equivalents(name: str) -> set[str]:
    """
    Get all equivalent forms of a name (nicknames + canonicals).

    Useful for deduplication: tells you all the ways a name might appear.

    Args:
        name: First name to check.

    Returns:
        Set containing the name itself plus all nicknames and canonicals.

    Examples:
        >>> get_name_equivalents("Bob")
        {"bob", "robert", "rob", "bobby", "bert", ...}

        >>> get_name_equivalents("Alexander")
        {"alexander", "alex", "al", "lex", ...}
    """
    if not name:
        return set()

    nn = _get_nickname_mapper()
    name_lower = name.lower()

    # Get nicknames of this name (if it's canonical)
    nicknames = nn.nicknames_of(name_lower)

    # Get canonicals of this name (if it's a nickname)
    canonicals = nn.canonicals_of(name_lower)

    # Union them all
    equivalents = {name_lower}
    equivalents.update(nicknames)
    equivalents.update(canonicals)

    return equivalents


def compare_first_names(name1: str, name2: str, use_nicknames: bool = True) -> float:
    """
    Compare two first names with fuzzy matching and nickname awareness.

    Returns a score from 0.0 to 1.0:
    - 1.0: Exact match (including case-insensitive)
    - 0.9+: Nicknames of same canonical (e.g., "Bob" vs "Robert")
    - 0.8+: Close fuzzy match (e.g., "Jon" vs "John")
    - 0.5+: Moderate fuzzy match
    - <0.5: Poor match

    Args:
        name1: First name.
        name2: First name to compare against.
        use_nicknames: Whether to use nickname equivalents (default True).

    Returns:
        Similarity score 0.0-1.0.

    Examples:
        >>> compare_first_names("Bob", "Robert")
        0.95  # Nicknames

        >>> compare_first_names("John", "Jon")
        0.85  # Fuzzy match

        >>> compare_first_names("John", "Jane")
        0.4  # Poor match
    """
    if not name1 or not name2:
        return 0.0

    name1_lower = name1.lower()
    name2_lower = name2.lower()

    # Exact match
    if name1_lower == name2_lower:
        return 1.0

    # Check nickname relationships if enabled
    if use_nicknames:
        equivalents1 = get_name_equivalents(name1_lower)
        equivalents2 = get_name_equivalents(name2_lower)

        # Both names are in each other's equivalent set
        if name1_lower in equivalents2 and name2_lower in equivalents1:
            return 0.95

    # Fuzzy matching (token-based for robustness)
    fuzzy_score = fuzz.token_set_ratio(name1_lower, name2_lower) / 100.0

    return fuzzy_score


def compare_last_names(last1: str, last2: str) -> float:
    """
    Compare two last names with fuzzy matching.

    Last names rarely have nicknames, so this focuses on:
    - Exact matches
    - Hyphenated name variations
    - Fuzzy matches (typos, alternate spellings)

    Args:
        last1: Last name.
        last2: Last name to compare against.

    Returns:
        Similarity score 0.0-1.0.

    Examples:
        >>> compare_last_names("Smith", "smith")
        1.0  # Case-insensitive exact

        >>> compare_last_names("Kennedy-Smith", "Smith")
        0.6  # Partial match

        >>> compare_last_names("Smith", "Smyth")
        0.8  # Close match
    """
    if not last1 or not last2:
        return 0.0

    last1_lower = last1.lower()
    last2_lower = last2.lower()

    # Exact match
    if last1_lower == last2_lower:
        return 1.0

    # Handle hyphenated names: check if one contains the other
    if "-" in last1_lower and "-" not in last2_lower:
        parts = last1_lower.split("-")
        if last2_lower in parts:
            return 0.85

    if "-" in last2_lower and "-" not in last1_lower:
        parts = last2_lower.split("-")
        if last1_lower in parts:
            return 0.85

    # Fuzzy matching
    fuzzy_score = fuzz.token_set_ratio(last1_lower, last2_lower) / 100.0

    return fuzzy_score


def match_names(raw1: str, raw2: str, strict: bool = False) -> Dict[str, any]:
    """
    Compare two full names with detailed scoring and reasoning.

    Analyzes:
    - First name similarity (with nickname support)
    - Last name similarity
    - Middle name/initial match
    - Overall name match score

    Args:
        raw1: First name to match.
        raw2: Second name to match against.
        strict: If True, require initials to match; if False, be lenient.

    Returns:
        Dict with:
        - score: Overall match score (0.0-1.0)
        - first_match: First name score
        - last_match: Last name score
        - middle_match: Middle match score (or None)
        - is_match: True if score >= 0.75
        - reasons: List of match reasons
        - details: Dict with component scores

    Examples:
        >>> match_names("John Smith", "Jon Smith")
        {
            "score": 0.88,
            "first_match": 0.85,
            "last_match": 1.0,
            "middle_match": None,
            "is_match": True,
            "reasons": ["first name variant", "last name exact match"],
            "details": {...}
        }
    """
    if not raw1 or not raw2:
        return {
            "score": 0.0,
            "is_match": False,
            "reasons": ["invalid input"],
            "details": {},
        }

    # Normalize both names
    norm1 = normalize_name(raw1)
    norm2 = normalize_name(raw2)

    if not norm1.get("is_valid") or not norm2.get("is_valid"):
        return {
            "score": 0.0,
            "is_match": False,
            "reasons": ["normalization failed"],
            "details": {},
        }

    reasons = []

    # Compare first names
    first_score = compare_first_names(norm1["first"], norm2["first"])
    if first_score == 1.0:
        reasons.append("first name exact match")
    elif first_score >= 0.9:
        reasons.append("first name nickname match")
    elif first_score >= 0.8:
        reasons.append("first name variant")

    # Compare last names
    last_score = compare_last_names(norm1["last"], norm2["last"])
    if last_score == 1.0:
        reasons.append("last name exact match")
    elif last_score >= 0.85:
        reasons.append("last name close match")
    elif last_score >= 0.7:
        reasons.append("last name partial match")

    # Compare middle names/initials
    middle_score = 1.0
    if norm1.get("middle") or norm2.get("middle"):
        mid1 = (norm1.get("middle") or "").lower()
        mid2 = (norm2.get("middle") or "").lower()

        if mid1 and mid2:
            if mid1 == mid2:
                reasons.append("middle name exact match")
            elif mid1[0] == mid2[0]:  # First letter match
                middle_score = 0.9
                reasons.append("middle initial match")
            else:
                middle_score = 0.5
                reasons.append("middle name mismatch")
        elif mid1 or mid2:
            # One has middle, one doesn't
            middle_score = 0.8 if not strict else 0.6
            reasons.append("middle name missing in one")
    else:
        middle_score = 1.0

    # Calculate overall score (weighted average)
    # Give more weight to last name (family name is less likely to vary)
    overall_score = first_score * 0.3 + last_score * 0.5 + middle_score * 0.2

    return {
        "score": round(overall_score, 2),
        "first_match": round(first_score, 2),
        "last_match": round(last_score, 2),
        "middle_match": round(middle_score, 2)
        if norm1.get("middle") or norm2.get("middle")
        else None,
        "is_match": overall_score >= 0.75,
        "reasons": reasons,
        "details": {
            "name1": norm1,
            "name2": norm2,
        },
    }
