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

import re
from functools import lru_cache
from typing import Optional

from rapidfuzz import fuzz

from .addresses import normalize_address
from .constants.names import NON_PERSON_PHRASES, ROMAN_NUMERALS
from .data.utils import load_package_json_gz
from .departments import find_best_match as find_best_department_match
from .departments import get_department_category, normalize_department
from .departments.matching import is_likely_non_department
from .emails import normalize_email
from .names import enrich_name, normalize_name
from .names.matching import detect_nickname
from .names.normalize import _strip_noise
from .organizations import normalize_organization
from .phones import normalize_phone
from .semantics import _extract_domains
from .titles import normalize_title_full
from .types import (AddressResult, DepartmentResult, EmailResult, NameResult,
                    OrganizationResult, PhoneResult, TitleResult)


@lru_cache(maxsize=1)
def _name_token_set() -> set[str]:
    """Load name tokens from names.json.gz for quick person scoring.

    Returns:
        Set of lowercase name tokens from cached names data, empty set on error.
    """
    try:
        data = load_package_json_gz("names.json.gz")
        return {k.lower() for k in data.keys()}
    except Exception:
        return set()


@lru_cache(maxsize=1)
def _semantic_token_map() -> dict[str, Optional[str]]:
    """Load semantic tokens map (token -> category) for org/person heuristics.

    Returns:
        Mapping of lowercase tokens to their semantic category, empty dict on error.
    """
    try:
        data = load_package_json_gz("semantic_tokens.json.gz")
        return {k.lower(): (v.lower() if isinstance(v, str) else None) for k, v in data.items()}
    except Exception:
        return {}


def _tokenize_lower(text: str) -> list[str]:
    """Lowercase, tokenized words (alpha/numeric/apostrophe) for scoring.

    Args:
        text: Text to tokenize.

    Returns:
        List of lowercase alphanumeric/apostrophe tokens.
    """
    return re.findall(r"[a-z0-9']+", text.lower())


