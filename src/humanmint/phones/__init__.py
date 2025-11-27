"""Phone number processing utilities."""

from .normalize import normalize_phone
from .detect import detect_impossible, detect_fax_pattern, detect_voip_pattern

__all__ = [
    "normalize_phone",
    "detect_impossible",
    "detect_fax_pattern",
    "detect_voip_pattern",
]
