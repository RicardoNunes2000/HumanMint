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
    from importlib_resources import files  # noqa: F401

import orjson  # noqa: F401

logger = logging.getLogger(__name__)

# Module-level cache for semantic tokens (lazy-loaded on first use)
_semantic_tokens: Optional[dict[str, str]] = None

# Targeted overrides to stabilize key domains regardless of upstream data.
SEMANTIC_OVERRIDES: dict[str, str] = {
    # IT / Digital
    "software": "IT",
    "web": "IT",
    "website": "IT",
    "online": "IT",
    "internet": "IT",
    "digital": "IT",
    "technology": "IT",
    "tech": "IT",
    # Ops / admin
    "manager": "ADMIN",
    "management": "ADMIN",
    "mgr": "ADMIN",
    "director": "ADMIN",
    "engineer": "IT",
    "ops": "OPS",
    "opns": "OPS",
    "operations": "OPS",
    # Infrastructure / maintenance
    "infrastructure": "INFRA",
    "mechanic": "INFRA",
    "maintenance": "INFRA",
    "maint": "INFRA",
    "water": "INFRA",
    # Legal / risk
    "risk": "RISK",
    "legal": "LEGAL",
    # Health / social
    "human": "SOCIAL",
    "case": "SOCIAL",
    "casemgmt": "SOCIAL",
    "cm": "SOCIAL",
    "casework": "SOCIAL",
    # Education
    "teacher": "EDU",
    "professor": "EDU",
    "instructor": "EDU",
    "educator": "EDU",
    # Neutralize noisy tokens
    "developer": "NULL",
    "services": "NULL",
}


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
        for token, domain in SEMANTIC_OVERRIDES.items():
            _semantic_tokens[token] = domain
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


# GENERIC RANK WORDS: These are excluded from token validation
# (sr, jr, iii, etc. are not meaningful for hallucination detection)
_GENERIC_RANK_TOKENS = {
    "sr",
    "sr.",
    "senior",
    "jr",
    "jr.",
    "junior",
    "i",
    "ii",
    "iii",
    "iv",
    "v",
    "1st",
    "2nd",
    "3rd",
    "asst",
    "asst.",
    "assistant",
    "assoc",
    "assoc.",
    "associate",
}

# TITLE WORDS: Cache for canonical title words from title_heuristics.json.gz
# These are known title role words (manager, specialist, coordinator, etc.)
# Not specializations or domains
_TITLE_WORDS_CACHE: set[str] | None = None


def _load_title_words() -> set[str]:
    """Load canonical title words (role/level words, not specializations).

    Uses position-based analysis: words that appear at the END of titles are
    typically role/level words (specialist, manager, director).

    Words at the BEGINNING/MIDDLE are typically specializations (gis, seo, hvac).

    Strategy: Track position frequency - if a word appears in multiple titles,
    prioritize appearances at the END (common role pattern) over beginning.
    Only classify as title word if it appears 2+ times AND appears in end position
    in at least one of those appearances.
    """
    global _TITLE_WORDS_CACHE
    if _TITLE_WORDS_CACHE is not None:
        return _TITLE_WORDS_CACHE

    try:
        from humanmint.data.utils import load_package_json_gz

        data = load_package_json_gz("title_heuristics.json.gz")

        canonicals = data.get("canonicals", [])

        # Track: token -> (total_count, appears_at_end_count)
        token_positions = {}

        for title in canonicals:
            tokens = title.lower().split()
            if not tokens:
                continue

            for idx, token in enumerate(tokens):
                if token not in token_positions:
                    token_positions[token] = [0, 0]  # [total_count, end_count]

                token_positions[token][0] += 1

                # Check if this token is at the END (last or second-to-last for hyphenated)
                is_at_end = idx >= len(tokens) - 2
                if is_at_end:
                    token_positions[token][1] += 1

        # Classify as title word if:
        # 1. Appears in 2+ titles, AND
        # 2. Appears at end position in at least 1 of them
        # This filters out specializations like "gis" which only appear at start
        title_words = {
            token
            for token, (total, at_end) in token_positions.items()
            if total >= 2 and at_end >= 1
        }

        _TITLE_WORDS_CACHE = title_words
        return title_words
    except Exception as e:
        # Gracefully degrade - return empty set if file not found
        logger.error(f"Failed to load title words for semantic safeguard: {e}")
        _TITLE_WORDS_CACHE = set()
        return _TITLE_WORDS_CACHE


def _extract_meaningful_tokens(text: str) -> set[str]:
    """
    Extract meaningful tokens from text for hallucination detection.

    Tokenizes on whitespace, lowercases, removes non-alphanumeric chars,
    and filters out generic rank/level words.

    Args:
        text: Input text (e.g., normalized job title).

    Returns:
        set[str]: Meaningful tokens (lowercase, alphanumeric only).

    Example:
        >>> _extract_meaningful_tokens("Sr. Software Engineer III")
        {'software', 'engineer'}  # Excludes 'sr' and 'iii'

        >>> _extract_meaningful_tokens("Finance Manager")
        {'finance', 'manager'}
    """
    # Lowercase and remove non-alphanumeric (except spaces for splitting)
    normalized = re.sub(r"[^a-z0-9\s]", "", text.lower())
    # Split on whitespace
    all_tokens = {t for t in normalized.split() if t}
    # Filter out generic rank words
    meaningful = {t for t in all_tokens if t not in _GENERIC_RANK_TOKENS}
    return meaningful if meaningful else all_tokens


