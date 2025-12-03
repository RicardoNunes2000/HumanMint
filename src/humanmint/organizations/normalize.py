"""
Normalize organization/agency names.

Removes civic prefixes/suffixes and common noise, expands a few abbreviations,
and returns a canonical lowercase string.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from humanmint.text_clean import normalize_unicode_ascii, strip_garbage

_CIVIC_PREFIXES = [
    "city of",
    "town of",
    "county of",
    "village of",
    "borough of",
    "office of",
    "department of",
    "dept of",
    "dept.",
    "office for",
    "agency of",
    "division of",
]

_NOISE = {"inc", "llc", "ltd", "co", "company", "corporation"}

_ABBREV_MAP = {
    "dpw": "public works",
    "dot": "transportation",
    "pw": "public works",
    "ps": "public safety",
    "pd": "police",
}

ACRONYM_MAP = {
    "usda": "United States Department of Agriculture",
    "epa": "Environmental Protection Agency",
    "fema": "Federal Emergency Management Agency",
    "fdny": "New York City Fire Department",
    "nypd": "New York City Police Department",
    "lapd": "Los Angeles Police Department",
    "lafd": "Los Angeles Fire Department",
    "doj": "Department of Justice",
    "dot": "Department of Transportation",
    "dhhs": "Department of Health and Human Services",
    "hud": "Department of Housing and Urban Development",
}


def _clean(text: str) -> str:
    text = strip_garbage(text)
    text = normalize_unicode_ascii(text)
    text = re.sub(r"[#/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_organization(raw: Optional[str]) -> Optional[Dict[str, Optional[str]]]:
    if not raw or not isinstance(raw, str):
        return None

    cleaned = _clean(raw)
    if not cleaned:
        return None

    lower = cleaned.lower()
    if lower in ACRONYM_MAP:
        canonical = ACRONYM_MAP[lower]
        confidence = 0.9
        return {
            "raw": raw,
            "normalized": lower,
            "canonical": canonical,
            "confidence": confidence,
        }
    for prefix in _CIVIC_PREFIXES:
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip(" ,-/")
            lower = cleaned.lower()
            break

    tokens = [t for t in re.split(r"\s+", lower) if t]
    normalized_tokens = []
    for tok in tokens:
        tok = tok.strip(".,")
        if tok in _NOISE:
            continue
        normalized_tokens.append(_ABBREV_MAP.get(tok, tok))

    normalized = " ".join(normalized_tokens)
    normalized = normalized.strip(" &,-")
    canonical = normalized.title()
    confidence = 0.7 + 0.05 * min(len(normalized_tokens), 4)
    confidence = min(confidence, 0.95)

    return {
        "raw": raw,
        "normalized": normalized,
        "canonical": canonical,
        "confidence": confidence,
    }
