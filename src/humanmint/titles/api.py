"""
Public API for job title normalization in HumanMint.

Provides the main normalize_title_full() function that returns a structured
result dictionary with raw, cleaned, and canonical information.
"""

from typing import Dict, Optional, TypedDict

from .matching import find_best_match
from .normalize import extract_seniority, normalize_title
from .normalize import re as _re


class TitleResult(TypedDict, total=False):
    """Result structure for title normalization."""
    raw: str
    cleaned: str
    canonical: Optional[str]
    is_valid: bool
    confidence: float


def normalize_title_full(
    raw_title: str,
    threshold: float = 0.6,
    dept_canonical: Optional[str] = None,
    overrides: Optional[Dict[str, str]] = None,
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

    # Step 1b: Reject if cleaned title is mostly symbols (no meaningful alphanumeric content)
    # Count alphanumeric characters vs total length
    if cleaned:
        alphanumeric_count = sum(1 for c in cleaned if c.isalnum())
        total_count = len(cleaned)
        # If less than 40% alphanumeric (more than 60% symbols), reject as invalid
        if total_count > 0 and alphanumeric_count / total_count < 0.4:
            return {
                "raw": raw_title,
                "cleaned": cleaned,
                "canonical": None,
                "is_valid": False,
            }

    # Step 2: Apply overrides if provided
    canonical = None
    confidence = 0.0
    special_cases = {
        "clerk of the works": ("clerk of the works", 0.98),
    }
    cleaned_lower = cleaned.lower()
    if cleaned_lower in special_cases:
        canonical, confidence = special_cases[cleaned_lower]
    elif "clerk" in cleaned_lower and "works" in cleaned_lower:
        canonical, confidence = ("clerk of the works", 0.95)

    if overrides:
        overrides_lower = {k.lower(): v for k, v in overrides.items()}
        if cleaned_lower in overrides_lower:
            canonical = overrides_lower[cleaned_lower]
            confidence = 0.98

    cleaned_for_valid = cleaned

    # Step 3: Find best canonical match
    if canonical is None:
        canonical, confidence = find_best_match(
            cleaned,
            threshold=threshold,
            normalize=False,  # Already cleaned
            dept_canonical=dept_canonical,
        )
        # Fallback: if we have chained roles separated by "/", try each segment
        if canonical is None and "/" in cleaned:
            best_canon = None
            best_conf = 0.0
            segments = [seg.strip() for seg in cleaned.split("/") if seg.strip()]
            primary_segment = segments[0] if segments else cleaned
            for seg in segments:
                seg_canon, seg_conf = find_best_match(
                    seg,
                    threshold=threshold,
                    normalize=False,
                    dept_canonical=dept_canonical,
                )
                if seg_canon and seg_conf > best_conf:
                    best_canon = seg_canon
                    best_conf = seg_conf
            if best_canon:
                canonical = best_canon
                confidence = best_conf
            elif segments:
                # Use the primary segment for heuristic validation
                cleaned_for_valid = primary_segment

        # Promotion bug guard: if we matched a head-of-org role ("mayor", "governor", "president")
        # from a chain that also contains a chief-of-staff pattern, prefer the chief-of-staff canonical.
        if canonical in {"mayor", "governor", "president"} and "chief of staff" in cleaned.lower():
            canonical = "chief of staff"
            confidence = max(confidence, 0.9)

    # Functional heuristics to mark common job patterns as valid even without canonical
    seniority_tokens = {
        "assistant",
        "associate",
        "senior",
        "deputy",
        "chief",
        "lead",
        "principal",
    }
    functional_tokens = {
        "planner",
        "analyst",
        "coordinator",
        "administrator",
        "admin",
        "specialist",
        "technician",
        "tech",
        "manager",
        "director",
        "officer",
        "supervisor",
        "investigator",
        "engineer",
        "program",
        "housing",
        "business",
        "development",
        "operations",
        "ops",
        "generalist",
        "captain",
        "sergeant",
        "lieutenant",
        "treasurer",
        "patrol",
    }

    tokens = [t.lower().strip(".") for t in _re.split(r"[\s/]+", cleaned_for_valid) if t]
    has_functional = any(t in functional_tokens for t in tokens)
    has_seniority = any(t in seniority_tokens for t in tokens)

    if canonical is None and confidence == 0.0 and (has_functional or has_seniority):
        confidence = 0.6

    # Only mark as valid if we have an actual canonical match OR (has functional/seniority AND confidence > 0)
    # Don't use heuristics to override explicit "no match" (confidence == 0.0 from hallucination detection)
    is_valid = canonical is not None or (confidence > 0.0 and (has_functional or has_seniority))

    # Ignore Roman numerals for validity decisions; keep canonical None if not matched
    canonical_value = canonical if canonical else (cleaned_for_valid if is_valid else None)

    # If dept is sheriff, avoid mapping to police-specific canonicals
    if dept_canonical and canonical_value:
        if dept_canonical.lower().startswith("sheriff") and "police" in canonical_value.lower():
            canonical_value = cleaned

    # Contextual fallback/override: rank-only titles paired with dept clues
    if dept_canonical:
        dept_low = dept_canonical.lower()
        cleaned_tokens = [t.lower() for t in cleaned.split() if t]
        rank_map = {
            "captain": "captain",
            "lt": "lieutenant",
            "lieutenant": "lieutenant",
            "sgt": "sergeant",
            "sergeant": "sergeant",
            "marshal": "marshal",
            "chief": "chief",
        }
        if len(cleaned_tokens) == 1 and cleaned_tokens[0] in rank_map:
            rank = rank_map[cleaned_tokens[0]]
            contextual = None
            if "fire" in dept_low:
                contextual = f"fire {rank}"
            elif "police" in dept_low or "public safety" in dept_low:
                contextual = f"police {rank}"
            elif "sheriff" in dept_low:
                contextual = f"sheriff {rank}"
            if contextual:
                canonical = contextual
                confidence = max(confidence, 0.9)

    # Allow certain titles as valid canonicals even without match
    fallback_titles = {
        "paralegal",
        "epidemiologist",
        "records clerk",
        "administrative aide",
    }
    cleaned_lower = cleaned.lower()
    if canonical is None and cleaned_lower in fallback_titles:
        canonical_value = cleaned_lower
        is_valid = True
        confidence = max(confidence, 0.9)

    # Recompute canonical_value after any contextual overrides
    canonical_value = canonical if canonical else (cleaned if is_valid else None)

    # Canonical should always be lowercase for consistency with canonical titles database
    if isinstance(canonical_value, str):
        canonical_value = canonical_value.lower()

    # Ensure confidence is non-zero when we have a canonical value
    if canonical_value and confidence == 0.0:
        confidence = 0.7

    # Extract seniority level from the cleaned title
    seniority = extract_seniority(cleaned)

    return {
        "raw": raw_title,
        "cleaned": cleaned,
        "canonical": canonical_value,
        "is_valid": is_valid,
        "confidence": float(confidence if canonical_value else 0.0),
        "seniority": seniority,
    }
