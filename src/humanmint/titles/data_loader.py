"""
Job title data loader and utilities.

Provides access to canonical job titles and title mappings from the
data folder. Uses compressed JSON caches for fast loads.
"""

import gzip
import json
from pathlib import Path
from typing import Optional
import warnings

# Path to the heuristics cache
DATA_DIR = Path(__file__).parent.parent / "data"
HEURISTICS_CACHE = DATA_DIR / "title_heuristics.json.gz"

# In-memory caches to avoid re-reading the file on every call
_canonical_titles: Optional[list[str]] = None
_canonical_titles_set: Optional[frozenset[str]] = None
_title_mappings: Optional[dict[str, str]] = None
_missing_cache_warned = False


def _load_heuristics_from_cache() -> Optional[tuple[list[str], dict[str, str]]]:
    """Load canonical titles/mappings from a precomputed cache if present."""
    if not HEURISTICS_CACHE.exists():
        return None
    try:
        data = gzip.decompress(HEURISTICS_CACHE.read_bytes())
        payload = json.loads(data.decode("utf-8"))
        canonicals = payload.get("canonicals")
        mappings = payload.get("mappings")
        if isinstance(canonicals, list) and isinstance(mappings, dict):
            return canonicals, mappings
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
                f"Title heuristics cache not found at {HEURISTICS_CACHE}. "
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
