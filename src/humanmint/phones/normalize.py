"""
Phone number normalization for HumanMint.

Parses, validates, and formats phone numbers using the phonenumbers library.
Supports US and international numbers, extensions, and multiple output formats.

Philosophy:
- US-focused: Optimized for US phone numbers in contact data
- Practical: "Can a human reasonably dial this?" > strict telecom validation
- Lenient: Accepts common patterns even if telecom-invalid (e.g., 555 numbers)
- Structured: Always returns consistent dict, never throws, never returns "N/A"
"""

import re
from functools import lru_cache
from typing import Dict, Optional

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType, carrier, geocoder, timezone

# Precompiled regexes for faster parsing
_EXT_KEYWORD_PATTERN = re.compile(
    r'\b(?:ext(?:ension)?|extn|x)\s*[:.]?\s*(\d{1,6})\b',
    re.IGNORECASE,
)
_HASH_PATTERN = re.compile(r'#(\d+)(?:\s|$)')
_MULTI_SPACE_PATTERN = re.compile(r'\s{2,}(\d{2,5})(?:\s|$)')
_TYPE_MAP = {
    PhoneNumberType.MOBILE: "MOBILE",
    PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    PhoneNumberType.SHARED_COST: "SHARED_COST",
    PhoneNumberType.VOIP: "VOIP",
    PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    PhoneNumberType.PAGER: "PAGER",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    PhoneNumberType.UNKNOWN: "UNKNOWN",
}

# Reusable empty template (copied per call to avoid accidental mutation)
_EMPTY_PHONE: Dict[str, Optional[str]] = {
    "e164": None,
    "pretty": None,
    "extension": None,
    "country": None,
    "type": None,
    "is_valid": False,
    "location": None,
    "carrier": None,
    "time_zones": None,
}


def _extract_extension(raw: str) -> tuple[str, Optional[str]]:
    """
    Extract extension from a phone string.

    Handles common extension patterns:
    - "x123", "X123" (x-extension)
    - "ext 123", "ext.123", "ext:123" (extension keyword)
    - "ext fax", "ext fx" (special extension keywords)
    - "#123" (hash extension)
    - " 123" at the end (numeric suffix)

    Args:
        raw: Raw phone string.

    Returns:
        Tuple of (phone_without_extension, extension_or_none).
    """
    if not raw:
        return raw, None

    # Pattern 1: x / ext / extension keywords followed by digits
    # Matches: x123, X456, ext123, ext 789, ext.999, ext:111, extension 77
    match = _EXT_KEYWORD_PATTERN.search(raw)
    if match:
        extension = match.group(1)
        cleaned = _EXT_KEYWORD_PATTERN.sub(' ', raw).strip()
        return cleaned, extension

    # Pattern 2: #123 (hash extension, common in some regions)
    match = _HASH_PATTERN.search(raw)
    if match:
        extension = match.group(1)
        cleaned = _HASH_PATTERN.sub(' ', raw).strip()
        return cleaned, extension

    # Pattern 3: Multiple spaces or trailing numbers that look like extensions
    # Only if there's clearly a gap (e.g., "202 555 1234    123")
    match = _MULTI_SPACE_PATTERN.search(raw)
    if match:
        extension = match.group(1)
        cleaned = _MULTI_SPACE_PATTERN.sub(' ', raw).strip()
        return cleaned, extension

    return raw, None


def _strip_international_prefix(raw: str) -> str:
    """
    Strip leading 00 (common international prefix) and collapse +001 -> +1.
    """
    if not raw:
        return raw
    cleaned = raw.strip()
    # Normalize 00... to +
    cleaned = re.sub(r"^00", "+", cleaned)
    # Collapse +001 to +1
    cleaned = re.sub(r"^\+00?1", "+1", cleaned)
    return cleaned


