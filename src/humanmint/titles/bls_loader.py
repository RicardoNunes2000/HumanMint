"""
BLS Occupational Outlook Handbook (OOH) title data loader.

Loads 4,800+ official job titles from the U.S. Department of Labor
Bureau of Labor Statistics and provides lookup functionality for
canonical title matching.
"""

import orjson
from functools import lru_cache
from typing import Dict, Optional, Set


@lru_cache(maxsize=1)
def _load_bls_titles() -> Dict[str, Dict]:
    """
    Load BLS job titles from gzipped JSON cache.

    Loads 4,800+ official job titles from the U.S. Department of Labor
    Bureau of Labor Statistics Occupational Outlook Handbook (OOH).

    Returns:
        Dictionary mapping lowercase job titles to metadata.
        Cached in memory for fast repeated access.

    Example:
        >>> titles = _load_bls_titles()
        >>> titles.get("software developer")
        {
            'raw': 'Software Developer',
            'canonical': 'Software Developers',
            'category': 'Computer And Information Technology',
            'subcategory': '...'
        }
    """
    import gzip

    # Use importlib.resources for cross-platform data file access
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files  # type: ignore

    try:
        # Load from gzipped JSON (90% compression ratio)
        package = files("humanmint.data")
        data_file = package.joinpath("bls_titles.json.gz")
        content = gzip.decompress(data_file.read_bytes()).decode("utf-8")
        data = orjson.loads(content)
        return data.get("titles", {})
    except Exception:
        # Fallback if file doesn't exist (graceful degradation)
        return {}


def lookup_bls_title(raw_title: str) -> Optional[Dict]:
    """
    Look up a job title in the BLS database.

    Attempts exact match after normalization (lowercase, whitespace trim).
    Returns the BLS record if found, None otherwise.

    Args:
        raw_title: The job title to look up.

    Returns:
        Dictionary with canonical, category, subcategory if found.
        None if not in BLS database.

    Example:
        >>> lookup_bls_title("Software Developer")
        {
            'raw': 'Software Developer',
            'canonical': 'Software Developers',
            'category': 'Computer And Information Technology',
            'subcategory': 'Software Developers'
        }
    """
    if not raw_title:
        return None

    bls_titles = _load_bls_titles()
    lookup_key = raw_title.lower().strip()

    return bls_titles.get(lookup_key)


def get_bls_category(raw_title: str) -> Optional[str]:
    """
    Get the BLS occupational category for a job title.

    Useful for enriching title normalization with occupational context.

    Args:
        raw_title: The job title.

    Returns:
        BLS category name (e.g., "Computer And Information Technology")
        or None if not found.

    Example:
        >>> get_bls_category("Software Developer")
        'Computer And Information Technology'
    """
    record = lookup_bls_title(raw_title)
    return record.get("category") if record else None


def get_all_bls_titles() -> Set[str]:
    """
    Get all job titles in the BLS database (lowercase).

    Useful for checking if a title exists in BLS.

    Returns:
        Set of all job titles (lowercase) in database.

    Example:
        >>> all_titles = get_all_bls_titles()
        >>> "software developer" in all_titles
        True
    """
    bls_titles = _load_bls_titles()
    return set(bls_titles.keys())


def get_bls_stats() -> Dict:
    """
    Get statistics about the BLS title database.

    Returns:
        Dictionary with:
        - total: Number of job titles
        - categories: Number of occupational categories
        - example: Sample title record
    """
    bls_titles = _load_bls_titles()
    categories = set()

    for record in bls_titles.values():
        if "category" in record:
            categories.add(record["category"])

    # Get first example
    example = next(iter(bls_titles.values())) if bls_titles else None

    return {
        "total": len(bls_titles),
        "categories": len(categories),
        "example": example,
    }
