"""
Email pattern detection and guessing for HumanMint.

Analyzes known email-to-name mappings to detect organizational email conventions
and generates likely email addresses for new individuals.
"""

from typing import List, Tuple, Dict, Optional
from collections import Counter

from .normalize import normalize_email
from ._pattern_definitions import PATTERNS


# ============================================================================
# NAME PARSING
# ============================================================================


def _parse_name(name: str) -> Optional[Dict[str, str]]:
    """
    Parse a full name into components.

    Args:
        name: Full name (e.g., "Alice Johnson" or "Jane Marie Doe").

    Returns:
        Dict with 'first' and 'last' keys, or None if parsing fails.
        For names with 3+ parts, 'first' is the first word and 'last' is the last word.
    """
    if not name or not isinstance(name, str):
        return None

    parts = name.strip().split()
    if len(parts) < 2:
        return None

    return {"first": parts[0].lower(), "last": parts[-1].lower()}


def _generate_local_variants(first: str, last: str) -> Dict[str, str]:
    """
    Generate all possible email local parts for a given name.

    Args:
        first: First name (lowercase).
        last: Last name (lowercase).

    Returns:
        Dict mapping pattern ID to generated local part.
    """
    return {
        "f_l": f"{first[0]}_{last}",
        "fl": f"{first[0]}{last}",
        "f.l": f"{first[0]}.{last}",
        "f-l": f"{first[0]}-{last}",
        "first_last": f"{first}_{last}",
        "first.last": f"{first}.{last}",
        "first-last": f"{first}-{last}",
        "firstlast": f"{first}{last}",
        "l_f": f"{last}_{first[0]}",
        "lf": f"{last}{first[0]}",
        "l.f": f"{last}.{first[0]}",
        "last_first": f"{last}_{first}",
        "last.first": f"{last}.{first}",
    }


# ============================================================================
# PATTERN DETECTION
# ============================================================================


def _extract_local_part(email: str) -> Optional[str]:
    """
    Extract the local part (before @) from an email address.

    Args:
        email: Email address.

    Returns:
        Local part in lowercase, or None if invalid.
    """
    normalized = normalize_email(email)
    if not normalized["is_valid"]:
        return None
    return normalized["local"].lower()


def _detect_pattern(name: str, email: str) -> Optional[str]:
    """
    Detect which pattern matches a given name-email pair.

    Args:
        name: Full name.
        email: Email address.

    Returns:
        Pattern ID (e.g., "f_l", "first.last") if match found, None otherwise.
    """
    parsed = _parse_name(name)
    if not parsed:
        return None

    local = _extract_local_part(email)
    if not local:
        return None

    variants = _generate_local_variants(parsed["first"], parsed["last"])

    for pattern_id, variant in variants.items():
        if variant == local:
            return pattern_id

    return None


def _analyze_patterns(
    known: List[Tuple[str, str]]
) -> Tuple[Dict[str, int], int]:
    """
    Analyze a list of known (name, email) pairs to detect patterns.

    Args:
        known: List of (name, email) tuples.

    Returns:
        Tuple of (pattern_counts, total_valid):
        - pattern_counts: Dict mapping pattern ID to frequency
        - total_valid: Number of successfully parsed pairs
    """
    pattern_counts = Counter()
    total_valid = 0

    for name, email in known:
        pattern = _detect_pattern(name, email)
        if pattern:
            pattern_counts[pattern] += 1
            total_valid += 1

    return dict(pattern_counts), total_valid


# ============================================================================
# EMAIL GENERATION
# ============================================================================


def _generate_email_variants(
    name: str, domain: str
) -> Optional[Dict[str, str]]:
    """
    Generate email variants for a given name across all patterns.

    Args:
        name: Full name.
        domain: Email domain (e.g., "acme.com").

    Returns:
        Dict mapping pattern ID to full email address, or None if name parsing fails.
    """
    parsed = _parse_name(name)
    if not parsed:
        return None

    variants = _generate_local_variants(parsed["first"], parsed["last"])
    return {pattern_id: f"{local}@{domain}" for pattern_id, local in variants.items()}


# ============================================================================
# PUBLIC API
# ============================================================================


def guess_email(
    name: str, domain: str, known: List[Tuple[str, str]]
) -> str:
    """
    Guess the most likely email address for a person based on organizational patterns.

    Analyzes known (name, email) pairs to detect the organization's email naming
    convention, then applies the most common pattern to generate an email for the
    new person.

    Args:
        name: Full name of the person (e.g., "Jonathan Smith").
        domain: Email domain (e.g., "acme.com").
        known: List of (name, email) tuples representing known employees.
               Example: [("Alice Johnson", "ajohnson@acme.com"), ...]

    Returns:
        Best-guess email address as a string (e.g., "jsmith@acme.com").
        Returns empty string if no pattern could be detected or name is invalid.

    Examples:
        >>> guess_email(
        ...     name="Jonathan Smith",
        ...     domain="acme.com",
        ...     known=[
        ...         ("Alice Johnson", "ajohnson@acme.com"),
        ...         ("Mark Stone", "mstone@acme.com"),
        ...     ]
        ... )
        "jsmith@acme.com"
    """
    if not name or not domain or not known:
        return ""

    # Detect patterns from known emails
    pattern_counts, total_valid = _analyze_patterns(known)

    if not pattern_counts or total_valid == 0:
        return ""

    # Find the most common pattern
    most_common_pattern = max(pattern_counts.keys(), key=lambda p: pattern_counts[p])

    # Generate email variants for the target name
    variants = _generate_email_variants(name, domain)
    if not variants or most_common_pattern not in variants:
        return ""

    return variants[most_common_pattern]


def get_pattern_scores(
    known: List[Tuple[str, str]]
) -> List[Tuple[str, float]]:
    """
    Analyze known emails and return all detected patterns with confidence scores.

    Useful for understanding what patterns an organization uses and with what frequency.

    Args:
        known: List of (name, email) tuples.

    Returns:
        List of (pattern_id, confidence) tuples, sorted by confidence descending.
        Confidence is a float between 0.0 and 1.0.

    Examples:
        >>> get_pattern_scores([
        ...     ("Alice Johnson", "ajohnson@acme.com"),
        ...     ("Mark Stone", "mstone@acme.com"),
        ... ])
        [("f_l", 1.0)]

        >>> get_pattern_scores([
        ...     ("Alice Johnson", "ajohnson@acme.com"),
        ...     ("Mark Stone", "mstone@acme.com"),
        ...     ("Jane Doe", "jane.doe@acme.com"),
        ... ])
        [("f_l", 0.67), ("first.last", 0.33)]
    """
    pattern_counts, total_valid = _analyze_patterns(known)

    if total_valid == 0:
        return []

    scores = [
        (pattern_id, count / total_valid)
        for pattern_id, count in pattern_counts.items()
    ]

    # Sort by confidence descending
    return sorted(scores, key=lambda x: x[1], reverse=True)


def describe_pattern(pattern_id: str) -> Optional[Dict[str, any]]:
    """
    Get detailed documentation for a specific pattern.

    Args:
        pattern_id: Pattern identifier (e.g., "f_l", "first.last").

    Returns:
        Dict with 'name', 'description', and 'examples', or None if pattern not found.

    Examples:
        >>> describe_pattern("f_l")
        {
            "name": "First initial + Last name (underscore)",
            "description": "First letter of first name + underscore + lowercase last name",
            "examples": [
                ("Alice Johnson", "a_johnson"),
                ("Mark Stone", "m_stone"),
                ("Jane Doe", "j_doe"),
            ]
        }
    """
    return PATTERNS.get(pattern_id)
