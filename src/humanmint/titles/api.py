"""
Public API for job title normalization in HumanMint.

Provides the main normalize_title_full() function that returns a structured
result dictionary with raw, cleaned, and canonical information.
"""

from typing import Optional, TypedDict
from .normalize import normalize_title
from .matching import find_best_match


class TitleResult(TypedDict, total=False):
    """Result structure for title normalization."""
    raw: str
    cleaned: str
    canonical: Optional[str]
    is_valid: bool


def normalize_title_full(
    raw_title: str,
    threshold: float = 0.6,
) -> TitleResult:
    """
    Normalize a job title and return structured result with all details.

    Performs:
    1. Cleaning: Remove noise, codes, parenthetical info, extra whitespace
    2. Matching: Find best canonical title match using heuristics then fuzzy matching

    Example:
        >>> normalize_title_full("Dr. John Smith, CEO 0001 (Finance)")
        {
            "raw": "Dr. John Smith, CEO 0001 (Finance)",
            "cleaned": "CEO",
            "canonical": "CEO",
            "is_valid": True
        }

        >>> normalize_title_full("Senior SW Developer")
        {
            "raw": "Senior SW Developer",
            "cleaned": "Senior Sw Developer",
            "canonical": "Software Developer",
            "is_valid": True
        }

        >>> normalize_title_full("Nonexistent Role")
        {
            "raw": "Nonexistent Role",
            "cleaned": "Nonexistent Role",
            "canonical": None,
            "is_valid": False
        }

    Args:
        raw_title: Raw job title string (may contain names, codes, noise).
        threshold: Minimum similarity score for fuzzy matching (0.0 to 1.0).
                   Defaults to 0.6.

    Returns:
        TitleResult: Dictionary with:
            - raw: Original input
            - cleaned: After normalization (noise removal)
            - canonical: Best matching canonical title, or None
            - is_valid: True if a canonical match was found

    Raises:
        ValueError: If raw_title is empty or threshold is invalid.
    """
    if not raw_title:
        raise ValueError("Job title cannot be empty")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

    # Step 1: Clean the raw title
    try:
        cleaned = normalize_title(raw_title)
    except ValueError:
        # If cleaning fails completely, return partial result
        return {
            "raw": raw_title,
            "cleaned": raw_title,
            "canonical": None,
            "is_valid": False,
        }

    # Step 2: Find best canonical match
    canonical = find_best_match(
        cleaned,
        threshold=threshold,
        normalize=False,  # Already cleaned
    )

    return {
        "raw": raw_title,
        "cleaned": cleaned,
        "canonical": canonical,
        "is_valid": canonical is not None,
    }
