"""
Optional GLiNER2 integration for unstructured text extraction.

Install with: pip install "humanmint[ml]"
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

_IMPORT_ERROR: Optional[Exception] = None
_HAS_GLINER = False

try:  # pragma: no cover - optional dependency
    from gliner2 import GLiNER2  # type: ignore
    try:
        from transformers import \
            logging as _tlogging  # type: ignore  # pragma: no cover

        _tlogging.set_verbosity_error()
    except Exception:
        pass
    _HAS_GLINER = True
except Exception as e:  # pragma: no cover
    _IMPORT_ERROR = e
    GLiNER2 = None  # type: ignore

# Schema tuned for civic/government contacts (simple, reliable)
_JSON_SCHEMA = {
    "contact": [
        "name::str::Full person name",
        "title::str::Job title or role",
        "department::str::Department or division",
        "organization::str::Agency, government body, or office",
        "email::str::Email address",
        "phone::str::Phone number",
        "address::str::Postal or physical address",
        "location::str::City, state, or place name",
    ]
}


def _preprocess_text(text: str) -> str:
    """Light cleanup to help extraction: collapse newlines and excess whitespace."""
    cleaned = re.sub(r"\s*\n\s*", " ", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


@dataclass
class GlinerConfig:
    """Optional configuration for GLiNER extraction."""

    extractor: Optional[Any] = None
    schema: Optional[dict] = None
    threshold: Optional[float] = None
    use_gpu: bool = False


def extract_fields_from_text(
    text: str,
    config: Optional[GlinerConfig] = None,
) -> Dict[str, Optional[str]]:
    """
    Extract name/email/phone/address/department/title/organization from free text using GLiNER2.
    Raises ImportError if gliner2 is not installed.
    """
    cfg = config or GlinerConfig()
    extractor = cfg.extractor
    schema = cfg.schema
    threshold = cfg.threshold
    use_gpu = cfg.use_gpu

    if extractor is None:
        if not _HAS_GLINER:
            raise ImportError(
                "use_gliner=True requires the optional dependency gliner2. "
                'Install with pip install "humanmint[ml]".'
            ) from _IMPORT_ERROR
        extractor = GLiNER2.from_pretrained("fastino/gliner2-base-v1")  # pragma: no cover
        if use_gpu:
            try:
                import torch  # type: ignore

                device = "cuda" if torch.cuda.is_available() else "cpu"
                extractor.to(device)
            except Exception:
                pass

    text_cleaned = _preprocess_text(text or "")

    payload = None
    effective_schema = schema or _JSON_SCHEMA
    try:
        payload = extractor.extract_json(text_cleaned, effective_schema, threshold=threshold)
    except Exception:
        payload = None

    contact_list = []
    if isinstance(payload, dict):
        contact = payload.get("contact") or payload
        if isinstance(contact, list):
            contact_list = contact
        else:
            contact_list = [contact]
    elif isinstance(payload, list):
        contact_list = payload

    if len(contact_list) > 1:
        raise ValueError(
            "Multiple person entities detected. "
            "mint(text, use_gliner=True) only supports one person per call. "
            "Use split_multi or provide separate text blocks per contact."
        )

    contact = contact_list[0] if contact_list else {}

    # Also guard against a single contact containing multiple names in the name field
    if isinstance(contact, dict):
        names = contact.get("name")
        if isinstance(names, list) and len(names) > 1:
            raise ValueError(
                "Multiple person entities detected. "
                "mint(text, use_gliner=True) only supports one person per call. "
                "Use split_multi or provide separate text blocks per contact."
            )

    def _get(key: str) -> Optional[str]:
        if isinstance(contact, dict) and key in contact and contact[key]:
            return str(contact[key])
        return None

    return {
        "name": _get("name"),
        "title": _get("title"),
        "department": _get("department"),
        "organization": _get("organization"),
        "email": _get("email"),
        "phone": _get("phone"),
        "address": _get("address"),
        "street": _get("street"),
        "city": _get("city"),
        "state": _get("state"),
        "zip": _get("zip"),
        "location": _get("location"),
    }
