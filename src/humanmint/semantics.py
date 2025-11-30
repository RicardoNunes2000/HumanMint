"""
Semantic safeguard for fuzzy matching using domain-based token voting.

This module prevents fuzzy matching from accepting semantically incompatible
matches (e.g., "Web Developer" vs "Water Developer") by checking if both texts
belong to the same semantic domain.

Token Voting Logic:
    1. Tokenize both strings (lowercase, alphanumeric, whitespace-split)
    2. Look up each token in semantic_tokens.json → build domain sets
    3. NULL tokens evaporate (ignored completely)
    4. Fail-open rule: If either set is EMPTY → PASS (allow match)
    5. Conflict rule: If both sets non-empty AND intersection EMPTY → BLOCK (veto)
    6. Otherwise → PASS

Example:
    >>> check_semantic_conflict("Web Developer", "Water Developer")
    True  # CONFLICT: {IT} vs {INFRA} - block this match

    >>> check_semantic_conflict("Software Engineer", "Senior Software Engineer")
    False  # PASS: {IT} vs {IT} - allow this match

    >>> check_semantic_conflict("Manager", "Director")
    False  # PASS: {} vs {} - fail-open, both empty
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Optional

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

import orjson

logger = logging.getLogger(__name__)

# Module-level cache for semantic tokens (lazy-loaded on first use)
_semantic_tokens: Optional[dict[str, str]] = None


def _load_semantic_tokens() -> dict[str, str]:
    """
    Lazy-load semantic tokens from compressed cache.

    Returns a mapping of token → domain (e.g., "software" → "IT").
    Gracefully degrades to empty dict if vocabulary is unavailable.

    Returns:
        dict[str, str]: Token to domain mapping. Empty dict on error.
    """
    global _semantic_tokens
    if _semantic_tokens is not None:
        return _semantic_tokens

    try:
        from humanmint.data.utils import load_package_json_gz

        data = load_package_json_gz("semantic_tokens.json.gz")
        _semantic_tokens = data if isinstance(data, dict) else {}
        return _semantic_tokens
    except FileNotFoundError:
        logger.warning(
            "Semantic tokens vocabulary not found. "
            "Run scripts/build_caches.py to generate it. "
            "Semantic safeguard disabled."
        )
        _semantic_tokens = {}
        return _semantic_tokens
    except Exception as e:
        logger.error(f"Failed to load semantic tokens: {e}. Disabling safeguard.")
        _semantic_tokens = {}
        return _semantic_tokens


def _tokenize(text: str) -> set[str]:
    """
    Extract tokens from text for semantic analysis.

    Converts to lowercase, removes non-alphanumeric characters, and splits
    on whitespace. Filters out empty tokens.

    Args:
        text: Input text to tokenize.

    Returns:
        set[str]: Set of tokens (lowercase, alphanumeric only).

    Example:
        >>> _tokenize("Senior Web-Developer")
        {'senior', 'web', 'developer'}
    """
    # Lowercase and remove non-alphanumeric (keeps spaces for splitting)
    normalized = re.sub(r"[^a-z0-9\s]", "", text.lower())
    # Split on whitespace and filter empty
    tokens = {t for t in normalized.split() if t}
    return tokens


def _extract_domains(text: str) -> set[str]:
    """
    Extract semantic domains for text by token voting.

    Tokenizes the text, looks up each token in the semantic vocabulary,
    and builds a set of domains. NULL tokens are filtered out (they evaporate).

    Args:
        text: Input text to analyze.

    Returns:
        set[str]: Set of domain labels (e.g., {"IT", "INFRA"}). Empty set if
                  no meaningful domains found.

    Example:
        >>> _extract_domains("Web Developer")
        {'IT'}

        >>> _extract_domains("Water Developer")
        {'INFRA'}

        >>> _extract_domains("Manager")
        set()  # "manager" maps to NULL, which evaporates
    """
    tokens = _tokenize(text)
    vocabulary = _load_semantic_tokens()

    # Vote: each token contributes its domain to the set
    domains = set()
    for token in tokens:
        domain = vocabulary.get(token)
        # NULL tokens are completely ignored (they evaporate)
        if domain and domain != "NULL":
            domains.add(domain)

    return domains


def check_semantic_conflict(text_a: str, text_b: str) -> bool:
    """
    Check if two texts are semantically incompatible (hard conflict).

    Uses domain-based token voting to detect if texts belong to different
    semantic domains. Returns True (conflict) only if both texts have
    specific domain signals that don't overlap.

    Fail-open design:
        - If either text has NO domain signals → PASS (allow match)
        - If both texts have domain signals with NO overlap → BLOCK (veto match)
        - Otherwise → PASS (allow match)

    Args:
        text_a: First text (e.g., input title or department name).
        text_b: Second text (e.g., candidate match).

    Returns:
        bool: True if hard semantic conflict detected (veto the match),
              False if compatible or insufficient info (allow match).

    Example:
        >>> check_semantic_conflict("Web Developer", "Water Developer")
        True  # BLOCK: {IT} vs {INFRA}

        >>> check_semantic_conflict("Software Engineer", "Senior Software Engineer")
        False  # PASS: {IT} vs {IT}

        >>> check_semantic_conflict("Manager", "Director")
        False  # PASS: {} vs {} (fail-open)

        >>> check_semantic_conflict("Developer", "Finance Manager")
        False  # PASS: {IT} vs {} (fail-open)
    """
    domains_a = _extract_domains(text_a)
    domains_b = _extract_domains(text_b)

    # Fail-open: if either is empty, allow the match
    if not domains_a or not domains_b:
        return False

    # Both have domain signals: check for overlap
    # BLOCK only if NO overlap (hard conflict)
    has_overlap = bool(domains_a.intersection(domains_b))
    return not has_overlap
