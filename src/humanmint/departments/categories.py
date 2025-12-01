"""
Department category classification for HumanMint.

Classifies canonical departments into logical categories by loading from
department_categories.json.gz (generated from semantic tokens).
"""

import gzip
import json
from pathlib import Path
from typing import Optional

# Load categories from generated file
_CATEGORIES_CACHE = None


def _load_categories():
    """Load department categories from JSON file."""
    global _CATEGORIES_CACHE
    if _CATEGORIES_CACHE is not None:
        return _CATEGORIES_CACHE

    try:
        # Find the data directory
        data_dir = Path(__file__).parent.parent / "data"
        categories_file = data_dir / "department_categories.json.gz"

        if not categories_file.exists():
            return {}

        with gzip.open(categories_file, "rt", encoding="utf-8") as f:
            _CATEGORIES_CACHE = json.load(f)
            return _CATEGORIES_CACHE
    except Exception:
        return {}


# Load on module import
_CATEGORIES_CACHE = _load_categories()


def get_department_category(dept: str) -> Optional[str]:
    """
    Get the category for a canonical department name.

    Categories are loaded from department_categories.json.gz, which is
    generated from semantic tokens and keyword fallbacks.

    Example:
        >>> get_department_category("Police")
        "public safety"
        >>> get_department_category("Water")
        "infrastructure"
        >>> get_department_category("Unknown Department")
        None

    Args:
        dept: Canonical department name.

    Returns:
        Optional[str]: Category name (lowercase), or None if not recognized.
    """
    if not _CATEGORIES_CACHE:
        return None

    category = _CATEGORIES_CACHE.get(dept)
    if category:
        return category.lower()
    return None


def get_all_categories() -> set[str]:
    """
    Get all unique department categories.

    Returns:
        set[str]: Set of all category names (lowercase).
    """
    if not _CATEGORIES_CACHE:
        return set()
    return {cat.lower() for cat in _CATEGORIES_CACHE.values()}


def get_departments_by_category(category: str) -> list[str]:
    """
    Get all departments belonging to a specific category.

    Example:
        >>> get_departments_by_category("public safety")
        ["Police", "Fire", "Emergency Management", ...]

    Args:
        category: Category name (case-insensitive).

    Returns:
        list[str]: List of canonical departments in that category, sorted
                  alphabetically.
    """
    if not _CATEGORIES_CACHE:
        return []

    category_lower = category.lower()
    departments = [
        dept
        for dept, cat in _CATEGORIES_CACHE.items()
        if cat.lower() == category_lower
    ]
    return sorted(departments)


def categorize_departments(dept_names: list[str]) -> dict[str, Optional[str]]:
    """
    Categorize multiple department names.

    Useful for batch processing to assign categories to a list of
    departments.

    Example:
        >>> categorize_departments(["Police", "Water", "Unknown"])
        {
            "Police": "public safety",
            "Water": "infrastructure",
            "Unknown": None
        }

    Args:
        dept_names: List of canonical department names.

    Returns:
        dict[str, Optional[str]]: Mapping of department names to their
                                  categories (None if not recognized).
    """
    return {dept: get_department_category(dept) for dept in dept_names}