def _get_phone_type(parsed_number) -> Optional[str]:
    """
    Get the type of phone number (MOBILE, FIXED_LINE, etc.).

    Args:
        parsed_number: Parsed phonenumbers.PhoneNumber object.

    Returns:
        Type string: "MOBILE", "FIXED_LINE", "TOLL_FREE", "UNKNOWN", or None if invalid.
    """
    try:
        number_type = phonenumbers.number_type(parsed_number)
        return _TYPE_MAP.get(number_type, "UNKNOWN")
    except Exception:
        return None


def _empty(
    extension: Optional[str] = None,
    country: Optional[str] = None,
    location: Optional[str] = None,
    carrier_name: Optional[str] = None,
    time_zones: Optional[list[str]] = None,
) -> Dict[str, Optional[str]]:
    """Return empty/invalid phone result."""
    result = _EMPTY_PHONE.copy()
    result["extension"] = extension
    result["country"] = country
    result["location"] = location
    result["carrier"] = carrier_name
    result["time_zones"] = time_zones
    return result


@lru_cache(maxsize=4096)
def _normalize_phone_cached(
    phone_part: str, country: Optional[str], extension: Optional[str]
) -> Dict[str, Optional[str]]:
    """
    Cached normalization core to avoid expensive re-parsing.

    This function uses @lru_cache(maxsize=4096) to cache phone parsing results.
    The phonenumbers library is expensive for large batches; caching dramatically
    improves performance when processing duplicate phone numbers.

    To clear the cache if memory is a concern:
        >>> _normalize_phone_cached.cache_clear()

    To check cache statistics:
        >>> _normalize_phone_cached.cache_info()
    """
    try:
        parsed = phonenumbers.parse(phone_part, country)
    except NumberParseException:
        # Retry without region hint to let international numbers parse
        try:
            parsed = phonenumbers.parse(phone_part, None)
        except NumberParseException:
            return _empty(extension=extension, country=country)

    detected_country = phonenumbers.region_code_for_number(parsed)

    # If region code is None but country code is 1, it's likely a US number (including fictional ranges like 555)
    if detected_country is None and parsed.country_code == 1:
        detected_country = "US"

    # Determine validity
    if detected_country == "US":
        # US numbers: accept if it has 10 digits and valid format structure
        # This includes fictional numbers like 555-xxxx which are valid for testing
        is_valid = (
            phonenumbers.is_possible_number(parsed)
            and len(str(parsed.national_number)) == 10
        )
    else:
        # International: use strict validation
        is_valid = phonenumbers.is_valid_number(parsed)

    # Rough location/description based on number prefix (best-effort, may be empty)
    location = None
    carrier_name = None
    try:
        desc = geocoder.description_for_number(parsed, "en")  # e.g., "New York, NY"
        location = desc or None
    except Exception:
        location = None

    try:
        carr = carrier.name_for_number(parsed, "en")
        carrier_name = carr or None
    except Exception:
        carrier_name = None

    # Determine phone type before time zone handling
    phone_type = _get_phone_type(parsed)

    # Wide-area toll-free numbers: avoid exploding time zones
    if phone_type == "TOLL_FREE":
        time_zones = None
    else:
        time_zones = None
        try:
            tzs = timezone.time_zones_for_number(parsed)
            if tzs:
                tz_list = list(tzs)
                # If too many zones, treat as wide-area
                time_zones = None if len(tz_list) > 5 else tz_list
            else:
                time_zones = None
        except Exception:
            time_zones = None

    if not is_valid:
        return _empty(
            extension=extension,
            country=detected_country,
            location=location,
            carrier_name=carrier_name,
            time_zones=time_zones,
        )

    # Format E.164
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    # Format pretty: use a custom format for US numbers
    if detected_country == "US":
        national = str(parsed.national_number)
        pretty = f"+1 {national[:3]}-{national[3:6]}-{national[6:]}"
    else:
        # Use phonenumbers formatting for other countries
        pretty = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

    phone_type = _get_phone_type(parsed)

    return {
        "e164": e164,
        "pretty": pretty,
        "extension": extension,
        "country": detected_country,
        "type": phone_type,
        "is_valid": True,
        "location": location,
        "carrier": carrier_name,
        "time_zones": time_zones,
    }


