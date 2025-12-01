"""
Title matching enhancements: rank hierarchy, acronyms, semantic clustering.

This module adds sophisticated logic to improve title matching by:
1. Preserving rank hierarchy (Engineer > Technician > Assistant)
2. Protecting acronyms (GIS, SOC, EMS) from fuzzy matching
3. Handling compound roles (X & Y Director)
4. Clustering semantically similar but distinct roles (Fire vs Police vs EMS)
"""

from typing import Optional, Set


# RANK HIERARCHY: Higher rank should never degrade to lower rank
RANK_HIERARCHY = {
    # Chief/Director level
    "chief": 100,
    "director": 95,
    "manager": 90,
    "supervisor": 85,
    "coordinator": 80,

    # Professional level
    "engineer": 75,
    "architect": 74,
    "analyst": 73,
    "specialist": 72,
    "officer": 71,

    # Technical level
    "technician": 60,
    "assistant": 50,
    "associate": 55,
    "aide": 45,
    "helper": 40,
}

# PROTECTED ACRONYMS: Must not be fuzzy-matched
PROTECTED_ACRONYMS = {
    "gis": "geographic information systems",
    "soc": "security operations center",
    "ems": "emergency medical services",
    "hvac": "heating ventilation air conditioning",
    "it": "information technology",
    "hr": "human resources",
    "cfo": "chief financial officer",
    "cio": "chief information officer",
    "cto": "chief technology officer",
}

# SEMANTIC ROLE CLUSTERS: Distinct role types that shouldn't cross-match
SEMANTIC_ROLE_CLUSTERS = {
    "FIRE": {"fire", "firefighter", "fire marshal", "fire chief"},
    "POLICE": {"police", "officer", "detective", "sergeant", "captain", "sheriff"},
    "EMS": {"emergency medical", "ems", "paramedic", "ambulance"},
    "WATER": {"water", "wastewater", "utilities", "sewer"},
    "IT": {"information technology", "it ", "network", "systems", "programmer", "developer"},
    "PLANNING": {"planner", "planning", "zoning", "development"},
}

# COMPOUND ROLE INDICATORS: Patterns that indicate multiple roles
COMPOUND_PATTERNS = [
    r"(\w+)\s+&\s+(\w+)\s+(director|manager|coordinator)",
    r"([\w\s]+)/\s*([\w\s]+)\s+(director|manager)",
]


def _extract_rank(title: str) -> int:
    """
    Extract the effective rank from a title.

    When multiple ranks exist, uses the highest but accounts for demotion
    indicators (e.g., "engineer" + "technician" = technician rank).

    Args:
        title: Job title string

    Returns:
        Rank score (0-100), higher = more senior
    """
    title_lower = title.lower()
    found_ranks = []

    for rank_word, rank_score in RANK_HIERARCHY.items():
        if rank_word in title_lower:
            found_ranks.append((rank_word, rank_score))

    if not found_ranks:
        return 0

    # If multiple ranks found, check for demotion patterns
    # e.g., "engineering technician" should use technician rank, not engineer
    if len(found_ranks) > 1:
        # Sort by rank score
        found_ranks.sort(key=lambda x: x[1], reverse=True)
        lowest_rank_word = found_ranks[-1][0]

        # Check if it's a compound like "X technician" or "X assistant"
        if lowest_rank_word in ("technician", "assistant", "aide", "helper"):
            if lowest_rank_word in title_lower.split()[-2:]:  # Check last 2 words
                return found_ranks[-1][1]  # Use the lower rank

    # Return highest rank found
    return found_ranks[0][1]


def _extract_acronyms(text: str) -> Set[str]:
    """
    Extract protected acronyms from text.

    Args:
        text: Input text

    Returns:
        Set of acronyms found (lowercase)
    """
    found = set()
    text_lower = text.lower()

    for acronym in PROTECTED_ACRONYMS.keys():
        if acronym in text_lower:
            found.add(acronym)

    return found


def _get_semantic_cluster(title: str) -> Optional[str]:
    """
    Determine which semantic cluster a title belongs to.

    Args:
        title: Job title

    Returns:
        Cluster name (e.g., "FIRE", "POLICE", "EMS"), or None
    """
    title_lower = title.lower()

    for cluster_name, keywords in SEMANTIC_ROLE_CLUSTERS.items():
        for keyword in keywords:
            if keyword in title_lower:
                return cluster_name

    return None


def check_rank_degradation(original: str, candidate: str) -> bool:
    """
    Check if candidate represents a rank degradation from original.

    Args:
        original: Original title
        candidate: Candidate match

    Returns:
        True if candidate is lower rank (avoid this match), False otherwise
    """
    original_rank = _extract_rank(original)
    candidate_rank = _extract_rank(candidate)

    # If original has clear rank and candidate is significantly lower, reject
    if original_rank > 0 and candidate_rank > 0:
        # Allow small differences (5 points), but block major demotions
        if candidate_rank < original_rank - 10:
            return True

    return False


def check_acronym_protection(original: str, candidate: str) -> bool:
    """
    Check if fuzzy match corrupted a protected acronym.

    Args:
        original: Original title
        candidate: Candidate match

    Returns:
        True if acronym was corrupted (avoid this match), False otherwise
    """
    original_acronyms = _extract_acronyms(original)

    if not original_acronyms:
        return False

    # If original has protected acronym, candidate must preserve it
    for acronym in original_acronyms:
        full_form = PROTECTED_ACRONYMS[acronym]
        # Check if the full form (or acronym) appears in candidate
        if acronym not in candidate.lower() and full_form not in candidate.lower():
            # Acronym was lost in fuzzy match
            return True

    return False


def check_semantic_cluster_conflict(original: str, candidate: str) -> bool:
    """
    Check if original and candidate belong to different semantic clusters.

    Args:
        original: Original title
        candidate: Candidate match

    Returns:
        True if clusters differ (avoid this match), False otherwise
    """
    original_cluster = _get_semantic_cluster(original)
    candidate_cluster = _get_semantic_cluster(candidate)

    # If both have clusters and they differ, it's a conflict
    if original_cluster and candidate_cluster:
        return original_cluster != candidate_cluster

    return False


def get_match_quality_score(original: str, candidate: str, fuzzy_score: float) -> float:
    """
    Compute a quality-adjusted score for a candidate match.

    Factors in:
    - Rank preservation
    - Acronym protection
    - Semantic clustering
    - Original fuzzy score

    Args:
        original: Original title
        candidate: Candidate match
        fuzzy_score: Fuzzy matching score (0-1)

    Returns:
        Adjusted score (0-1), or 0 if match should be rejected
    """
    # Hard rejects
    if check_rank_degradation(original, candidate):
        return 0.0

    if check_acronym_protection(original, candidate):
        return 0.0

    if check_semantic_cluster_conflict(original, candidate):
        return 0.0

    # If we got here, match is acceptable - use original score
    return fuzzy_score
