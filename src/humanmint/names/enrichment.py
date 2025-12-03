"""
Name enrichment for HumanMint.

Optional v0.5 features: gender inference based on merged names database.
Combines:
- 2159 canonical names from nicknames library
- Gender data from US baby names (SSA data 1920-2023)
"""

import gzip
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import orjson

# Cache for names dataset (lazy-loaded)
_gender_cache: Optional[Dict[str, str]] = None
DATA_DIR = Path(__file__).parent.parent / "data"
NAMES_CACHE = DATA_DIR / "names.json.gz"
_gender_warning_emitted = False


def _load_gender_data_from_cache() -> Optional[Dict[str, str]]:
    """Load gender data from a prebuilt cache, if present."""
    if not NAMES_CACHE.exists():
        return None
    try:
        data = gzip.decompress(NAMES_CACHE.read_bytes())
        payload = orjson.loads(data)
        if isinstance(payload, dict):
            return {
                k: v
                for k, v in payload.items()
                if isinstance(k, str) and isinstance(v, str)
            }
    except Exception:
        return None
    return None


def _load_gender_data() -> Dict[str, str]:
    """
    Load gender data from names database.

    Contains 2159+ canonical names with gender inference from:
    - nicknames library (canonical name variants)
    - US baby names (SSA data 1920-2023)

    Returns:
        Dict mapping name (lowercase) to gender ("M" or "F").
    """
    global _gender_cache

    if _gender_cache is not None:
        return _gender_cache

    from_cache = _load_gender_data_from_cache()
    if from_cache is not None:
        _gender_cache = from_cache
        return _gender_cache

    raise FileNotFoundError(
        f"Names cache not found: {NAMES_CACHE}. Run scripts/build_caches.py."
    )


def infer_gender(
    first_name: str,
    confidence: bool = False
) -> Dict[str, Optional[str]]:
    """
    Infer gender from a first name using US baby names dataset.

    Uses historical US Social Security Administration data to infer gender
    based on name frequency by sex. Results are based on statistical patterns
    from 1920-2023 US baby names.

    Note:
        This is probabilistic and not a determination of identity. Use with
        care in downstream workflows.

    Args:
        first_name: Person's first name.
        confidence: If True, return confidence level; if False, just gender.

    Returns:
        Dict with:
        - gender: "Male", "Female", or "Unknown"
        - confidence: Confidence level (only if confidence=True)

    Examples:
        >>> infer_gender("John")
        {"gender": "Male", "confidence": None}

        >>> infer_gender("Mary")
        {"gender": "Female", "confidence": None}

        >>> infer_gender("John", confidence=True)
        {"gender": "Male", "confidence": 0.95}
    """
    if not first_name:
        return {"gender": "Unknown", "confidence": None}

    # Load gender data; fall back gracefully if cache is missing
    try:
        gender_data = _load_gender_data()
    except FileNotFoundError:
        global _gender_warning_emitted
        if not _gender_warning_emitted:
            warnings.warn(
                f"Names cache missing; gender inference disabled. "
                f"Expected at {NAMES_CACHE}. Run scripts/build_caches.py to generate.",
                RuntimeWarning,
            )
            _gender_warning_emitted = True
        gender_data = {}

    # Clean first name
    first_name_lower = first_name.strip().lower()

    if not first_name_lower:
        return {"gender": "Unknown", "confidence": None}

    # Look up gender
    sex = gender_data.get(first_name_lower)

    if not sex:
        gender_label = "Unknown"
        conf = 0.0
    elif sex == "M":
        gender_label = "Male"
        conf = 0.95 if confidence else None
    elif sex == "F":
        gender_label = "Female"
        conf = 0.95 if confidence else None
    else:
        gender_label = "Unknown"
        conf = 0.0

    return {
        "gender": gender_label,
        "confidence": conf,
    }


def enrich_name(
    normalized_name: Dict[str, Optional[str]],
    include_gender: bool = True,
) -> Dict[str, Any]:
    """
    Enrich a normalized name with optional metadata.

    Adds:
    - Gender inference based on US baby names dataset (if include_gender=True)

    Args:
        normalized_name: Result dict from normalize_name().
        include_gender: Whether to include gender inference (default True).

    Returns:
        Enhanced dict with original fields plus enrichment.

    Examples:
        >>> result = normalize_name("John Smith")
        >>> enriched = enrich_name(result)
        >>> enriched["gender"]
        "Male"
    """
    if not normalized_name or not normalized_name.get("is_valid"):
        return normalized_name

    enriched = normalized_name.copy()

    # Add gender inference
    if include_gender:
        gender_result = infer_gender(
            normalized_name.get("first", ""),
            confidence=True
        )
        enriched["gender"] = gender_result["gender"]
        enriched["gender_confidence"] = gender_result["confidence"]
    else:
        enriched["gender"] = None
        enriched["gender_confidence"] = None

    return enriched
