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
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


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
    if parsed:
        return parsed

    cleaned = _clean_text(raw)
    if not cleaned:
        return None

    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    street_part = parts[0] if parts else cleaned
    tail_parts = parts[1:] if len(parts) > 1 else []

    unit = None
    unit_match = re.search(r"(?:apt|unit|#)\s*([A-Za-z0-9-]+)", street_part, re.IGNORECASE)
    if unit_match:
        unit = unit_match.group(1)
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

    street = " ".join([t for t in [street_number, street_name] if t])
    raw_lower = raw.lower()
    has_us_indicator = "usa" in raw_lower or "united states" in raw_lower
    is_us_state = state in _US_STATES if state else False
    is_us_zip = bool(zip_code and re.fullmatch(r"\d{5}(?:-\d{4})?", zip_code))
    country = "US" if (is_us_zip or is_us_state or has_us_indicator) else None
    if not is_us_state and country != "US":
        state = None

    canonical_parts = [p for p in [street, f"Apt {unit}" if unit else None, city, state, zip_code] if p]
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
