"""
Job title fuzzy matching for HumanMint.

Fuzzy matching engine to find the best canonical job title match for
normalized job titles using similarity scoring.

Strategy:
1. Check if already canonical (O(1))
2. Check heuristics mappings for exact match (O(1))
3. Check for substring match with canonicals (O(n))
4. Fall back to fuzzy matching with rapidfuzz (O(n*m) but fast)
"""

from functools import lru_cache
from typing import Optional
from rapidfuzz import fuzz, process
from .data_loader import (
    get_canonical_titles,
    get_mapping_for_variant,
    is_canonical,
)
from .normalize import normalize_title
from .bls_loader import lookup_bls_title

# Cache canonical titles and lowercase versions for matching
_canonical_lowers: Optional[list[tuple[str, str]]] = None
_GENERIC_TITLE_TOKENS = {
    "manager",
    "director",
    "administrator",
    "admin",
    "analyst",
    "specialist",
    "technician",
    "tech",
    "coordinator",
    "officer",
    "supervisor",
    "consultant",
    "advisor",
    "assistant",
    "associate",
    "lead",
    "program",
}


def _get_canonical_lowers() -> list[tuple[str, str]]:
    """Cache canonical titles with their lowercase versions."""
    global _canonical_lowers
    if _canonical_lowers is None:
        canonicals = get_canonical_titles()
        _canonical_lowers = [(c, c.lower()) for c in canonicals]
    return _canonical_lowers


def _should_skip_generic_expansion(search_title: str, candidate: str, dept_canonical: Optional[str]) -> bool:
    """
    Check if a generic term should be expanded based on department context.

    Generic terms like "coordinator" should only expand to specific titles
    (e.g., "recreation coordinator") if the department context supports it.
    Without context, keep the generic term.

    Args:
        search_title: The cleaned/normalized title
        candidate: The fuzzy match candidate
        dept_canonical: The canonical department name (optional)

    Returns:
        bool: True if we should skip this expansion due to lack of context
    """
    search_lower = search_title.lower()
    cand_lower = candidate.lower()

    # If search title is a single generic term and candidate adds specificity,
    # check if the specificity makes sense for the department
    if " " not in search_lower and " " in cand_lower:
        # E.g., "coordinator" -> "recreation coordinator"
        # Only allow if dept context supports it
        generic_term = search_lower

        # List of departments that support specific coordinator types
        supported_coords = {
            "recreation": {"recreation", "parks"},
            "planning": {"planning"},
            "human resources": {"human resources", "hr"},
        }

        if generic_term == "coordinator":
            # If no dept context at all, skip the expansion
            if not dept_canonical:
                return True

            dept_low = dept_canonical.lower()
            for spec_type, dept_keywords in supported_coords.items():
                if any(kw in dept_low for kw in dept_keywords):
                    # Dept supports this type of coordinator
                    return False
            # Dept doesn't support this coordinator expansion
            return True

    return False


@lru_cache(maxsize=4096)
def _find_best_match_normalized_cached(
    search_title: str,
    threshold: float,
) -> tuple[Optional[str], float]:
    """
    Cached core matcher for already-normalized titles (without dept context).

    This function uses @lru_cache(maxsize=4096) to cache fuzzy matching results.
    For large batches with repeated job titles, caching avoids redundant fuzzy
    matching computations against the canonical title set.

    To clear the cache if memory is a concern:
        >>> _find_best_match_normalized_cached.cache_clear()

    To check cache statistics:
        >>> _find_best_match_normalized_cached.cache_info()
    """
    search_title_lower = search_title.lower()

    # Strategy 1: Check if already canonical (O(1))
    if is_canonical(search_title):
        return search_title, 1.0

    # Strategy 2: Check BLS official titles (4,800+ from DOL) (O(1))
    # BLS titles take priority over heuristics since they're official government data
    bls_record = lookup_bls_title(search_title)
    if bls_record:
        canonical = bls_record.get("canonical", search_title)
        return canonical, 0.995  # Highest confidence - official DOL data

    # Strategy 3: Check heuristics mappings for exact match (O(1))
    mapped = get_mapping_for_variant(search_title)
    if mapped:
        return mapped, 0.95  # High confidence but lower than BLS

    # Strategy 4: Check for substring match with canonical titles
    # e.g., "Senior Software Developer" contains "Software Developer"
    # BUT: Single-word searches (e.g., "Manager", "Director") should only match
    # single-word canonicals or variations via heuristics, not arbitrary multi-word titles
    canonical_lowers = _get_canonical_lowers()
    matches = []
    search_tokens = search_title_lower.split()
    is_single_word = len(search_tokens) == 1

    for canonical, canonical_lower in canonical_lowers:
        if canonical_lower in search_title_lower or search_title_lower in canonical_lower:
            # Guard: single-word searches should only match single-word canonicals
            # This prevents "Manager" from matching "Deputy City Manager" or
            # "Director" from matching "Information Technology Director"
            if is_single_word:
                canon_tokens = canonical_lower.split()
                if len(canon_tokens) > 1:
                    # Don't match single-word searches to multi-word canonicals via substring
                    # (multi-word matches should come from heuristics or fuzzy matching)
                    continue

            # Score: how early in the search string does this appear?
            # Prefer early matches and longer canonical names for specificity
            position = search_title_lower.find(canonical_lower)
            score = (-position, len(canonical))  # Negative position = earlier = higher score
            matches.append((score, canonical))

    if matches:
        # Return the best match (earliest appearance, then longest)
        best = max(matches, key=lambda x: x[0])[1]
        return best, 0.9

    # Strategy 5: Find close matches using rapidfuzz (fallback)
    canonicals = get_canonical_titles()
    score_cutoff = threshold * 100
    result = process.extractOne(
        search_title,
        canonicals,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=score_cutoff,
    )

    if not result:
        return None, 0.0

    candidate = result[0]
    score = result[1] / 100.0 if len(result) > 1 else 0.0

    # Guard: if fuzzy score is weak (<0.75), consider it too risky
    if score < 0.75:
        return None, score
    search_tokens = {t for t in search_title_lower.split() if t}
    cand_tokens = {t for t in candidate.lower().split() if t}

    # Require overlap on at least one non-generic token to avoid cross-domain matches
    meaningful_overlap = {
        t for t in search_tokens.intersection(cand_tokens) if t not in _GENERIC_TITLE_TOKENS
    }
    if meaningful_overlap:
        return candidate, score

    return None, score


