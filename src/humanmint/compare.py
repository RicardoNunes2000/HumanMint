"""
Lightweight similarity scoring between two MintResult objects.

Useful for deduplication, clustering, and comparing extracted contacts.
Returns a 0-100 score (higher = more similar).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Mapping, Optional

from rapidfuzz import fuzz

from .mint import MintResult
from .names.matching import compare_first_names, compare_last_names

DEFAULT_COMPARE_WEIGHTS: dict[str, float] = {
    "name": 0.4,
    "email": 0.4,
    "phone": 0.4,
    "department": 0.2,
    "title": 0.2,
}


def _safe_lower(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    return str(val).lower()


def _exact_match_score(val1: Optional[str], val2: Optional[str]) -> float:
    if not val1 or not val2:
        return 0.0
    return 100.0 if _safe_lower(val1) == _safe_lower(val2) else 0.0


def _fuzzy_score(val1: Optional[str], val2: Optional[str]) -> float:
    if not val1 or not val2:
        return 0.0
    return float(fuzz.token_set_ratio(val1, val2))


def _ascii_fold(text: Optional[str]) -> str:
    """Fold accents and strip non-ASCII characters for stable comparisons."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", str(text))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.encode("ascii", "ignore").decode("ascii")


def _clean_component(text: Optional[str]) -> str:
    """Lowercase, ASCII-only component with punctuation removed."""
    folded = _ascii_fold(text)
    folded = folded.replace("-", " ")
    folded = re.sub(r"[^a-zA-Z\s]", " ", folded)
    return re.sub(r"\s+", " ", folded).strip().lower()


def _clean_full_name(name_obj: dict) -> str:
    """Fallback cleaned full/canonical name string."""
    source = name_obj.get("canonical") or name_obj.get("full") or ""
    folded = _ascii_fold(source)
    folded = re.sub(r"[^a-z0-9]+", " ", folded.lower())
    return re.sub(r"\s+", " ", folded).strip()


def _name_score(name_a: Optional[dict], name_b: Optional[dict]) -> float:
    if not name_a or not name_b:
        return 0.0
    first_a = _clean_component(name_a.get("first"))
    first_b = _clean_component(name_b.get("first"))
    last_a = _clean_component(name_a.get("last"))
    last_b = _clean_component(name_b.get("last"))
    middle_a = _clean_component(name_a.get("middle"))
    middle_b = _clean_component(name_b.get("middle"))
    full_a = _clean_full_name(name_a)
    full_b = _clean_full_name(name_b)

    use_components = bool(first_a and first_b and last_a and last_b)
    first_score = last_score = swapped_score = 0.0

    if use_components:
        first_score = compare_first_names(first_a, first_b)
        last_score = compare_last_names(last_a, last_b)
        base = 100 * (0.35 * first_score + 0.55 * last_score)

        if middle_a or middle_b:
            if middle_a and middle_b:
                if middle_a == middle_b:
                    base += 5
                elif middle_a[:1] == middle_b[:1]:
                    base += 3
                else:
                    base -= 5
            else:
                base -= 2

        # Initial + last match still strong
        if first_a[:1] == first_b[:1] and last_a == last_b:
            base = max(base, 82)

        swapped_score = 100 * (
            0.35 * compare_first_names(first_a, last_b, use_nicknames=False)
            + 0.55 * compare_last_names(last_a, first_b)
        )
        base = max(base, swapped_score * 0.9)
    else:
        base = 0.0

    # Fallback to fuzzy full-name comparison when components are messy/missing
    if full_a and full_b:
        fuzzy_full = float(fuzz.token_set_ratio(full_a, full_b))
        base = max(base, fuzzy_full)

    # Guardrails on partial matches
    if use_components:
        if swapped_score >= 80:
            pass
        elif last_score == 1.0 and first_score < 0.5:
            if first_a[:1] != first_b[:1]:
                base = min(base, 24)
            else:
                base = max(base, 75)
        if first_score >= 0.95 and last_score < 0.5 and swapped_score < 80:
            base = min(base, 52)
        if first_score < 0.65 and last_score < 0.9 and swapped_score < 80:
            base = min(base, 58)

    return max(0.0, min(100.0, base))


