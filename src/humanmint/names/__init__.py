"""Name processing utilities."""

from .normalize import normalize_name
from .matching import (
    detect_nickname,
    get_nickname_variants,
    get_name_equivalents,
    compare_first_names,
    compare_last_names,
    match_names,
)
from .enrichment import infer_gender, enrich_name

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