def normalize_phone(
    raw: Optional[str], country: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Normalize a phone number to E.164 format and extract metadata.

    Handles:
    - International numbers with country codes
    - Domestic numbers (with optional country hint)
    - Extensions (x, ext, #, etc.)
    - Various formatting styles

    Args:
        raw: Raw phone string (e.g., "(202) 555-1234", "+1-202-555-1234 x123").
        country: Optional ISO 3166-1 alpha-2 country code (e.g., "US", "GB").
                 Used as hint for parsing domestic numbers without country code.

    Returns:
        Dict with keys:
        - e164: Normalized E.164 format (e.g., "+12025551234") or None
        - pretty: Pretty-formatted number (e.g., "(202) 555-1234") or None
        - extension: Extracted extension number or None
        - country: Detected or provided country code or None
        - type: Phone type ("MOBILE", "FIXED_LINE", etc.) or None
        - is_valid: Whether the number is valid

    Examples:
        >>> normalize_phone("(202) 555-1234", country="US")
        {
            "e164": "+12025551234",
            "pretty": "(202) 555-1234",
            "extension": None,
            "country": "US",
            "type": "FIXED_LINE",
            "is_valid": True
        }

        >>> normalize_phone("+1-202-555-1234 x123")
        {
            "e164": "+12025551234",
            "pretty": "+1 202 555 1234",
            "extension": "123",
            "country": "US",
            "type": "FIXED_LINE",
            "is_valid": True
        }
    """
    if not raw or not isinstance(raw, str):
        return _empty()

    # Clean up the input
    raw = raw.strip()
    # Drop inline labels like (home), (office), (work), (cell), (mobile)
    raw = re.sub(r"\(\s*(home|office|work|cell|mobile)\s*\)", "", raw, flags=re.IGNORECASE)
    if not raw:
        return _empty()

    # If multiple numbers are present, pick the first valid one
    # Common separators: "/", ";", ",", " or ", "|" (phone trees, shared lines)
    candidates = re.split(r"(?:/|;|,|\bor\b|\|)", raw)
    first_extension = None
    first_raw_candidate = None
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue

        phone_clean = _strip_international_prefix(candidate)
        phone_part, extension = _extract_extension(phone_clean)
        phone_part = phone_part.strip()
        extension = extension or None
        if first_raw_candidate is None:
            first_raw_candidate = phone_part or phone_clean or candidate
        if first_extension is None:
            first_extension = extension

        if not phone_part:
            continue

        result = _normalize_phone_cached(phone_part, country, extension)
        if result.get("is_valid"):
            return result.copy()

    # If none of the splits validate, return an empty/invalid phone result
    # but preserve the first detected extension (helps when number is malformed)
    # and keep the raw digits so data isn't lost.
    fallback = _empty(extension=first_extension)
    fallback["pretty"] = first_raw_candidate or raw
    return fallback


def extract_phones(text: str, region: str = "US") -> list[Dict[str, Optional[str]]]:
    """
    Extract all phone numbers from free text using phonenumbers.PhoneNumberMatcher.

    Args:
        text: Input string containing phone numbers.
        region: Default region hint (ISO alpha-2) for parsing numbers without country codes.

    Returns:
        List of phone dicts shaped like normalize_phone(), with best-effort location/carrier.
    """
    if not text:
        return []
    results: list[Dict[str, Optional[str]]] = []
    try:
        for match in phonenumbers.PhoneNumberMatcher(text, region):
            parsed = match.number
            # Reuse cached normalization logic with no extension
            normalized = _normalize_phone_cached(
                phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                None,
                None,
            )
            results.append(normalized.copy())
    except Exception:
        return []
    return results