def _has_hallucinations(
    input_tokens: set[str], candidate_tokens: set[str], input_domains: set[str]
) -> bool:
    """
    Detect if candidate introduces tokens from different semantic domains or substitutes key tokens.

    A hallucination occurs when:
    1. Candidate has tokens NOT in input (extra tokens) AND those tokens either:
       a. Map to semantic domains DIFFERENT from input_domains, OR
       b. Are domain-specific tokens (specialized) not in vocabulary
    2. OR: Candidate is missing tokens from input (token substitution)
       - e.g., "city" in input but "facility" in candidate = domain substitution

    Example (HALLUCINATION - Unknown specialization):
        Input: "Sr. Software Engineer III"
        Input tokens: {software, engineer}
        Input domains: {IT}

        Candidate: "Senior iOS Software Engineer"
        Candidate tokens: {senior, ios, software, engineer}
        Extra tokens: {senior, ios}
          - "senior" → NULL (generic, OK)
          - "ios" → NOT IN VOCAB + domain context → HALLUCINATION

    Example (HALLUCINATION - Token Substitution):
        Input: "Assistant City Manager"
        Input tokens: {city, manager}

        Candidate: "assistant facility manager"
        Candidate tokens: {manager, facility}
        Missing tokens: {city} (domain term removed)
        Extra tokens: {facility} (different term added)
        → HALLUCINATION (domain term replaced)

    Example (NO HALLUCINATION):
        Input: "Finance Manager, CPA"
        Input tokens: {finance, manager}

        Candidate: "Finance Manager"
        Candidate tokens: {finance, manager}
        Extra tokens: {} (none)

    Args:
        input_tokens: Meaningful tokens from input.
        candidate_tokens: Meaningful tokens from candidate.
        input_domains: Semantic domains from input (from _extract_domains).

    Returns:
        bool: True if hallucination detected (reject match),
              False if OK to accept (no hallucinations).
    """
    # Find tokens in candidate that are NOT in input
    extra_tokens = candidate_tokens - input_tokens
    # Find tokens in input that are NOT in candidate (missing/replaced)
    missing_tokens = input_tokens - candidate_tokens

    # If no extra or missing tokens → no hallucination possible
    if not extra_tokens and not missing_tokens:
        return False

    vocabulary = _load_semantic_tokens()

    # List of common generic/rank tokens that can appear in any title
    # (don't count as hallucinations if they appear as extra tokens)
    GENERIC_FILLERS = {
        "senior",
        "junior",
        "lead",
        "principal",
        "head",
        "chief",
        "assistant",
        "associate",
        "apprentice",
        "trainee",
        "full",
        "time",
        "part",
        "contract",
        "temporary",
    }

    # GUARD 1: Check for token substitution (missing input tokens + extra candidate tokens)
    # This catches cases like "city" → "facility" where a meaningful term is replaced
    if missing_tokens and extra_tokens:
        # Both missing and extra tokens → likely substitution
        # Only allow if both are generic fillers (e.g., "senior engineer" → "principal engineer")
        missing_non_generic = {t for t in missing_tokens if t not in GENERIC_FILLERS}
        extra_non_generic = {t for t in extra_tokens if t not in GENERIC_FILLERS}

        if missing_non_generic and extra_non_generic:
            # Meaningful tokens were replaced by different meaningful tokens → HALLUCINATION
            return True

    # GUARD 2: Check extra tokens for domain conflicts
    title_words = _load_title_words()  # Load canonical title words for filtering

    for extra_token in extra_tokens:
        # Skip truly generic fillers (rank words like senior, junior)
        if extra_token in GENERIC_FILLERS:
            continue

        # Skip known title words (specialist, manager, coordinator, etc.)
        # These are role/title words, not specializations
        if extra_token in title_words:
            continue

        token_domain = vocabulary.get(extra_token)

        # Case 1: Token is in vocabulary - check domain match
        if token_domain:
            if token_domain == "NULL":
                # Generic/NULL domain → OK
                continue
            elif input_domains and token_domain not in input_domains:
                # Different domain + we have domain context → HALLUCINATION
                return True
        else:
            # Case 2: Token NOT in vocabulary AND NOT a known title word
            # This is an unknown specialization (like "ios", "seo", "gis")
            # These are likely hallucinations - reject them
            return True

    # All checks passed → OK
    return False


def has_semantic_token_overlap(text_a: str, text_b: str) -> bool:
    """
    Check if two texts share at least one semantic domain.

    Used for Tier 3 fuzzy matching validation: requires at least one
    matching semantic token between input and candidate.

    Args:
        text_a: First text (input).
        text_b: Second text (candidate).

    Returns:
        bool: True if at least one domain overlaps, False otherwise.

    Example:
        >>> has_semantic_token_overlap("Sr. Software Engineer III", "Senior Software Engineer")
        True  # Both have {IT}

        >>> has_semantic_token_overlap("Water Developer", "Web Developer")
        False  # {INFRA} vs {IT} - no overlap
    """
    domains_a = _extract_domains(text_a)
    domains_b = _extract_domains(text_b)

    # If either has no domains, fail-open
    if not domains_a or not domains_b:
        return True

    # Check for overlap
    return bool(domains_a.intersection(domains_b))
