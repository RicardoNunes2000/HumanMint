"""Email processing utilities."""

from .normalize import normalize_email
from .patterns import guess_email, get_pattern_scores, describe_pattern
from .classifier import is_free_provider

__all__ = ["normalize_email", "guess_email", "get_pattern_scores", "describe_pattern", "is_free_provider"]