def _person_org_score(text: str) -> tuple[float, float, bool]:
    """Compute lightweight person vs. org score.

    Uses name token presence, non-person phrases/patterns, and semantic token categories
    to estimate whether text is a person name or organization name.

    Args:
        text: Text to score.

    Returns:
        Tuple of (person_score, org_score, is_likely_org_from_patterns).
            Higher scores indicate stronger match for that category.
    """
    tokens = _tokenize_lower(text)
    if not tokens:
        return (0.0, 0.0, False, 0, 0)

    names = _name_token_set()
    semantic = _semantic_token_map()

    person_score = 0.0
    org_score = 0.0
    lower = text.lower()

    # Strong org patterns that should nearly always be treated as non-person
    strong_org_patterns = [
        r"^city of\s+",
        r"\bboard of\b",
        r"\bcommissioners?\b",
        r"\blibrary\b",
        r"\bhelp\s+support\b",
    ]
    strong_org = any(re.search(pat, lower) for pat in strong_org_patterns)

    # Non-person phrase hits add org weight
    for phrase in NON_PERSON_PHRASES:
        if phrase in lower:
            org_score += 3.0

    for tok in tokens:
        if tok in names:
            person_score += 2.0
        if any(ch.isdigit() for ch in tok):
            org_score += 0.75

        cat = semantic.get(tok)
        if cat and cat != "null":
            org_score += 1.0
            if cat in {
                "admin",
                "edu",
                "finance",
                "planning",
                "infra",
                "safety",
                "social",
                "legal",
                "health",
                "it",
            }:
                org_score += 0.5

    name_hits = sum(1 for t in tokens if t in names)

    return person_score, org_score, strong_org, name_hits, len(tokens)


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
            m = re.search(r"[\"']([^\"']{2,})[\"']", raw_name)
            if m:
                nickname = m.group(1).strip()
            # Capture parenthesized nickname if present
            if not nickname:
                m2 = re.search(r"\(([^()]{2,})\)", raw_name)
                if m2:
                    nickname = m2.group(1).strip()

        if aggressive_clean:
            from .names.garbled import (clean_garbled_name,
                                        should_use_garbled_cleaning)

            # Auto-detect if cleaning is needed
            if should_use_garbled_cleaning(raw_name):
                cleaned = clean_garbled_name(raw_name)
                if cleaned:
                    cleaned_name = cleaned

        # Light noise strip before scoring/gating
        cleaned_name = _strip_noise(cleaned_name)

        # Track if the cleaned string strongly resembles a department or organization.
        dept_hint = False
        org_hint = False
        cleaned_lower = cleaned_name.lower()

        # Reject obvious placeholders like TBD that slip through noise stripping
        if re.search(r"\btbd\b", cleaned_lower):
            return None

        # Person vs org scoring based on tokens/semantics
        person_score, org_score, strong_org, name_hits, token_count = _person_org_score(
            cleaned_name
        )

        # Single-token with a known name hit should not be blocked by org heuristics
        if token_count == 1 and name_hits >= 1:
            org_score = 0.0
            strong_org = False
        try:
            dept_norm = normalize_department(cleaned_name)
            dept_match = find_best_department_match(cleaned_name, threshold=0.7)
            if dept_match:
                dept_hint = True
            elif (
                dept_norm
                and dept_norm.lower() != cleaned_lower
                and not is_likely_non_department(dept_norm)
            ):
                dept_hint = True
        except Exception:
            pass

        try:
            org_norm = normalize_organization(cleaned_name)
            if org_norm and org_norm.get("confidence", 0.0) >= 0.9:
                org_hint = True
        except Exception:
            pass

        # Gate obvious org/department strings before deep name parsing
        if strong_org:
            return None
        if (org_score - person_score) >= 1.5 and org_score >= 2.0:
            return None
        if org_score >= 3.5 and person_score <= 1.0:
            return None
        if name_hits == 0 and token_count >= 2 and (
            (org_score - person_score) >= 1.5 or org_score >= 3.0 or org_hint or dept_hint
        ):
            return None

        normalized = normalize_name(cleaned_name)
        enriched = enrich_name(normalized)

        if not (enriched.get("full") or enriched.get("is_valid")):
            if dept_hint or org_hint or org_score > person_score:
                return None
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

        # Display version of suffix (roman numerals uppercased, otherwise capitalized)
        suffix_display = None
        if suffix_name:
            suffix_lower = suffix_name.lower()
            if suffix_lower in {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}:
                suffix_display = suffix_lower.upper()
            else:
                suffix_display = ROMAN_NUMERALS.get(suffix_name, suffix_name.capitalize())

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

        # Reject organization/department-like strings masquerading as names
        canon_lower = canonical_val.lower()
        if canon_lower in NON_PERSON_PHRASES:
            return None
        # Two-word org-like combos (e.g., "information desk", "general services")
        if len(canon_lower.split()) <= 3:
            tokens = canon_lower.split()
            org_keywords = {
                "services",
                "service",
                "resources",
                "desk",
                "center",
                "administration",
                "department",
                "operations",
            }
            if any(t in org_keywords for t in tokens) and not suffix_type:
                return None

        def _guess_salutation(gender_val: Optional[str]) -> Optional[str]:
            """Map detected gender to a salutation; keep neutral when unknown."""
            if not gender_val or gender_val == "unknown":
                return None
            gender_val = gender_val.lower()
            if gender_val == "male":
                return "Mr."
            if gender_val == "female":
                return "Ms."
            if gender_val in {"nonbinary", "non-binary"}:
                return "Mx."
            return None

        return {
            "raw": raw_name,
            "first": first_name or "",
            "middle": middle_name,
            "last": last_name or "",
            "suffix": suffix_name,
            "suffix_type": suffix_type,
            "full": " ".join(
                p for p in [first_name, middle_name, last_name, suffix_display] if p
            )
            or raw_name,
            "gender": gender,
            "nickname": nickname,
            "canonical": canonical_val,
            "is_valid": enriched.get("is_valid", False),
            "salutation": _guess_salutation(gender),
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
                "location": result.get("location"),
                "carrier": result.get("carrier"),
                "time_zones": result.get("time_zones"),
            }
        return None
    except (ValueError, TypeError, FileNotFoundError):
        return None


