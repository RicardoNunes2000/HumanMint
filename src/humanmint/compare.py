"""
Lightweight similarity scoring between two MintResult objects.

Useful for deduplication, clustering, and comparing extracted contacts.
Returns a 0-100 score (higher = more similar).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Mapping, Optional, Tuple, Union

from rapidfuzz import fuzz

from .mint import MintResult
from .names.matching import compare_first_names, compare_last_names
from .semantics import _extract_domains, check_semantic_conflict

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
    explain: bool = False,
) -> Union[float, Tuple[float, list[str]]]:
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
        explain: If True, returns (score, explanation_lines) with a breakdown of signals and penalties.
    """
    weight_config = {**DEFAULT_COMPARE_WEIGHTS, **(weights or {})}
    weight_pairs: list[tuple[float, float]] = []
    explanations: list[str] = []

    # Names
    name_score = _name_score(result_a.name, result_b.name)
    if result_a.name and result_b.name:
        weight_pairs.append((name_score, weight_config["name"]))
        explanations.append(f"name: {name_score:.1f} (weight {weight_config['name']})")

    # Email
    email_norm_a = result_a.email.get("normalized") if result_a.email else None
    email_norm_b = result_b.email.get("normalized") if result_b.email else None
    email_score = _exact_match_score(email_norm_a, email_norm_b)
    if email_norm_a and email_norm_b:
        if email_score == 0.0:
            # Treat plus aliases as same user if domain/local_base match
            local_a, _, domain_a = email_norm_a.partition("@")
            local_b, _, domain_b = email_norm_b.partition("@")
            base_a = local_a.split("+", 1)[0]
            base_b = local_b.split("+", 1)[0]
            if domain_a == domain_b and base_a == base_b:
                email_score = 95.0
        weight_pairs.append((email_score, weight_config["email"]))
        explanations.append(f"email: {email_score:.1f} (weight {weight_config['email']})")

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
        weight_pairs.append((phone_score, weight_config["phone"]))
        explanations.append(f"phone: {phone_score:.1f} (weight {weight_config['phone']})")

    # Department canonical fuzzy
    score_penalty = 0.0
    dept_score = _fuzzy_score(
        (result_a.department or {}).get("canonical"),
        (result_b.department or {}).get("canonical"),
    )
    if result_a.department and result_b.department:
        weight_pairs.append((dept_score, weight_config["department"]))
        dept_can_a = _safe_lower((result_a.department or {}).get("canonical"))
        dept_can_b = _safe_lower((result_b.department or {}).get("canonical"))
        if (
            weight_config["department"] > 0
            and dept_can_a
            and dept_can_b
            and dept_can_a != dept_can_b
        ):
            score_penalty += 15.0
            explanations.append("penalty: -15.0 (department mismatch)")
        explanations.append(f"department: {dept_score:.1f} (weight {weight_config['department']})")

    # Title canonical fuzzy
    title_can_a = (result_a.title or {}).get("canonical")
    title_can_b = (result_b.title or {}).get("canonical")
    title_clean_a = (result_a.title or {}).get("normalized")
    title_clean_b = (result_b.title or {}).get("normalized")
    title_score = max(
        _fuzzy_score(title_can_a, title_can_b),
        _fuzzy_score(title_clean_a, title_clean_b),
    )

    # Semantic safeguard: veto cross-domain title matches
    # Check both canonical and cleaned versions for semantic conflicts
    has_semantic_conflict = False
    if title_can_a and title_can_b:
        has_semantic_conflict = check_semantic_conflict(title_can_a, title_can_b)
    if not has_semantic_conflict and title_clean_a and title_clean_b:
        has_semantic_conflict = check_semantic_conflict(title_clean_a, title_clean_b)

    # If semantic conflict detected, heavily penalize the score
    if has_semantic_conflict:
        title_score = min(title_score, 35.0)
        explanations.append("penalty: semantic conflict cap on title (≤35)")

    # Check if this is a seniority variation EARLY (before other penalties)
    # This prevents legitimate variations like "manager" vs "senior manager" from being penalized
    seniority_words = {"senior", "interim", "acting", "deputy", "assistant", "associate", "lead", "principal"}
    is_seniority_variation = False

    # Strategy 1: Check if one is a substring of the other (e.g., "director" in "interim director")
    if title_can_a and title_can_b:
        can_a_lower = (title_can_a or "").lower()
        can_b_lower = (title_can_b or "").lower()
        # Check if one contains the other
        if (can_a_lower in can_b_lower or can_b_lower in can_a_lower):
            # Check if the extra words are only seniority/temporal markers
            if can_a_lower in can_b_lower:
                extra_text = can_b_lower.replace(can_a_lower, "").strip()
            else:
                extra_text = can_a_lower.replace(can_b_lower, "").strip()

            extra_words = {w for w in extra_text.split() if w}
            if extra_words and extra_words.issubset(seniority_words):
                is_seniority_variation = True

    # Additional safeguard: if one title has clear semantic domains and the other
    # doesn't (or is all NULL), penalize heavily to avoid false positives
    # (e.g., "Network Engineer" vs "Environmental Engineer" where "environmental"→NULL)
    # BUT: skip this check if it's a seniority variation
    if not is_seniority_variation and title_can_a and title_can_b:
        domains_a = _extract_domains(title_can_a)
        domains_b = _extract_domains(title_can_b)
        # One has domains, the other doesn't → likely cross-domain mismatch
        if (domains_a and not domains_b) or (domains_b and not domains_a):
            title_score = min(title_score, 35.0)
        # Both have NO semantic domains: require meaningful token overlap
        # Avoid false positives like "Cloud Administrator" vs "Zoning Administrator"
        # which only share the generic "administrator" word
        elif not domains_a and not domains_b and title_score > 50:
            # Check if they share meaningful (non-generic) tokens
            generic_admin_tokens = {"administrator", "manager", "director", "officer",
                                   "coordinator", "specialist", "analyst", "consultant"}
            tokens_a = {t.lower() for t in (title_can_a or "").split()}
            tokens_b = {t.lower() for t in (title_can_b or "").split()}
            meaningful_overlap = tokens_a.intersection(tokens_b) - generic_admin_tokens
            # If no meaningful overlap, penalize (unless it's a seniority variation)
            if not meaningful_overlap and not is_seniority_variation:
                title_score = min(title_score, 35.0)

    # Penalize titles that only share generic tokens (chief/officer/manager) but differ otherwise
    generic_tokens = {"chief", "officer", "manager", "director"}
    if title_score > 0 and not is_seniority_variation:  # Skip if already detected as seniority variation
        tokens_a = {t for t in (title_can_a or "").split() if t}
        tokens_b = {t for t in (title_can_b or "").split() if t}
        clean_tokens_a = {t for t in (title_clean_a or "").lower().split() if t}
        clean_tokens_b = {t for t in (title_clean_b or "").lower().split() if t}
        overlap = {t for t in tokens_a.intersection(tokens_b) if t not in generic_tokens}
        clean_overlap = {t for t in clean_tokens_a.intersection(clean_tokens_b) if t not in generic_tokens}
        strong_clean_match = _fuzzy_score(title_clean_a, title_clean_b) >= 85

        # Strategy 2 for seniority variation detection: Check if clean tokens show it
        if not is_seniority_variation:
            if not overlap and clean_overlap:
                # Clean overlap exists - possible seniority variation
                is_seniority_variation = True
            elif not overlap and not clean_overlap:
                # Check if one title is the other with only seniority/temporal words added
                tokens_only_in_a = clean_tokens_a - clean_tokens_b
                tokens_only_in_b = clean_tokens_b - clean_tokens_a
                # If one side has all generic/seniority tokens and the other side is a subset
                if (clean_tokens_a and clean_tokens_b and
                    (tokens_only_in_a.issubset(seniority_words) or tokens_only_in_b.issubset(seniority_words))):
                    is_seniority_variation = True

        if not overlap and not clean_overlap and not is_seniority_variation:
            # ONLY penalize if:
            # 1. No meaningful overlap (generic tokens excluded)
            # 2. NOT a seniority variation (e.g., "manager" vs "senior manager")
            # 3. Fuzzy score is not extremely high
            if strong_clean_match or title_score >= 90:
                # Strong match - keep the score
                title_score = max(75.0, title_score)
            else:
                # Weak match with no meaningful content overlap
                title_score = min(title_score, 35.0)

    if result_a.title and result_b.title:
        weight_pairs.append((title_score, weight_config["title"]))
        explanations.append(f"title: {title_score:.1f} (weight {weight_config['title']})")

    score = _weighted_average(weight_pairs)

    # Gender penalty if conflicting and both present and name is weighted
    gender_a = _safe_lower((result_a.name or {}).get("gender"))
    gender_b = _safe_lower((result_b.name or {}).get("gender"))
    if weight_config["name"] > 0 and gender_a and gender_b and gender_a != gender_b:
        score -= 3.0
        explanations.append("penalty: -3.0 (gender mismatch)")
    score -= score_penalty

    # Strong name agreement should not collapse entirely from other disagreements
    if weight_config["name"] > 0 and name_score >= 95.0:
        score = max(score, 45.0)
        explanations.append("floor: name agreement floor to 45.0")

    # If we have strong identifiers (email/phone) matching exactly, ensure a high floor
    if (
        weight_config["email"] > 0 and email_score == 100.0
    ) or (weight_config["phone"] > 0 and phone_score == 100.0):
        score = max(score, 90.0)
        explanations.append("floor: exact email/phone match floor to 90.0")

    final_score = max(0.0, min(100.0, score))
    if explain:
        explanations.append(f"Final Score: {final_score:.1f}")
        return final_score, explanations
    return final_score
