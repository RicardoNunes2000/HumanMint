"""
Job title data loader and utilities.

Provides access to:
- Canonical job titles (curated standardized 133 titles)
- Title heuristic mappings
- 73k+ real job titles from government data (job-titles.txt)

Uses compressed JSON caches for fast loads.
"""

import warnings
from typing import Optional

from humanmint.data.utils import load_package_json_gz

# In-memory caches to avoid re-reading the file on every call
_canonical_titles: Optional[list[str]] = None
_canonical_titles_set: Optional[frozenset[str]] = None
_title_mappings: Optional[dict[str, str]] = None
_job_titles: Optional[list[str]] = None
_job_titles_set: Optional[frozenset[str]] = None
_job_titles_by_first_char: Optional[dict[str, list[str]]] = (
    None  # Pre-indexed for faster fuzzy matching
)
_missing_cache_warned = False


def _load_heuristics_from_cache() -> Optional[tuple[list[str], dict[str, str]]]:
    """Load canonical titles/mappings from a precomputed cache if present."""
    try:
        payload = load_package_json_gz("title_heuristics.json.gz")
        canonicals = payload.get("canonicals")
        mappings = payload.get("mappings")
        if isinstance(canonicals, list) and isinstance(mappings, dict):
            return canonicals, mappings
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None


def _build_caches() -> None:
    """Load and cache canonical titles and mappings (idempotent)."""
    global _canonical_titles, _canonical_titles_set, _title_mappings
    global _missing_cache_warned

    if _canonical_titles is not None:
        return

    loaded = _load_heuristics_from_cache()
    if loaded:
        canonicals, mappings = loaded
    else:
        if not _missing_cache_warned:
            warnings.warn(
                "Title heuristics cache (title_heuristics.json.gz) not found. "
                "Run scripts/build_caches.py to generate it.",
                RuntimeWarning,
            )
            _missing_cache_warned = True
        canonicals, mappings = [], {}

    _canonical_titles = canonicals
    _canonical_titles_set = frozenset(canonicals)
    _title_mappings = mappings


def get_canonical_titles() -> list[str]:
    """
    Get the complete list of canonical job titles.

    Returns:
        list[str]: Sorted list of all standardized job titles.
    """
    _build_caches()
    return sorted(_canonical_titles) if _canonical_titles else []  # type: ignore[return-value]


def is_canonical(title: str) -> bool:
    """
    Check if a job title is already canonical.

    Args:
        title: Job title to check.

    Returns:
        bool: True if the title is in the canonical list.
    """
    _build_caches()
    return title in _canonical_titles_set if _canonical_titles_set else False


def get_mapping_for_variant(variant_title: str) -> Optional[str]:
    """
    Get the canonical job title for a variant.

    Args:
        variant_title: Variant or canonical job title.

    Returns:
        Optional[str]: Canonical job title, or None if not found.
    """
    _build_caches()
    if not _title_mappings:
        return None
    return _title_mappings.get(variant_title.lower())


def get_all_mappings() -> dict[str, str]:
    """
    Get the complete mapping dictionary.

    Returns:
        dict[str, str]: Mapping of all variants (lowercase) to canonical titles.
    """
    _build_caches()
    return _title_mappings.copy() if _title_mappings else {}  # type: ignore[return-value]


# Job titles database functions (73k+ real job titles)


def _load_job_titles_from_cache() -> Optional[dict]:
    """Load job titles from compressed JSON cache."""
    try:
        return load_package_json_gz("job_titles.json.gz")
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _build_job_titles_cache() -> None:
    """Load and cache job titles with pre-indexing for fast fuzzy matching (idempotent)."""
    global _job_titles, _job_titles_set, _job_titles_by_first_char

    if _job_titles is not None:
        return

    loaded = _load_job_titles_from_cache()
    if loaded:
        _job_titles = loaded.get("titles", [])
    else:
        _job_titles = []

    _job_titles_set = frozenset(_job_titles)

    # Pre-index titles by first character for faster fuzzy matching
    # This reduces search space from 73k to ~3k titles per query (25x speedup)
    _job_titles_by_first_char = {}
    for title in _job_titles:
        if title:
            first_char = title[0].lower()
            if first_char not in _job_titles_by_first_char:
                _job_titles_by_first_char[first_char] = []
            _job_titles_by_first_char[first_char].append(title)


