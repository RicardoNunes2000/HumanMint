"""
HumanMint unified facade.

Single entry point for cleaning and normalizing human-centric data:
names, emails, phone numbers, departments, and job titles.

Example:
    >>> from humanmint import mint
    >>> result = mint(
    ...     name="Dr. Alex J. Mercer, PhD",
    ...     email="ALEX.MERCER@CITY.GOV",
    ...     phone="(201) 555-0123 x 101",
    ...     department="005 - Public Works Dept",
    ...     title="Dir. of Public Works"
    ... )
    >>> print(result)
    MintResult(
      name: Alex J Mercer Phd
      email: alex.mercer@city.gov
      phone: +1 201-555-0123
      department: Public Works
      title: public works director
    )
    >>> result.email_str
    'alex.mercer@city.gov'
    >>> result.department_category
    'Infrastructure'
"""

from typing import Optional
from dataclasses import dataclass

from .processors import (
    process_name,
    process_email,
    process_phone,
    process_department,
    process_title,
)
from .types import NameResult, EmailResult, PhoneResult, DepartmentResult, TitleResult


@dataclass
class MintResult:
    """Result of unified data cleaning and normalization."""

    name: Optional[NameResult] = None
    email: Optional[EmailResult] = None
    phone: Optional[PhoneResult] = None
    department: Optional[DepartmentResult] = None
    title: Optional[TitleResult] = None

    def model_dump(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "title": self.title,
        }

    def __str__(self) -> str:
        """Return a clean, human-readable summary."""
        lines = ["MintResult("]
        if self.name:
            lines.append(f"  name: {self.name['full']}")
        else:
            lines.append("  name: None")

        if self.email:
            lines.append(f"  email: {self.email['normalized']}")
        else:
            lines.append("  email: None")

        if self.phone:
            phone_str = self.phone["pretty"] or self.phone["e164"] or "(invalid)"
            lines.append(f"  phone: {phone_str}")
        else:
            lines.append("  phone: None")

        if self.department:
            lines.append(f"  department: {self.department['canonical']}")
        else:
            lines.append("  department: None")

        if self.title:
            lines.append(f"  title: {self.title['canonical']}")
        else:
            lines.append("  title: None")

        lines.append(")")
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return the same as __str__ for interactive use."""
        return self.__str__()

    # Convenience properties for simple access
    @property
    def name_str(self) -> Optional[str]:
        """Get full name as string, or None."""
        return self.name["full"] if self.name else None

    @property
    def name_first(self) -> Optional[str]:
        """Get first name, or None."""
        return self.name["first"] if self.name else None

    @property
    def name_last(self) -> Optional[str]:
        """Get last name, or None."""
        return self.name["last"] if self.name else None

    @property
    def name_middle(self) -> Optional[str]:
        """Get middle name, or None."""
        return self.name["middle"] if self.name else None

    @property
    def name_suffix(self) -> Optional[str]:
        """Get suffix, or None."""
        return self.name["suffix"] if self.name else None

    @property
    def name_gender(self) -> Optional[str]:
        """Get gender, or None."""
        return self.name["gender"] if self.name else None

    @property
    def email_str(self) -> Optional[str]:
        """Get normalized email, or None."""
        return self.email["normalized"] if self.email else None

    @property
    def email_domain(self) -> Optional[str]:
        """Get email domain, or None."""
        return self.email["domain"] if self.email else None

    @property
    def email_valid(self) -> Optional[bool]:
        """Check if email is valid, or None."""
        return self.email["is_valid"] if self.email else None

    @property
    def email_generic(self) -> Optional[bool]:
        """Check if email is generic inbox, or None."""
        return self.email["is_generic"] if self.email else None

    @property
    def email_free(self) -> Optional[bool]:
        """Check if email is from free provider, or None."""
        return self.email["is_free_provider"] if self.email else None

    @property
    def phone_str(self) -> Optional[str]:
        """Get formatted phone (pretty or e164), or None."""
        if self.phone:
            return self.phone["pretty"] or self.phone["e164"]
        return None

    @property
    def phone_e164(self) -> Optional[str]:
        """Get E.164 phone format, or None."""
        return self.phone["e164"] if self.phone else None

    @property
    def phone_pretty(self) -> Optional[str]:
        """Get pretty-formatted phone, or None."""
        return self.phone["pretty"] if self.phone else None

    @property
    def phone_extension(self) -> Optional[str]:
        """Get phone extension, or None."""
        return self.phone["extension"] if self.phone else None

    @property
    def phone_valid(self) -> Optional[bool]:
        """Check if phone is valid, or None."""
        return self.phone["is_valid"] if self.phone else None

    @property
    def phone_type(self) -> Optional[str]:
        """Get phone type (MOBILE, FIXED_LINE, etc), or None."""
        return self.phone["type"] if self.phone else None

    @property
    def department_str(self) -> Optional[str]:
        """Get canonical department name, or None."""
        return self.department["canonical"] if self.department else None

    @property
    def department_category(self) -> Optional[str]:
        """Get department category, or None."""
        return self.department["category"] if self.department else None

    @property
    def department_normalized(self) -> Optional[str]:
        """Get normalized (before canonical match) department, or None."""
        return self.department["normalized"] if self.department else None

    @property
    def department_override(self) -> Optional[bool]:
        """Check if department came from override, or None."""
        return self.department["is_override"] if self.department else None

    @property
    def title_str(self) -> Optional[str]:
        """Get canonical title, or None."""
        return self.title["canonical"] if self.title else None

    @property
    def title_cleaned(self) -> Optional[str]:
        """Get cleaned (intermediate) title, or None."""
        return self.title["cleaned"] if self.title else None

    @property
    def title_valid(self) -> Optional[bool]:
        """Check if title is valid, or None."""
        return self.title["is_valid"] if self.title else None




def mint(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    department: Optional[str] = None,
    title: Optional[str] = None,
    dept_overrides: Optional[dict[str, str]] = None,
    aggressive_clean: bool = False,
) -> MintResult:
    """
    Clean and normalize human-centric data in one call.

    Processes name, email, phone, department, and title fields through their
    respective normalization and enrichment pipelines. Returns a structured
    result with cleaned and validated data.

    Args:
        name: Full name or first/last name.
        email: Email address.
        phone: Phone number in any format.
        department: Department name (with or without noise).
        title: Job title (with or without noise, name prefixes, codes).
        dept_overrides: Custom department mappings (e.g., {"Revenue Operations": "Sales"}).
            Overrides are applied after normalization, before canonical matching.
            If a normalized department matches a key in overrides, the override value is used.
            Otherwise, normal canonical matching applies.
        aggressive_clean: If True, strips SQL artifacts and corruption markers from names.
            Only use if data comes from genuinely untrusted sources (e.g., raw database
            exports, CRM dumps with injection artifacts). Default False to preserve
            legitimate names. WARNING: May remove legitimate content in edge cases.

    Returns:
        MintResult: Structured result with cleaned fields.

    Example:
        >>> result = mint(
        ...     name="Dr. Alex J. Mercer, PhD",
        ...     email="ALEX.MERCER@CITY.GOV",
        ...     phone="(201) 555-0123 x 101",
        ...     department="005 - Public Works Dept",
        ...     title="Dir. of Public Works"
        ... )
        >>> result.name
        {
            'raw': 'Dr. Alex J. Mercer, PhD',
            'first': 'Alex',
            'middle': 'J',
            'last': 'Mercer',
            'suffix': 'phd',
            'full': 'Alex J Mercer Phd',
            'gender': 'Male'
        }
        >>> result.email
        {
            'raw': 'ALEX.MERCER@CITY.GOV',
            'normalized': 'alex.mercer@city.gov',
            'is_valid': True,
            'is_generic': False,
            'is_free_provider': False,
            'domain': 'city.gov'
        }
        >>> result.phone
        {
            'raw': '(201) 555-0123 x 101',
            'e164': '+12015550123',
            'pretty': '+1 201-555-0123',
            'extension': '101',
            'is_valid': True,
            'type': 'FIXED_LINE'
        }
        >>> result.department
        {
            'raw': '005 - Public Works Dept',
            'normalized': 'Public Works',
            'canonical': 'Public Works',
            'category': 'Infrastructure',
            'is_override': False
        }

        With custom department override:
        >>> result = mint(
        ...     department="HR Dept",
        ...     dept_overrides={"Human Resources": "People Operations"}
        ... )
        >>> result.department
        {
            'raw': 'HR Dept',
            'normalized': 'Human Resources',
            'canonical': 'People Operations',
            'category': 'administration',
            'is_override': True
        }
    """
    return MintResult(
        name=process_name(name, aggressive_clean=aggressive_clean),
        email=process_email(email),
        phone=process_phone(phone),
        department=process_department(department, dept_overrides),
        title=process_title(title),
    )
