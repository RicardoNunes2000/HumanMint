"""
Job title normalization and matching for HumanMint.

Public API for standardizing and matching job titles against a canonical list.
"""

from .api import normalize_title_full, TitleResult
from .normalize import normalize_title
from .matching import (
    find_best_match,
    find_all_matches,
    get_similarity_score,
)
from .data_loader import (
    get_canonical_titles,
    is_canonical,
    get_mapping_for_variant,
    get_all_mappings,
)

__all__ = [
    # Main API
    "normalize_title_full",
    "TitleResult",
    # Core functions
    "normalize_title",
    "find_best_match",
    "find_all_matches",
    "get_similarity_score",
    # Data access
    "get_canonical_titles",
    "is_canonical",
    "get_mapping_for_variant",
    "get_all_mappings",
]