def _find_best_match_normalized(
    search_title: str,
    threshold: float,
    dept_canonical: Optional[str] = None,
) -> tuple[Optional[str], float]:
    """
    Core matcher for already-normalized titles with optional department context.

    Wraps the cached version and applies context-aware filtering for generic terms.

    Args:
        search_title: Already-normalized job title.
        threshold: Minimum similarity score (0.0 to 1.0).
        dept_canonical: Optional canonical department for context-aware matching.

    Returns:
        tuple[Optional[str], float]: (canonical_title, confidence_score)
    """
    # Get the cached result (without dept context)
    candidate, score = _find_best_match_normalized_cached(search_title, threshold)

    if not candidate:
        return candidate, score

    # Check if we should skip generic expansion
    # This happens when:
    # 1. dept_canonical is None (no context) and it's a generic expansion
    # 2. dept_canonical is provided but doesn't support this expansion
    if _should_skip_generic_expansion(search_title, candidate, dept_canonical):
        # Skip this expansion - return no match
        return None, score

    return candidate, score


def find_best_match(
    job_title: str,
    threshold: float = 0.6,
    normalize: bool = True,
    dept_canonical: Optional[str] = None,
) -> tuple[Optional[str], float]:
    """
    Find the best canonical job title match for a given title.

    Uses rapidfuzz to find fuzzy matches against the canonical title list. If the input
    is not already normalized, it will be normalized first.

    Example:
        >>> find_best_match("Dr. Senior Software Engineer")
        "Software Engineer"
        >>> find_best_match("SW Dev", threshold=0.6)
        "Software Developer"
        >>> find_best_match("Nonexistent Role", threshold=0.6)
        None

    Args:
        job_title: Job title to match (raw or normalized).
        threshold: Minimum similarity score (0.0 to 1.0). Defaults to 0.6.
        normalize: Whether to normalize the input first. Defaults to True.
        dept_canonical: Canonical department name for context (optional).
                       Used to prevent inappropriate generic term expansions.

    Returns:
        Optional[str]: Best matching canonical job title, or None if no
                      match exceeds the threshold.

    Raises:
        ValueError: If job_title is empty.
        ValueError: If threshold is not between 0.0 and 1.0.
    """
    if not job_title:
        raise ValueError("Job title cannot be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    # Normalize the input if requested
    try:
        search_title = normalize_title(job_title) if normalize else job_title
    except ValueError:
        # If normalization fails, return None
        return None, 0.0

    return _find_best_match_normalized(search_title, threshold, dept_canonical)


def find_all_matches(
    job_title: str,
    threshold: float = 0.6,
    top_n: int = 3,
    normalize: bool = True,
) -> list[str]:
    """
    Find all canonical job title matches above a similarity threshold.

    Returns multiple matches ranked by similarity score, useful for
    interactive selection or validation.

    Example:
        >>> find_all_matches("Senior Developer", threshold=0.5, top_n=3)
        ["Software Developer", "Software Engineer"]

    Args:
        job_title: Job title to match (raw or normalized).
        threshold: Minimum similarity score (0.0 to 1.0). Defaults to 0.6.
        top_n: Maximum number of matches to return. Defaults to 3.
        normalize: Whether to normalize the input first. Defaults to True.

    Returns:
        list[str]: List of matching canonical job titles, ranked by
                   similarity. Empty list if no matches exceed the threshold.

    Raises:
        ValueError: If job_title is empty.
        ValueError: If threshold is not between 0.0 and 1.0.
    """
    if not job_title:
        raise ValueError("Job title cannot be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    # Normalize the input if requested
    try:
        search_title = normalize_title(job_title) if normalize else job_title
    except ValueError:
        return []

    # Check if already canonical
    if is_canonical(search_title):
        return [search_title]

    # Find all close matches
    canonicals = get_canonical_titles()
    score_cutoff = threshold * 100
    matches = process.extract(
        search_title,
        canonicals,
        scorer=fuzz.token_sort_ratio,
        limit=top_n,
        score_cutoff=score_cutoff,
    )

    return [m[0] for m in matches]


def get_similarity_score(title1: str, title2: str) -> float:
    """
    Calculate similarity score between two job titles.

    Uses rapidfuzz token_sort_ratio to compute a similarity ratio between
    0.0 (completely different) and 1.0 (identical).

    Example:
        >>> get_similarity_score("Software Developer", "Software Developer")
        1.0
        >>> get_similarity_score("Software Developer", "Software Engineer")
        0.8...

    Args:
        title1: First job title.
        title2: Second job title.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    if not title1 or not title2:
        return 0.0

    score = fuzz.token_sort_ratio(title1.lower(), title2.lower())
    return score / 100.0
