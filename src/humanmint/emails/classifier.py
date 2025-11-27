"""
Email classification utilities for HumanMint.

Classifies emails based on domain properties (free provider, generic inbox, etc.).
"""

import gzip
import json
import sys
from functools import lru_cache
from typing import Optional, Set

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


_FREE_PROVIDERS_CACHE: Optional[Set[str]] = None


def _load_free_email_providers() -> Set[str]:
    """
    Load free email providers from free_email_providers.json.gz package data.

    Returns:
        Set of free email provider domains (lowercased).

    Raises:
        FileNotFoundError: If the cache cannot be loaded.
    """
    global _FREE_PROVIDERS_CACHE

    if _FREE_PROVIDERS_CACHE is not None:
        return _FREE_PROVIDERS_CACHE

    providers = set()

    try:
        # Load from package data using importlib.resources
        data_files = files("humanmint").joinpath("data")
        cache_file = data_files.joinpath("free_email_providers.json.gz")
        data = gzip.decompress(cache_file.read_bytes())
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, (set, list, tuple)):
            providers = {str(item).lower() for item in payload}
            _FREE_PROVIDERS_CACHE = providers
            return providers
    except (FileNotFoundError, AttributeError, TypeError):
        pass
    except Exception:
        pass

    if not providers:
        raise FileNotFoundError(
            "Free email providers cache not found or unreadable. "
            "Run scripts/build_pickles.py to regenerate free_email_providers.json.gz."
        )

    _FREE_PROVIDERS_CACHE = providers
    return providers


@lru_cache(maxsize=4096)
def is_free_provider(domain: str) -> bool:
    """
    Check if an email domain is a known free email provider.

    Args:
        domain: Email domain (e.g., "gmail.com", "yahoo.com").
                Can be the full domain with or without subdomains.

    Returns:
        True if the domain is a known free email provider, False otherwise.

    Examples:
        >>> is_free_provider("gmail.com")
        True

        >>> is_free_provider("yahoo.com")
        True

        >>> is_free_provider("company.com")
        False
    """
    if not domain or not isinstance(domain, str):
        return False

    domain_lower = domain.strip().lower()

    # Handle edge cases
    if not domain_lower or domain_lower.startswith("."):
        return False

    providers = _load_free_email_providers()

    # Direct match
    if domain_lower in providers:
        return True

    # Check if it's a subdomain of a known provider
    # e.g., mail.google.com -> check google.com
    parts = domain_lower.split(".")
    for i in range(1, len(parts)):
        subdomain = ".".join(parts[i:])
        if subdomain in providers:
            return True

    return False
