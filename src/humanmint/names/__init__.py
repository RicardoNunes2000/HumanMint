"""Name processing utilities."""

from .enrichment import enrich_name, infer_gender
from .matching import (compare_first_names, compare_last_names,
                       detect_nickname, get_name_equivalents,
                       get_nickname_variants, match_names)
from .normalize import normalize_name

__all__ = [
    "normalize_name",
    "detect_nickname",
    "get_nickname_variants",
    "get_name_equivalents",
    "compare_first_names",
    "compare_last_names",
    "match_names",
    "infer_gender",
    "enrich_name",
]
