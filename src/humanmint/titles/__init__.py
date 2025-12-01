"""
Job title normalization and matching for HumanMint.

Public API for standardizing and matching job titles against a canonical list.
"""

from .api import TitleResult, normalize_title_full
from .data_loader import (get_all_mappings, get_canonical_titles,
                          get_mapping_for_variant, is_canonical)
from .matching import find_all_matches, find_best_match, get_similarity_score
from .normalize import extract_seniority, normalize_title

__all__ = [
    # Main API
    "normalize_title_full",
    "TitleResult",
    # Core functions
    "normalize_title",
    "extract_seniority",
    "find_best_match",
    "find_all_matches",
    "get_similarity_score",
    # Data access
    "get_canonical_titles",
    "is_canonical",
    "get_mapping_for_variant",
    "get_all_mappings",
]