def get_all_job_titles() -> list[str]:
    """
    Get all 73k+ real job titles from government data.

    Returns:
        list[str]: Sorted list of all job titles in lowercase.
    """
    _build_job_titles_cache()
    return _job_titles.copy() if _job_titles else []  # type: ignore[return-value]


def get_job_titles_set() -> frozenset[str]:
    """
    Get all job titles as a frozenset for O(1) lookup.

    Returns:
        frozenset[str]: Set of all job titles.
    """
    _build_job_titles_cache()
    return _job_titles_set if _job_titles_set else frozenset()


def find_exact_job_title(title: str) -> Optional[str]:
    """
    Find exact match for a job title (case-insensitive, whitespace-trimmed).

    Args:
        title: Job title to search for.

    Returns:
        str: Exact matching title if found, None otherwise.

    Example:
        >>> find_exact_job_title("Software Developer")
        "software developer"
        >>> find_exact_job_title("Nonexistent Role")
        None
    """
    if not title:
        return None

    search_key = title.lower().strip()
    job_titles_set = get_job_titles_set()

    return search_key if search_key in job_titles_set else None


def find_similar_job_titles(
    title: str,
    top_n: int = 5,
    min_length: int = 0,
) -> list[tuple[str, float]]:
    """
    Find similar job titles using fuzzy matching.

    Args:
        title: Job title to search for.
        top_n: Maximum number of results to return. Defaults to 5.
        min_length: Filter out matches shorter than this. Defaults to 0 (no filter).

    Returns:
        list[tuple[str, float]]: List of (title, score) tuples sorted by score.
                                 Score is between 0.0 and 1.0.

    Example:
        >>> find_similar_job_titles("Dvr", top_n=3)
        [("driver", 0.92), ("diver", 0.88), ...]
    """
    if not title:
        return []

    from rapidfuzz import fuzz, process

    search_title = title.lower().strip()
    all_titles = get_all_job_titles()

    # Use token_sort_ratio for better matching of reordered terms
    matches = process.extract(
        search_title,
        all_titles,
        scorer=fuzz.token_sort_ratio,
        limit=top_n * 2,  # Get extra to filter by min_length
        score_cutoff=60,  # Return matches above 60%
    )

    # Convert scores to 0-1 range and filter by min_length if requested
    # rapidfuzz returns (string, score) or (string, score, index) tuples
    converted = []
    for match in matches:
        if len(match) >= 2:
            title_match = match[0]
            score = match[1] / 100.0
            if min_length == 0 or len(title_match) >= min_length:
                converted.append((title_match, score))

    return converted[:top_n]


def get_job_titles_by_keyword(keyword: str) -> list[str]:
    """
    Get all job titles containing a specific keyword.

    Args:
        keyword: Keyword to search for (case-insensitive).

    Returns:
        list[str]: List of matching titles.

    Example:
        >>> get_job_titles_by_keyword("driver")
        ["driver", "bus driver", "cab driver", ...]
    """
    if not keyword:
        return []

    search_key = keyword.lower()
    all_titles = get_all_job_titles()

    return [t for t in all_titles if search_key in t]


def map_to_canonical(job_title: str) -> Optional[str]:
    """
    Map a job title (from job-titles.txt) to a canonical title (from 133-title list).

    Uses fuzzy matching against the canonical titles to find the best standardized form.
    For example: "driver" → might map to "driver" or stay as-is if no good match exists.

    Args:
        job_title: A title from the job-titles.txt database.

    Returns:
        Canonical title if a good match found, None otherwise.

    Example:
        >>> map_to_canonical("chief of police")
        "police chief"
        >>> map_to_canonical("driver")
        None  # (driver might not be in canonical list)
    """
    if not job_title:
        return None

    from rapidfuzz import fuzz, process

    canonicals = get_canonical_titles()
    if not canonicals:
        return None

    # Try to find a canonical that matches this job title
    # Use token_sort_ratio for flexible matching
    result = process.extractOne(
        job_title.lower(),
        canonicals,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=80,  # Only match if similarity >= 80%
    )

    if result:
        return result[0]  # Return the canonical title

    return None
