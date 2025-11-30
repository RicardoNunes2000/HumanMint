"""Email processing utilities."""

from .classifier import is_free_provider
from .normalize import normalize_email
from .patterns import describe_pattern, get_pattern_scores, guess_email

__all__ = ["normalize_email", "guess_email", "get_pattern_scores", "describe_pattern", "is_free_provider"]
