"""
Internal processors for HumanMint unified facade.

Handles the heavy lifting of normalizing individual fields:
- Name parsing and enrichment
- Email validation and domain extraction
- Phone number formatting
- Department matching and categorization
- Title standardization

These are internal helpers; use mint() from the main facade instead.
"""

from typing import Optional

from .names import normalize_name, enrich_name
from .emails import normalize_email
from .phones import normalize_phone
from .departments import (
    normalize_department,
    find_best_match as find_best_department_match,
    get_department_category,
)
from .departments.matching import is_likely_non_department
from .titles import normalize_title_full
from .types import NameResult, EmailResult, PhoneResult, DepartmentResult, TitleResult


def process_name(
    raw_name: Optional[str], aggressive_clean: bool = False
) -> Optional[NameResult]:
    """
    Extract and enrich name components.

    Args:
        raw_name: Raw name string.
        aggressive_clean: If True, strips SQL artifacts and corruption markers.
                         Only use if data comes from genuinely untrusted sources.
                         Default False to preserve legitimate names.

    Returns:
        NameResult with raw input and parsed components, or None if invalid.
    """
    if not raw_name:
        return None

    try:
        # Apply aggressive cleaning if requested
        cleaned_name = raw_name
        if aggressive_clean:
            from .names.garbled import clean_garbled_name, should_use_garbled_cleaning

            # Auto-detect if cleaning is needed
            if should_use_garbled_cleaning(raw_name):
                cleaned = clean_garbled_name(raw_name)
                if cleaned:
                    cleaned_name = cleaned

        normalized = normalize_name(cleaned_name)
        enriched = enrich_name(normalized)

        if not (enriched.get("full") or enriched.get("is_valid")):
            return None

        full_name = enriched.get("full", "").strip() if enriched.get("full") else ""
        first_name = enriched.get("first", "").strip() if enriched.get("first") else ""
        middle_name = enriched.get("middle", "").strip() if enriched.get("middle") else None
        last_name = enriched.get("last", "").strip() if enriched.get("last") else ""
        suffix_name = enriched.get("suffix", "").strip() if enriched.get("suffix") else None

        # Normalize gender to lowercase
        gender = enriched.get("gender", "unknown")
        if gender and gender != "unknown":
            gender = gender.lower()

        return {
            "raw": raw_name,
            "first": first_name or "",
            "middle": middle_name,
            "last": last_name or "",
            "suffix": suffix_name,
            "full": full_name or raw_name,
            "gender": gender,
        }
    except (ValueError, AttributeError, TypeError, FileNotFoundError):
        return None


def process_email(raw_email: Optional[str]) -> Optional[EmailResult]:
    """
    Normalize and validate email.

    Args:
        raw_email: Raw email string.

    Returns:
        EmailResult with raw input and validation metadata, or None if invalid.
    """
    if not raw_email:
        return None

    try:
        result = normalize_email(raw_email)
        if isinstance(result, dict):
            return {
                "raw": raw_email,
                "normalized": result.get("email") or raw_email,
                "is_valid": result.get("is_valid", False),
                "is_generic": result.get("is_generic", False),
                "is_free_provider": result.get("is_free_provider", False),
                "domain": result.get("domain"),
            }
        return None
    except (ValueError, TypeError, FileNotFoundError):
        return None


def process_phone(raw_phone: Optional[str]) -> Optional[PhoneResult]:
    """
    Normalize and format phone number.

    Args:
        raw_phone: Raw phone string.

    Returns:
        PhoneResult with raw input and formatted variants, or None if invalid.
    """
    if not raw_phone:
        return None

    try:
        result = normalize_phone(raw_phone, country="US")
        if isinstance(result, dict):
            # Normalize phone type to lowercase
            phone_type = result.get("type")
            if phone_type:
                phone_type = phone_type.lower()

            return {
                "raw": raw_phone,
                "e164": result.get("e164"),
                "pretty": result.get("pretty"),
                "extension": result.get("extension"),
                "is_valid": result.get("is_valid", False),
                "type": phone_type,
            }
        return None
    except (ValueError, TypeError, FileNotFoundError):
        return None


def process_department(
    raw_dept: Optional[str], overrides: Optional[dict[str, str]] = None
) -> Optional[DepartmentResult]:
    """
    Normalize department and apply overrides.

    Args:
        raw_dept: Raw department string.
        overrides: Optional custom department mappings.

    Returns:
        DepartmentResult with raw input and normalized variants, or None if invalid.
    """
    if not raw_dept:
        return None

    try:
        normalized = normalize_department(raw_dept)
        is_non_dept = is_likely_non_department(normalized)

        # Check if normalized department matches any override
        is_override = False
        final_dept = normalized
        if overrides and normalized in overrides:
            final_dept = overrides[normalized]
            is_override = True
        else:
            # Find best canonical match if no override matched
            canonical = find_best_department_match(raw_dept, threshold=0.6)
            if canonical:
                final_dept = canonical
            elif is_non_dept:
                final_dept = None
            else:
                final_dept = normalized

        category = get_department_category(final_dept) if final_dept else None
        # Normalize category to lowercase
        if category:
            category = category.lower()

        return {
            "raw": raw_dept,
            "normalized": normalized,
            "canonical": final_dept,
            "category": category,
            "is_override": is_override,
        }
    except (ValueError, FileNotFoundError):
        return None


def process_title(raw_title: Optional[str]) -> Optional[TitleResult]:
    """
    Normalize and canonicalize job title.

    Args:
        raw_title: Raw title string.

    Returns:
        TitleResult with raw input and normalized variants, or None if invalid.
    """
    if not raw_title:
        return None

    try:
        result = normalize_title_full(raw_title, threshold=0.6)
        return {
            "raw": result.get("raw"),
            "cleaned": result.get("cleaned"),
            "canonical": result.get("canonical"),
            "is_valid": result.get("is_valid"),
        }
    except (ValueError, FileNotFoundError):
        return None