def process_department(
    raw_dept: Optional[str],
    overrides: Optional[dict[str, str]] = None,
    title_canonical: Optional[str] = None,
) -> Optional[DepartmentResult]:
    """
    Normalize department and apply overrides.

    Args:
        raw_dept: Raw department string.
        overrides: Optional custom department mappings.

    Returns:
        DepartmentResult with raw input and normalized variants, or None if invalid.
    """
    if (not raw_dept or not isinstance(raw_dept, str)) and not title_canonical:
        return None

    IT_TOKENS = {
        "it",
        "information",
        "technology",
        "technologist",
        "software",
        "developer",
        "engineer",
        "engineering",
        "programmer",
        "web",
        "website",
        "digital",
        "online",
        "internet",
        "devops",
    }
    WATER_TOKENS = {
        "water",
        "wastewater",
        "sewer",
        "sewerage",
        "utilities",
        "utility",
        "hydrant",
        "pipe",
        "plumber",
    }

    def _infer_domains_from_text(text: Optional[str]) -> set[str]:
        """Infer functional domains (IT, WATER, etc.) from text tokens.

        Args:
            text: Text to analyze, or None.

        Returns:
            Set of domain codes inferred from vocabulary and token analysis.
        """
        if not text:
            return set()
        tokens = set(re.findall(r"[a-z0-9']+", text.lower()))
        domains = set()
        vocab_domains = {d.upper() for d in _extract_domains(text)}
        if vocab_domains:
            domains |= vocab_domains
        if tokens & IT_TOKENS:
            domains.add("IT")
        if tokens & WATER_TOKENS:
            domains.add("WATER")
        return domains

    try:
        normalized = normalize_department(raw_dept) if raw_dept else None
        is_non_dept = is_likely_non_department(normalized)
        inferred_canonical = None

        dept_domains = _infer_domains_from_text(normalized or raw_dept)
        title_domains = _infer_domains_from_text(title_canonical)

        # Preserve generic business departments that should not remap (e.g., Accounting)
        if normalized and normalized.lower() == "accounting":
            return {
                "raw": raw_dept,
                "normalized": normalized,
                "canonical": normalized,
                "category": get_department_category(normalized.lower()) or None,
                "is_override": False,
                "confidence": 0.85,
            }

        # Explicit mapping for web/digital/online/website keywords (prefer IT over fuzzy)
        if normalized:
            if re.search(r"\b(web|website|digital|online|internet)\b", normalized.lower()):
                inferred_canonical = "Information Technology"

        # Disambiguate abbreviated "W." departments using title domains
        ambiguous_w = False
        if raw_dept and re.match(r"^\s*w\.?\b", raw_dept, flags=re.IGNORECASE):
            ambiguous_w = True

        if not inferred_canonical and ambiguous_w:
            if "IT" in title_domains and "WATER" not in title_domains:
                inferred_canonical = "Information Technology"
            elif "WATER" in title_domains and "IT" not in title_domains:
                inferred_canonical = "Water"
            # If still ambiguous, leave None to allow overrides/fuzzy/no match

        # Explicit mapping for web/digital/website style departments (IT context)
        if "IT" in dept_domains and not inferred_canonical:
            inferred_canonical = "Information Technology"
        elif "WATER" in dept_domains and not inferred_canonical:
            inferred_canonical = "Water"

        # Check if normalized department matches any override
        is_override = False
        matched_canonical = False
        final_dept = inferred_canonical or normalized

        # Lock in strong inference before fuzzy matching
        if inferred_canonical:
            final_dept = inferred_canonical
            matched_canonical = True
        if overrides:
            normalized_lower = (normalized or "").lower()
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
            if is_non_dept and not inferred_canonical:
                final_dept = None
            else:
                if not matched_canonical:
                    # Prefer canonical match first
                    canonical = find_best_department_match(raw_dept, threshold=0.6) if raw_dept else None
                    if canonical:
                        final_dept = canonical
                        matched_canonical = True
                    elif not raw_dept and title_domains:
                        # Infer from title domains when no department provided
                        if "IT" in title_domains:
                            final_dept = "Information Technology"
                            matched_canonical = True
                        elif "WATER" in title_domains:
                            final_dept = "Water"
                            matched_canonical = True
                    else:
                        final_dept = None

        if not final_dept and normalized and not is_non_dept:
            final_dept = normalized

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
    """Normalize a postal address (US-focused).

    Args:
        raw_address: Raw address string, or None.

    Returns:
        AddressResult dict with normalized fields, or None on error or empty input.

    Example:
        >>> result = process_address("123 Main St, Springfield, IL 62701")
        >>> result.get("street")
        '123 Main Street'
    """
    try:
        return normalize_address(raw_address)
    except Exception:
        return None


def process_organization(raw_org: Optional[str]) -> Optional[OrganizationResult]:
    """Normalize an organization/agency name.

    Args:
        raw_org: Raw organization name, or None.

    Returns:
        OrganizationResult dict with normalized fields, or None on error or empty input.

    Example:
        >>> result = process_organization("City of Springfield Dept. of Public Works")
        >>> result.get("canonical")
        'Springfield City'
    """
    try:
        return normalize_organization(raw_org)
    except Exception:
        return None
