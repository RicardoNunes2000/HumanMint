"""
Department processing utilities for HumanMint.

Provides normalization, fuzzy matching, and categorization of department names
with a comprehensive canonical list of standardized departments.

Example:
    >>> from humanmint.departments import normalize_department, find_best_match
    >>> raw_dept = "Public Works 850-123-1234 ext 200"
    >>> normalized = normalize_department(raw_dept)
    >>> normalized
    "Public Works"
    >>> matched = find_best_match("PW Dept")
    >>> matched
    "Public Works"
"""

from .normalize import normalize_department
from .matching import (
    find_best_match,
    find_all_matches,
    match_departments,
    get_similarity_score,
)
from .categories import (
    get_department_category,
    get_all_categories,
    get_departments_by_category,
    categorize_departments,
)
from .data_loader import (
    CANONICAL_DEPARTMENTS,
    get_canonical_departments,
    is_canonical,
    load_mappings,
    get_mapping_for_original,
    get_originals_for_canonical,
)

__all__ = [
    # Normalization
    "normalize_department",
    # Matching
    "find_best_match",
    "find_all_matches",
    "match_departments",
    "get_similarity_score",
    # Categories
    "get_department_category",
    "get_all_categories",
    "get_departments_by_category",
    "categorize_departments",
    # Data & Mappings
    "CANONICAL_DEPARTMENTS",
    "get_canonical_departments",
    "is_canonical",
    "load_mappings",
    "get_mapping_for_original",
    "get_originals_for_canonical",
]
