"""
Department data loader and utilities.

Provides access to canonical departments and department mappings from the
data folder. Uses compressed JSON caches for fast loads.
"""

import gzip
import json
from pathlib import Path
from typing import Optional
import warnings

# Path to the mappings cache
DATA_DIR = Path(__file__).parent.parent / "data"
MAPPINGS_CACHE = DATA_DIR / "department_mappings_list.json.gz"

# Canonical list of all standardized department names
CANONICAL_DEPARTMENTS = [
    "Administration",
    "Airport",
    "Animal Control",
    "Assessor",
    "Athletics",
    "Auditor",
    "Board of Education",
    "Budget",
    "Building & Inspections",
    "Cemetery",
    "City Attorney",
    "City Clerk",
    "City Council",
    "City Manager",
    "Clerk of Courts",
    "Communications",
    "Community Development",
    "Coroner",
    "Curriculum & Instruction",
    "District Attorney",
    "District Court",
    "Elections",
    "Elementary School",
    "Emergency Communications",
    "Emergency Management",
    "Engineering",
    "Facilities Management",
    "Finance",
    "Fire",
    "Fleet Management",
    "Food Service",
    "Health",
    "High School",
    "Human Resources",
    "Human Services",
    "Information Technology",
    "Juvenile Court",
    "Library",
    "Mayor's Office",
    "Middle School",
    "Municipal Court",
    "Parks & Recreation",
    "Planning",
    "Police",
    "Probation",
    "Public Defender",
    "Public Safety",
    "Public Works",
    "Purchasing",
    "Risk Management",
    "Senior Services",
    "Solid Waste",
    "Special Education",
    "Stormwater",
    "Streets & Roads",
    "Student Services",
    "Superintendent",
    "Transportation Services",
    "Treasurer",
    "Utilities",
    "Veterans Services",
    "Wastewater",
    "Water",
    "Zoning",
]

# Frozen set for O(1) lookup
CANONICAL_DEPARTMENTS_SET = frozenset(CANONICAL_DEPARTMENTS)

# In-memory caches to avoid re-reading on every call
_mappings_cache: Optional[dict[str, list[str]]] = None
_reverse_mapping_cache: Optional[dict[str, str]] = None
_missing_cache_warned = False


def get_canonical_departments() -> list[str]:
    """
    Get the complete list of canonical department names.

    Returns:
        list[str]: Sorted list of all standardized department names.
    """
    return CANONICAL_DEPARTMENTS.copy()


def is_canonical(dept: str) -> bool:
    """
    Check if a department name is already canonical.

    Args:
        dept: Department name to check.

    Returns:
        bool: True if the department is in the canonical list.
    """
    return dept in CANONICAL_DEPARTMENTS_SET


def _load_from_cache() -> Optional[tuple[dict[str, list[str]], dict[str, str]]]:
    """Load mappings from a precomputed cache if available."""
    if not MAPPINGS_CACHE.exists():
        return None
    try:
        data = gzip.decompress(MAPPINGS_CACHE.read_bytes())
        payload = json.loads(data.decode("utf-8"))
        mappings = payload.get("mappings")
        reverse = payload.get("reverse")
        if isinstance(mappings, dict) and isinstance(reverse, dict):
            return mappings, reverse
    except Exception:
        return None
    return None


def _build_caches() -> None:
    """Populate mappings and reverse mappings in memory (idempotent)."""
    global _mappings_cache, _reverse_mapping_cache
    global _missing_cache_warned

    if _mappings_cache is not None and _reverse_mapping_cache is not None:
        return

    loaded = _load_from_cache()
    if loaded:
        mappings, reverse = loaded
    else:
        if not _missing_cache_warned:
            warnings.warn(
                f"Department cache not found at {MAPPINGS_CACHE}. "
                "Run scripts/build_pickles.py to generate it.",
                RuntimeWarning,
            )
            _missing_cache_warned = True
        mappings, reverse = {}, {}

    _mappings_cache = mappings
    _reverse_mapping_cache = reverse


def load_mappings() -> dict[str, list[str]]:
    """
    Load all department mappings from cache.

    Returns:
        dict[str, list[str]]: Mapping of canonical names to original names.

    Raises:
        FileNotFoundError: If the cache file is not found.
    """
    _build_caches()
    return _mappings_cache  # type: ignore[return-value]


def get_mapping_for_original(original_name: str) -> Optional[str]:
    """
    Get the canonical department name for an original name.

    Args:
        original_name: Original department name to look up.

    Returns:
        Optional[str]: Canonical department name, or None if not found.

    Raises:
        FileNotFoundError: If the cache file is not found.
    """
    _build_caches()
    original_name = original_name.strip().lower()
    return _reverse_mapping_cache.get(original_name) if _reverse_mapping_cache else None


def get_originals_for_canonical(canonical_name: str) -> list[str]:
    """
    Get all original names that map to a canonical department.

    Useful for reverse lookups and understanding variations.

    Args:
        canonical_name: Canonical department name.

    Returns:
        list[str]: List of original names mapping to this canonical name.

    Raises:
        FileNotFoundError: If the pickle file is not found.
    """
    _build_caches()
    canonical_name = canonical_name.strip()
    if not _mappings_cache:
        return []
    return _mappings_cache.get(canonical_name, [])