def _weighted_average(pairs: list[tuple[float, float]]) -> float:
    total_weight = sum(w for _, w in pairs)
    if total_weight == 0:
        return 0.0
    return sum(score * w for score, w in pairs) / total_weight


def compare(
    result_a: MintResult,
    result_b: MintResult,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    """
    Compare two MintResult objects and return a similarity score (0-100).

    Dynamic weighting: only counts signals that exist on both sides, and normalizes
    by available weight so email-only or phone-only records still score highly.

    Args:
        result_a: First MintResult to compare.
        result_b: Second MintResult to compare.
        weights: Optional mapping to override signal weights. Supported keys are
            "name", "email", "phone", "department", and "title". Any omitted keys
            fall back to the defaults used today.
    """
    weight_config = {**DEFAULT_COMPARE_WEIGHTS, **(weights or {})}
    # Ensure no negative weights
    weight_config = {k: max(0.0, v) for k, v in weight_config.items()}

    def _weight_ratio(key: str) -> float:
        default = DEFAULT_COMPARE_WEIGHTS.get(key, 0.0)
        if default <= 0:
            return 0.0
        weight = weight_config.get(key, default)
        # Scale to default, but cap at 1.0 so floors/penalties do not exceed defaults
        return min(weight / default, 1.0)

    # Collect weighted contributions (each field contributes score * weight to final)
    weighted_contributions: list[float] = []
    active_weights: list[float] = []

    # Names
    name_score = _name_score(result_a.name, result_b.name)
    if result_a.name and result_b.name:
        weighted_contributions.append(name_score * weight_config["name"])
        active_weights.append(weight_config["name"])

    # Email
    email_norm_a = result_a.email.get("normalized") if result_a.email else None
    email_norm_b = result_b.email.get("normalized") if result_b.email else None
    email_score = _exact_match_score(email_norm_a, email_norm_b)
    if email_norm_a and email_norm_b:
        if email_score == 0.0:
            # Parse email components
            local_a, _, domain_a = email_norm_a.partition("@")
            local_b, _, domain_b = email_norm_b.partition("@")

            # Same domain comparison
            if domain_a == domain_b:
                # Remove plus-aliases for base comparison
                base_a = local_a.split("+", 1)[0]
                base_b = local_b.split("+", 1)[0]

                if base_a == base_b:
                    # Same base (e.g., john+work vs john+personal)
                    email_score = 95.0
                else:
                    # Different bases but same domain - check similarity
                    # Handle common patterns: rchen vs robert.chen, jsmith vs john.smith
                    base_a_clean = base_a.replace(".", "").replace("-", "").replace("_", "")
                    base_b_clean = base_b.replace(".", "").replace("-", "").replace("_", "")

                    # Check if one is substring of the other (e.g., rchen in robert.chen)
                    if base_a_clean in base_b_clean or base_b_clean in base_a_clean:
                        email_score = 70.0
                    else:
                        # Fuzzy match on local parts (same domain suggests related)
                        fuzzy_local = fuzz.ratio(base_a_clean, base_b_clean)
                        if fuzzy_local >= 80:
                            email_score = 65.0
                        elif fuzzy_local >= 60:
                            email_score = 50.0

        weighted_contributions.append(email_score * weight_config["email"])
        active_weights.append(weight_config["email"])

    # Phone (prefer E.164)
    phone_a = result_a.phone or {}
    phone_b = result_b.phone or {}
    phone_e164_a = phone_a.get("e164")
    phone_e164_b = phone_b.get("e164")
    phone_pretty_a = phone_a.get("pretty")
    phone_pretty_b = phone_b.get("pretty")
    phone_score = _exact_match_score(phone_e164_a, phone_e164_b)
    if phone_score == 0.0:
        phone_score = _exact_match_score(phone_pretty_a, phone_pretty_b)
    if (phone_e164_a or phone_pretty_a) and (phone_e164_b or phone_pretty_b):
        weighted_contributions.append(phone_score * weight_config["phone"])
        active_weights.append(weight_config["phone"])

    # Department canonical fuzzy
    score_penalty = 0.0
    dept_score = _fuzzy_score(
        (result_a.department or {}).get("canonical"),
        (result_b.department or {}).get("canonical"),
    )
    if result_a.department and result_b.department:
        weighted_contributions.append(dept_score * weight_config["department"])
        active_weights.append(weight_config["department"])
        dept_can_a = _safe_lower((result_a.department or {}).get("canonical"))
        dept_can_b = _safe_lower((result_b.department or {}).get("canonical"))
        if (
            weight_config["department"] > 0
            and dept_can_a
            and dept_can_b
            and dept_can_a != dept_can_b
        ):
            score_penalty += 15.0

    # Title canonical fuzzy
    title_can_a = (result_a.title or {}).get("canonical")
    title_can_b = (result_b.title or {}).get("canonical")
    title_clean_a = (result_a.title or {}).get("cleaned")
    title_clean_b = (result_b.title or {}).get("cleaned")
    title_score = max(
        _fuzzy_score(title_can_a, title_can_b),
        _fuzzy_score(title_clean_a, title_clean_b),
    )
    # Penalize titles that only share generic tokens (chief/officer/manager) but differ otherwise
    generic_tokens = {"chief", "officer", "manager", "director"}
    if title_score > 0:
        tokens_a = {t for t in (title_can_a or "").split() if t}
        tokens_b = {t for t in (title_can_b or "").split() if t}
        clean_tokens_a = {t for t in (title_clean_a or "").lower().split() if t}
        clean_tokens_b = {t for t in (title_clean_b or "").lower().split() if t}
        overlap = {t for t in tokens_a.intersection(tokens_b) if t not in generic_tokens}
        clean_overlap = {t for t in clean_tokens_a.intersection(clean_tokens_b) if t not in generic_tokens}
        strong_clean_match = _fuzzy_score(title_clean_a, title_clean_b) >= 85
        if not overlap and not clean_overlap:
            if strong_clean_match:
                title_score = max(75.0, min(title_score, 90.0))
            else:
                title_score = min(title_score, 35.0)

    if result_a.title and result_b.title:
        weighted_contributions.append(title_score * weight_config["title"])
        active_weights.append(weight_config["title"])

    # Calculate final score: each field contributes (score/100 * weight) points
    # Weights represent the maximum points each field can contribute
    # Sum of all weights = maximum possible score
    score = sum(weighted_contributions) / 100.0  # Since each contribution is score * weight

    # Normalize to 0-100 scale based on sum of active weights
    max_possible = sum(active_weights)
    if max_possible > 0:
        score = (score / max_possible) * 100.0
    else:
        score = 0.0

    # Gender penalty if conflicting and both present and name is weighted
    gender_a = _safe_lower((result_a.name or {}).get("gender"))
    gender_b = _safe_lower((result_b.name or {}).get("gender"))
    if weight_config["name"] > 0 and gender_a and gender_b and gender_a != gender_b:
        score -= 3.0 * _weight_ratio("name")
    score -= score_penalty * _weight_ratio("department")

    # Strong name agreement should not collapse entirely from other disagreements
    if weight_config["name"] > 0 and name_score >= 95.0:
        score = max(score, 45.0 * _weight_ratio("name"))

    # If we have strong identifiers (email/phone) matching exactly, ensure a high floor
    email_floor = 90.0 * _weight_ratio("email") if weight_config["email"] > 0 and email_score == 100.0 else 0.0
    phone_floor = 90.0 * _weight_ratio("phone") if weight_config["phone"] > 0 and phone_score == 100.0 else 0.0
    if email_floor > 0 or phone_floor > 0:
        score = max(score, max(email_floor, phone_floor))

    return max(0.0, min(100.0, score))
