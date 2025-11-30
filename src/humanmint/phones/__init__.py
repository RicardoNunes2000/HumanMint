"""Phone number processing utilities."""

from .detect import detect_fax_pattern, detect_impossible, detect_voip_pattern
from .normalize import normalize_phone

__all__ = [
    "normalize_phone",
    "detect_impossible",
    "detect_fax_pattern",
    "detect_voip_pattern",
]
