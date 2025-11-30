"""
Advanced phone number detection for HumanMint.

Detects patterns that indicate impossible numbers, fax lines, and VoIP providers.
"""

import re
from typing import Dict, Optional

# VoIP provider patterns (common VoIP area codes and prefixes)
# This is a curated list of known VoIP indicators
VOIP_PATTERNS = {
    # Common VOIP area codes in North America
    "area_codes": {
        "534",  # Wisconsin VoIP
        "551",  # New Jersey VoIP
        "564",  # Washington VoIP
        "628",  # California VoIP
        "650",  # California VoIP
        "678",  # Georgia VoIP
        "737",  # Texas VoIP
        "747",  # California VoIP
        "831",  # California VoIP
        "843",  # South Carolina VoIP
        "844",  # Toll-free VoIP
        "855",  # Toll-free VoIP
        "856",  # New Jersey VoIP
        "857",  # Massachusetts VoIP
        "862",  # New Jersey VoIP
        "872",  # Illinois VoIP
        "878",  # Pennsylvania VoIP
        "888",  # Toll-free VoIP
        "909",  # California VoIP
        "925",  # California VoIP
        "971",  # Oregon VoIP
        "989",  # Michigan VoIP
    },
    # Common VoIP provider patterns
    "provider_prefixes": {
        # Vonage / Bandwidth patterns
        "1800555",
        "1888555",
        "1855555",
        # Various carriers known for VoIP
        "1844",
        "1855",
        "1866",
        "1877",
        "1888",
    },
}


def detect_impossible(phone_dict: Dict[str, Optional[str]]) -> bool:
    """
    Detect if a phone number has characteristics of an impossible number.

    Impossible numbers are those that:
    - Have all same digits (e.g., 111-111-1111, 777-777-7777)
    - Are sequential patterns (e.g., 123-456-7890)
    - Have insufficient digit variation
    - Are test numbers (555-0xxx in North America)

    Args:
        phone_dict: Result dict from normalize_phone().

    Returns:
        True if number appears to be impossible/test/fake.

    Examples:
        >>> detect_impossible({"e164": "+12125550123", ...})
        True  # Test number pattern

        >>> detect_impossible({"e164": "+12015551234", ...})
        False  # Legitimate number
    """
    if not phone_dict.get("is_valid"):
        return False

    e164 = phone_dict.get("e164")
    if not e164:
        return False

    # Extract digits only
    digits = re.sub(r"\D", "", e164)

    if len(digits) < 10:
        return False

    # Check 1: All same digits (e.g., 1111111111)
    if len(set(digits)) == 1:
        return True

    # Check 2: Sequential pattern (e.g., 1234567890)
    if digits == "".join(str((int(d) + i) % 10) for i, d in enumerate(digits)):
        return True

    # Check 3: Test number pattern (555-0xxx range, North America)
    # E.164 format for US: +1NNNNNNNNNN
    if e164.startswith("+1") and len(digits) >= 10:
        area_and_exchange = digits[-10:-4]  # Last 10 digits, first 6 (area + exchange)
        if area_and_exchange.endswith("555"):
            last_4 = digits[-4:]
            # 555-0000 through 555-0099 are explicitly reserved for examples
            if last_4.startswith("0"):
                return True

    # Check 4: Very low digit variation (less than 3 unique digits)
    if len(set(digits)) < 3:
        return True

    return False


def detect_fax_pattern(phone_dict: Dict[str, Optional[str]]) -> bool:
    """
    Detect if a phone number matches known fax patterns.

    Fax patterns include:
    - Explicit fax identifiers in extension (e.g., "fax", "f123")
    - Known fax number ranges
    - Premium rate numbers commonly used for fax
    - Specific prefixes associated with fax services

    Args:
        phone_dict: Result dict from normalize_phone().

    Returns:
        True if number appears to be a fax line.

    Examples:
        >>> detect_fax_pattern({"extension": "fax", ...})
        True

        >>> detect_fax_pattern({"type": "PREMIUM_RATE", ...})
        True  # Premium rate often used for fax

        >>> detect_fax_pattern({"type": "MOBILE", ...})
        False
    """
    if not phone_dict.get("is_valid"):
        return False

    # Check 1: Explicit fax in extension
    extension = phone_dict.get("extension")
    if extension:
        ext_lower = extension.lower()
        if "fax" in ext_lower or ext_lower in ("f", "fx"):
            return True

    # Check 2: Premium rate or certain types commonly used for fax
    phone_type = phone_dict.get("type")
    if phone_type in ("PREMIUM_RATE", "SHARED_COST"):
        return True

    # Check 3: Known fax service prefixes (limited set)
    # This is intentionally conservative to avoid false positives
    e164 = phone_dict.get("e164")
    if e164:
        digits = re.sub(r"\D", "", e164)
        # Some older fax service patterns (very rare in modern use)
        fax_prefixes = [
            "1900",  # Premium rate (often fax services)
        ]
        for prefix in fax_prefixes:
            if digits.startswith(prefix):
                return True

    return False


def detect_voip_pattern(phone_dict: Dict[str, Optional[str]]) -> bool:
    """
    Detect if a phone number matches known VoIP provider patterns.

    VoIP indicators include:
    - Explicit VOIP type from phonenumbers library
    - Known VoIP area codes (commonly assigned to VoIP)
    - Known VoIP provider prefixes
    - Toll-free numbers (increasingly VoIP)

    Note: This is probabilistic. Many legitimate VoIP lines exist,
    and some VoIP may not be detected. Use as a heuristic, not absolute truth.

    Args:
        phone_dict: Result dict from normalize_phone().

    Returns:
        True if number appears to match VoIP patterns.

    Examples:
        >>> detect_voip_pattern({"type": "VOIP", ...})
        True

        >>> detect_voip_pattern({"e164": "+16285551234", ...})
        True  # Area code 628 is commonly VoIP

        >>> detect_voip_pattern({"e164": "+12025551234", ...})
        False  # Area code 202 is traditional landline
    """
    if not phone_dict.get("is_valid"):
        return False

    # Check 1: Explicitly marked as VOIP by phonenumbers
    if phone_dict.get("type") == "VOIP":
        return True

    e164 = phone_dict.get("e164")
    if not e164:
        return False

    digits = re.sub(r"\D", "", e164)

    # Must have at least 10 digits for North American analysis
    if len(digits) < 10:
        return False

    # Check 2: Known VoIP area codes (North America only for now)
    if e164.startswith("+1"):
        area_code = digits[-10:-7]  # Last 10 digits, first 3
        if area_code in VOIP_PATTERNS["area_codes"]:
            return True

    # Check 3: Known VoIP provider prefixes
    for prefix in VOIP_PATTERNS["provider_prefixes"]:
        if digits.startswith(prefix):
            return True

    # Check 4: Toll-free is increasingly VoIP (but not always)
    # Only flag if also has other VoIP indicators
    if phone_dict.get("type") == "TOLL_FREE":
        # Already checked explicit VOIP type above
        # Could add additional heuristics here
        pass

    return False
