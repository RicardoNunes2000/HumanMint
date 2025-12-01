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

from rapidfuzz import fuzz

from .addresses import normalize_address
from .departments import find_best_match as find_best_department_match
from .departments import get_department_category, normalize_department
from .departments.matching import is_likely_non_department
from .emails import normalize_email
from .names import enrich_name, normalize_name
from .names.matching import detect_nickname
from .organizations import normalize_organization
from .phones import normalize_phone
from .titles import normalize_title_full
from .types import (AddressResult, DepartmentResult, EmailResult, NameResult,
                    OrganizationResult, PhoneResult, TitleResult)


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
    if not raw_name or not isinstance(raw_name, str):
        return None

    try:
        # Apply aggressive cleaning if requested
        cleaned_name = raw_name
        nickname = None
        # Capture quoted nickname if present in raw
        if isinstance(raw_name, str):
            import re

            m = re.search(r"[\"']([^\"']{2,})[\"']", raw_name)
            if m:
                nickname = m.group(1).strip()
        if aggressive_clean:
            from .names.garbled import (clean_garbled_name,
                                        should_use_garbled_cleaning)

            # Auto-detect if cleaning is needed
            if should_use_garbled_cleaning(raw_name):
                cleaned = clean_garbled_name(raw_name)
                if cleaned:
                    cleaned_name = cleaned

        normalized = normalize_name(cleaned_name)
        enriched = enrich_name(normalized)

        if not (enriched.get("full") or enriched.get("is_valid")):
            return None

        first_name = enriched.get("first", "").strip() if enriched.get("first") else ""
        middle_name = (
            enriched.get("middle", "").strip() if enriched.get("middle") else None
        )
        last_name = enriched.get("last", "").strip() if enriched.get("last") else ""
        suffix_name = (
            enriched.get("suffix", "").strip() if enriched.get("suffix") else None
        )

        # Normalize gender to lowercase
        gender = enriched.get("gender", "unknown")
        if gender and gender != "unknown":
            gender = gender.lower()

        # Detect nickname in middle if it matches a nickname of the first name
        if middle_name:
            middle_norm = middle_name.strip().strip("'\"")
            if middle_norm:
                detected_canonical = detect_nickname(middle_norm)
                if (
                    detected_canonical
                    and first_name
                    and detected_canonical.lower() == first_name.lower()
                ):
                    nickname = nickname or middle_norm
                    middle_name = None
                elif nickname and nickname.lower() == middle_norm.lower():
                    middle_name = None

        canonical_parts = [first_name.lower()]
        if middle_name:
            canonical_parts.append(middle_name.lower())
        if last_name:
            canonical_parts.append(last_name.lower())
        if suffix_name:
            canonical_parts.append(suffix_name.lower())
        canonical_val = " ".join(canonical_parts)

        # Detect nickname if not explicitly quoted
        if not nickname and first_name:
            detected_canonical = detect_nickname(first_name)
            if detected_canonical:
                nickname = first_name

        # Classify suffix type (e.g., generational)
        generational_suffixes = {
            "jr",
            "sr",
            "ii",
            "iii",
            "iv",
            "v",
            "vi",
            "vii",
            "viii",
            "ix",
            "x",
        }
        suffix_type = (
            "generational"
            if suffix_name and suffix_name.lower() in generational_suffixes
            else None
        )

        return {
            "raw": raw_name,
            "first": first_name or "",
            "middle": middle_name,
            "last": last_name or "",
            "suffix": suffix_name,
            "suffix_type": suffix_type,
            "full": " ".join(
                p for p in [first_name, middle_name, last_name, suffix_name] if p
            )
            or raw_name,
            "gender": gender,
            "nickname": nickname,
            "canonical": canonical_val,
            "is_valid": enriched.get("is_valid", False),
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
    if not raw_email or not isinstance(raw_email, str):
        return None

    try:
        result = normalize_email(raw_email)
        if isinstance(result, dict):
            return {
                "raw": raw_email,
                "normalized": result.get("email") or raw_email,
                "is_valid": result.get("is_valid", False),
                "is_generic_inbox": result.get("is_generic", False),
                "is_free_provider": result.get("is_free_provider", False),
                "domain": result.get("domain"),
                "local": result.get("local"),
                "local_base": result.get("local_base"),
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
    if not raw_phone or not isinstance(raw_phone, str):
        return None

    try:
        result = normalize_phone(raw_phone, country="US")
        if isinstance(result, dict):
            return {
                "raw": raw_phone,
                "e164": result.get("e164"),
                "pretty": result.get("pretty"),
                "extension": result.get("extension"),
                "is_valid": result.get("is_valid", False),
                "type": result.get("type"),
                "country": result.get("country"),
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
    if not raw_dept or not isinstance(raw_dept, str):
        return None

    try:
        normalized = normalize_department(raw_dept)
        is_non_dept = is_likely_non_department(normalized)

        # Check if normalized department matches any override
        is_override = False
        matched_canonical = False
        final_dept = normalized
        if overrides:
            normalized_lower = normalized.lower()
            norm_overrides = {}
            for k, v in overrides.items():
                try:
                    k_norm = normalize_department(k)
                except Exception:
                    k_norm = k
                norm_overrides[k_norm.lower()] = v

            if normalized_lower in norm_overrides:
                final_dept = norm_overrides[normalized_lower]
                is_override = True
                matched_canonical = True
            else:
                # Fuzzy fallback on overrides (token_sort_ratio)
                best = None
                for key_norm, value in norm_overrides.items():
                    score = fuzz.token_sort_ratio(normalized_lower, key_norm)
                    if score >= 85:
                        best = value
                        break
                if best:
                    final_dept = best
                    is_override = True
                    matched_canonical = True

        if not is_override:
            # If it's a non-department (location-like), don't try to match
            if is_non_dept:
                final_dept = None
            else:
                # Find best canonical match if no override matched
                canonical = find_best_department_match(raw_dept, threshold=0.6)
                if canonical:
                    final_dept = canonical
                    matched_canonical = True
                else:
                    final_dept = None

        category = get_department_category(final_dept) if final_dept else None
        if category:
            category = category.lower()
        # Calibrate confidence: highest for explicit overrides, medium for canonical matches,
        # lower when we fall back to just the normalized string, zero when we reject.
        if is_override:
            confidence = 0.95
        elif matched_canonical:
            confidence = 0.85
        elif is_non_dept or not final_dept:
            confidence = 0.0
        else:
            confidence = 0.4

        return {
            "raw": raw_dept,
            "normalized": normalized,
            "canonical": final_dept,
            "category": category,
            "is_override": is_override,
            "confidence": confidence,
        }
    except (ValueError, FileNotFoundError):
        return None


def process_title(
    raw_title: Optional[str],
    dept_canonical: Optional[str] = None,
    overrides: Optional[dict[str, str]] = None,
) -> Optional[TitleResult]:
    """
    Normalize and canonicalize job title.

    Args:
        raw_title: Raw title string.

    Returns:
        TitleResult with raw input and normalized variants, or None if invalid.
    """
    if not raw_title or not isinstance(raw_title, str):
        return None

    try:
        result = normalize_title_full(
            raw_title,
            threshold=0.6,
            dept_canonical=dept_canonical,
            overrides=overrides,
        )
        # Return None only if the title is mostly symbols/garbage (no alphanumeric content)
        cleaned = result.get("cleaned", "")
        if cleaned:
            alphanumeric_count = sum(1 for c in cleaned if c.isalnum())
            total_count = len(cleaned)
            # If less than 40% alphanumeric, reject as completely invalid
            if total_count > 0 and alphanumeric_count / total_count < 0.4:
                return None

        return {
            "raw": result.get("raw"),
            "normalized": result.get("cleaned"),
            "canonical": result.get("canonical"),
            "is_valid": result.get("is_valid"),
            "confidence": result.get("confidence", 0.0),
            "seniority": result.get("seniority"),
        }
    except (ValueError, FileNotFoundError):
        return None


def process_address(raw_address: Optional[str]) -> Optional[AddressResult]:
    """Normalize a postal address (US-focused)."""
    try:
        return normalize_address(raw_address)
    except Exception:
        return None


def process_organization(raw_org: Optional[str]) -> Optional[OrganizationResult]:
    """Normalize an organization/agency name."""
    try:
        return normalize_organization(raw_org)
    except Exception:
        return None
