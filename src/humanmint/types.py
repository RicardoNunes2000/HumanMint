"""
Type definitions for HumanMint result objects.

Separated from mint.py to avoid circular imports and improve modularity.
"""

from typing import Optional, TypedDict


class NameResult(TypedDict, total=False):
    """Parsed and enriched name components."""
    raw: str
    first: str
    middle: Optional[str]
    last: str
    suffix: Optional[str]
    full: str
    gender: str
    canonical: str


class EmailResult(TypedDict, total=False):
    """Validated and normalized email with metadata."""
    raw: str
    normalized: str
    is_valid: bool
    is_valid_format: bool
    is_generic: bool
    is_generic_inbox: bool
    is_free_provider: bool
    domain: Optional[str]
    local: Optional[str]
    local_base: Optional[str]


class PhoneResult(TypedDict, total=False):
    """Normalized phone number in multiple formats."""
    raw: str
    e164: Optional[str]
    pretty: Optional[str]
    extension: Optional[str]
    is_valid: bool
    is_valid_number: bool
    detected_type: Optional[str]
    type: Optional[str]
    country: Optional[str]


class DepartmentResult(TypedDict, total=False):
    """Normalized department with canonicalization."""
    raw: str
    normalized: str
    mapped_to: Optional[str]
    canonical: Optional[str]
    category: Optional[str]
    was_overridden: bool
    is_override: bool
    confidence: float


class TitleResult(TypedDict, total=False):
    """Normalized and canonicalized job title."""
    raw: Optional[str]
    normalized: Optional[str]
    cleaned: Optional[str]
    mapped_to: Optional[str]
    canonical: Optional[str]
    is_valid_match: Optional[bool]
    is_valid: Optional[bool]
    confidence: float
    seniority: Optional[str]


class AddressResult(TypedDict, total=False):
    """Normalized postal address."""
    raw: str
    street: Optional[str]
    unit: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    canonical: Optional[str]
    confidence: float


class OrganizationResult(TypedDict, total=False):
    """Normalized organization/agency name."""
    raw: str
    normalized: str
    canonical: str
    confidence: float
