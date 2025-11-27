"""
Email normalization for HumanMint.

Simple, functional, predictable.
"""

import sys
import gzip
import json
from functools import lru_cache
from typing import Dict, Optional, Set
from email_validator import validate_email, EmailNotValidError

from .classifier import is_free_provider

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


_GENERIC_INBOXES_CACHE: Optional[Set[str]] = None
_EMPTY_EMAIL: Dict[str, Optional[str]] = {
    "email": None,
    "local": None,
    "domain": None,
    "local_base": None,
    "is_generic": False,
    "is_free_provider": False,
    "is_valid": False,
}


def _load_generic_inboxes() -> Set[str]:
    """
    Load generic inboxes from generic_inboxes.json.gz package data.

    Returns:
        Set of generic inbox names (lowercased).
    """
    global _GENERIC_INBOXES_CACHE

    if _GENERIC_INBOXES_CACHE is not None:
        return _GENERIC_INBOXES_CACHE

    inboxes = set()

    try:
        # Load from package data using importlib.resources
        data_files = files("humanmint").joinpath("data")

        # Require compressed JSON cache; no text fallback
        cache_file = data_files.joinpath("generic_inboxes.json.gz")
        data = gzip.decompress(cache_file.read_bytes())
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, (set, list, tuple)):
            inboxes = {str(item).lower() for item in payload}
            _GENERIC_INBOXES_CACHE = inboxes
            return inboxes
    except (FileNotFoundError, AttributeError, TypeError):
        # Fallback if package data is not found (should not happen in normal use)
        pass
    except Exception:
        pass

    if not inboxes:
        raise FileNotFoundError(
            "Generic inbox cache not found or unreadable. "
            "Run scripts/build_pickles.py to regenerate generic_inboxes.json.gz."
        )

    _GENERIC_INBOXES_CACHE = inboxes
    return inboxes


def _clean(raw: str) -> str:
    return raw.strip().lower()


def _validate(email: str) -> Optional[str]:
    try:
        # Skip DNS lookups for speed and offline resilience
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return None


def _extract_fields(email: str) -> Dict[str, str]:
    local, _, domain = email.partition("@")
    local_base = local.split("+", 1)[0]
    return {
        "email": email,
        "local": local,
        "domain": domain,
        "local_base": local_base,
    }


def _enrich(
    fields: Dict[str, str], generic_inboxes: Optional[Set[str]] = None
) -> Dict[str, str]:
    """
    Enrich email fields with validity, genericity, and free provider checks.

    Args:
        fields: Email fields dict from _extract_fields().
        generic_inboxes: Set of generic inbox names. If None, loads from package data.

    Returns:
        Enriched fields dict.

    Raises:
        TypeError: If generic_inboxes is not a set or None.
    """
    if generic_inboxes is None:
        generic_inboxes = _load_generic_inboxes()
    elif not isinstance(generic_inboxes, set):
        raise TypeError(
            f"generic_inboxes must be a set, got {type(generic_inboxes).__name__}"
        )

    fields["is_generic"] = fields["local_base"] in generic_inboxes
    fields["is_free_provider"] = is_free_provider(fields["domain"])
    fields["is_valid"] = True
    return fields


def _empty() -> Dict[str, Optional[str]]:
    return _EMPTY_EMAIL.copy()


@lru_cache(maxsize=4096)
def _normalize_email_cached(cleaned: str) -> Dict[str, Optional[str]]:
    """Cached normalization path when using default inbox list."""
    validated = _validate(cleaned)

    if validated is None:
        result = _EMPTY_EMAIL.copy()
        result["email"] = cleaned
        return result

    fields = _extract_fields(validated)
    return _enrich(fields)


def normalize_email(
    raw: Optional[str], generic_inboxes: Optional[Set[str]] = None
) -> Dict[str, Optional[str]]:
    """
    Public API: normalize an email.

    Always returns the same keys. Throws only on type validation errors for generic_inboxes.
    Pure function.

    Args:
        raw: Email string to normalize.
        generic_inboxes: Optional set of generic inbox names. If None, loads from package data.
            Must be a set of strings if provided.

    Returns:
        Dict with keys: email, local, domain, local_base, is_generic, is_free_provider, is_valid.

    Raises:
        TypeError: If generic_inboxes is not a set or None.

    Examples:
        >>> normalize_email('info@gmail.com')
        {'email': 'info@gmail.com', 'local': 'info', 'domain': 'gmail.com',
         'local_base': 'info', 'is_generic': False, 'is_free_provider': True, 'is_valid': True}

        >>> normalize_email('user@company.com', generic_inboxes={'custom', 'test'})
        {'email': 'user@company.com', 'local': 'user', 'domain': 'company.com',
         'local_base': 'user', 'is_generic': False, 'is_free_provider': False, 'is_valid': True}
    """
    if not raw or not isinstance(raw, str):
        return _empty()

    cleaned = _clean(raw)

    # Fast path: default inbox list can be cached
    if generic_inboxes is None:
        return _normalize_email_cached(cleaned).copy()

    validated = _validate(cleaned)

    if validated is None:
        return _empty() | {"email": cleaned}  # keep original cleaned string

    fields = _extract_fields(validated)
    enriched = _enrich(fields, generic_inboxes)
    return enriched
