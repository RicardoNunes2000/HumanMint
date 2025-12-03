"""
Lightweight address normalization (US-focused).

Performs basic parsing:
- Street number + name extraction
- Unit/apartment detection
- City/state/ZIP splitting
- Abbreviation expansion (st -> street, ave -> avenue, nw -> northwest)
- Canonical string assembly

This is intentionally simple; can be swapped for libpostal later.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

try:
    import usaddress  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    usaddress = None

from humanmint.text_clean import normalize_unicode_ascii, strip_garbage

_DIRECTIONALS = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "ne": "northeast",
    "nw": "northwest",
    "se": "southeast",
    "sw": "southwest",
}

_SUFFIXES = {
    "st": "street",
    "street": "street",
    "rd": "road",
    "road": "road",
    "ave": "avenue",
    "av": "avenue",
    "avenue": "avenue",
    "blvd": "boulevard",
    "ln": "lane",
    "lane": "lane",
    "dr": "drive",
    "drive": "drive",
    "hwy": "highway",
    "highway": "highway",
    "pkwy": "parkway",
    "cir": "circle",
    "ctr": "center",
    "ct": "court",
    "ter": "terrace",
    "pl": "place",
}

_US_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}


def _clean_text(raw: str) -> str:
    cleaned = strip_garbage(raw)
    cleaned = normalize_unicode_ascii(cleaned)
    cleaned = cleaned.replace("\n", " ")

    # Heuristic desmash: insert spaces between digit/letter and lower/upper boundaries
    # Avoid splitting ordinals like 5th/21st
    cleaned = re.sub(r"(?<=\d)(?=[A-Za-z])(?![stndrh]{1,2}\b)", " ", cleaned)
    cleaned = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", cleaned)
    cleaned = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cleaned)

    # Normalize ordinals like 5Th -> 5th (before title casing)
    cleaned = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: f"{m.group(1)}{m.group(2).lower()}", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _parse_unstructured_address(cleaned: str) -> Dict[str, Optional[str]]:
    """
    Parse address without comma delimiters using regex patterns.

    Extracts ZIP first (most reliable), then state, then street number,
    then uses heuristics to split street name from city.

    Example:
        "123 Main St Springfield MA 12345" -> street, city, state, ZIP

    Args:
        cleaned: Cleaned address string without commas

    Returns:
        Dictionary with extracted components
    """
    # Extract ZIP code first (most reliable anchor)
    zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", cleaned)
    zip_code = zip_match.group(1) if zip_match else None
    remainder = (
        re.sub(r"\b\d{5}(?:-\d{4})?\b", "", cleaned).strip()
        if zip_code
        else cleaned
    )

    # Extract state (2-letter code)
    state = None
    state_match = re.search(r"\b([A-Z]{2})\b", remainder)
    if state_match and state_match.group(1) in _US_STATES:
        state = state_match.group(1)
        remainder = re.sub(r"\b" + re.escape(state) + r"\b", "", remainder).strip()

    # Extract street number (leading digits)
    street_number = None
    number_match = re.match(r"^(\d+[A-Za-z]?)\s+", remainder)
    if number_match:
        street_number = number_match.group(1)
        remainder = remainder[number_match.end() :].strip()

    # Split street name from city using suffix patterns
    street_name = None
    city = None
    if remainder:
        suffix_pattern = r"\b(" + "|".join(_SUFFIXES.values()) + r")\b"
        suffix_match = re.search(suffix_pattern, remainder, re.IGNORECASE)

        if suffix_match:
            street_name = remainder[: suffix_match.end()].strip()
            city = remainder[suffix_match.end() :].strip() or None
        else:
            # Fallback: assume last word(s) are city
            tokens = remainder.split()
            if len(tokens) >= 2:
                street_name = " ".join(tokens[:-1])
                city = tokens[-1]
            else:
                street_name = remainder
                city = None

    street = " ".join([t for t in [street_number, street_name] if t])
    # Normalize ordinals like 5Th -> 5th
    street = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: f"{m.group(1)}{m.group(2).lower()}", street, flags=re.IGNORECASE)
    return {
        "street": street if street else None,
        "city": city,
        "state": state,
        "zip": zip_code,
    }


def _expand_directional(token: str) -> str:
    low = token.lower().strip(".")
    return _DIRECTIONALS.get(low, token)


def _expand_suffix(token: str) -> str:
    low = token.lower().strip(".")
    return _SUFFIXES.get(low, token)


def _parse_with_usaddress(raw: str) -> Optional[Dict[str, Optional[str]]]:
    """Parse using the `usaddress` library."""
    if usaddress is None:
        return None
    try:
        tagged, _addr_type = usaddress.tag(raw)
    except Exception:
        return None

    def get_tag(*keys: str) -> Optional[str]:
        for key in keys:
            if key in tagged:
                return tagged[key]
        return None

    number = get_tag("AddressNumber")
    predir = get_tag("StreetNamePreDirectional")
    name = get_tag("StreetName")
    posttype = get_tag("StreetNamePostType")
    postdir = get_tag("StreetNamePostDirectional")
    unit = " ".join(
        filter(
            None,
            [
                get_tag("OccupancyType", "SubaddressType"),
                get_tag("OccupancyIdentifier", "SubaddressIdentifier"),
            ],
        )
    ) or None
    city = get_tag("PlaceName")
    state = get_tag("StateName")
    zip_code = get_tag("ZipCode")

    state = state.upper() if state else None
    zip_code = zip_code if zip_code else None

    street_parts = [number, predir, name, posttype, postdir]
    street = " ".join(part for part in street_parts if part)

    raw_lower = raw.lower()
    has_us_indicator = "usa" in raw_lower or "united states" in raw_lower
    is_us_state = state in _US_STATES if state else False
    is_us_zip = bool(zip_code and re.fullmatch(r"\d{5}(?:-\d{4})?", zip_code))

    country = "US" if (is_us_zip or is_us_state or has_us_indicator) else None
    if not is_us_state and country != "US":
        state = None

    canonical_parts = [street if street else None, unit, city, state, zip_code]
    if country:
        canonical_parts.append(country)
    canonical = " ".join(p for p in canonical_parts if p)

    if country == "US":
        confidence = 0.7
        for field in [street, city, state, zip_code]:
            if field:
                confidence += 0.05
        confidence = min(confidence, 0.95)
    else:
        confidence = 0.3
        for field in [street, city, state, zip_code]:
            if field:
                confidence += 0.05
        confidence = min(confidence, 0.5)

    return {
        "raw": raw,
        "street": street or None,
        "unit": unit,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
        "canonical": canonical or None,
        "confidence": confidence,
    }


def normalize_address(raw: Optional[str]) -> Optional[Dict[str, Optional[str]]]:
    """
    Normalize a postal address into components (US-focused).
    """
    if not raw or not isinstance(raw, str):
        return None

    parsed = _parse_with_usaddress(raw)
    if parsed and any(parsed.get(k) for k in ("city", "state", "zip")):
        return parsed

    cleaned = _clean_text(raw)
    if not cleaned:
        return None

    parsed_clean = _parse_with_usaddress(cleaned)
    if parsed_clean and any(parsed_clean.get(k) for k in ("city", "state", "zip", "street")):
        return parsed_clean

    # Check if address has commas (structured) or not (unstructured)
    has_commas = "," in cleaned

    street = street_number = city = state = zip_code = unit = None

    if has_commas:
        # Original comma-based parsing for structured addresses
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        street_part = parts[0] if parts else cleaned
        tail_parts = parts[1:] if len(parts) > 1 else []

        unit = None
        unit_label = None
        # If first part is a unit (suite/apt/ste), capture it and shift street_part to next chunk
        unit_match_leading = re.match(r"^(suite|ste|apt|unit|#)\s*([A-Za-z0-9-]+)", street_part, re.IGNORECASE)
        if unit_match_leading and len(parts) >= 2:
            unit_label = unit_match_leading.group(1)
            unit = unit_match_leading.group(2)
            street_part = parts[1]
            tail_parts = parts[2:] if len(parts) > 2 else []
        else:
            unit_match = re.search(r"(suite|ste|apt|unit|#)\s*([A-Za-z0-9-]+)", street_part, re.IGNORECASE)
            if unit_match:
                unit_label = unit_match.group(1)
                unit = unit_match.group(2)
                street_part = street_part[: unit_match.start()].strip()

        street_tokens = street_part.split()
        street_number = None
        street_name_tokens = []
        if street_tokens and re.match(r"\d+[A-Za-z]?$", street_tokens[0]):
            street_number = street_tokens[0]
            street_name_tokens = street_tokens[1:]
        else:
            street_name_tokens = street_tokens

        expanded_tokens = []
        for tok in street_name_tokens:
            if tok.lower().strip(".") in _DIRECTIONALS:
                expanded_tokens.append(_expand_directional(tok))
            else:
                expanded_tokens.append(_expand_suffix(tok))
        street_name = " ".join(expanded_tokens).title() if expanded_tokens else None
        street = " ".join([t for t in [street_number, street_name] if t])

        city = state = zip_code = None
        if tail_parts:
            state_zip_part = tail_parts[-1]
            zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", state_zip_part)
            if zip_match:
                zip_code = zip_match.group(1)
            state_match = re.search(r"\b([A-Za-z]{2})\b", state_zip_part)
            if state_match:
                state = state_match.group(1).upper()
            if len(tail_parts) >= 2:
                city = tail_parts[-2].title() if tail_parts[-2] else None
        else:
            # Try inline city/state/zip
            zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", cleaned)
            if zip_match:
                zip_code = zip_match.group(1)
            state_match = re.search(r"\b([A-Za-z]{2})\b", cleaned)
            if state_match:
                state = state_match.group(1).upper()
    else:
        # Use smart non-comma parser for unstructured addresses
        parsed = _parse_unstructured_address(cleaned)
        street = parsed["street"]
        city = parsed["city"]
        state = parsed["state"]
        zip_code = parsed["zip"]

        # Extract unit if present
        unit_match = re.search(r"(suite|ste|apt|unit|#)\s*([A-Za-z0-9-]+)", cleaned, re.IGNORECASE)
        if unit_match:
            unit = unit_match.group(2)
            if not unit_label:
                unit_label = unit_match.group(1)

        # Titlecase city if found
        if city:
            city = city.title()
    raw_lower = raw.lower()
    has_us_indicator = "usa" in raw_lower or "united states" in raw_lower
    is_us_state = state in _US_STATES if state else False
    is_us_zip = bool(zip_code and re.fullmatch(r"\d{5}(?:-\d{4})?", zip_code))
    country = "US" if (is_us_zip or is_us_state or has_us_indicator) else None
    if not is_us_state and country != "US":
        state = None

    unit_str = None
    if unit:
        label = unit_label or "Apt"
        # Normalize label formatting
        if label.lower() in {"#", "unit"}:
            unit_str = f"{label} {unit}"
        elif label.lower() in {"suite", "ste"}:
            unit_str = f"Suite {unit}"
        else:
            unit_str = f"Apt {unit}"

    canonical_parts = [p for p in [street, unit_str, city, state, zip_code] if p]
    if country:
        canonical_parts.append(country)
    canonical = " ".join(canonical_parts) if canonical_parts else None

    if country == "US":
        confidence = 0.5
        for field in [street, city, state, zip_code]:
            if field:
                confidence += 0.1
        confidence = min(confidence, 0.98)
    else:
        confidence = 0.3
        for field in [street, city, zip_code]:
            if field:
                confidence += 0.05
        confidence = min(confidence, 0.5)

    return {
        "raw": raw,
        "street": street if street else None,
        "unit": unit,
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": country,
        "canonical": canonical,
        "confidence": confidence,
    }
