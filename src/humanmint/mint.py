"""
HumanMint unified facade.

Single entry point for cleaning and normalizing human-centric data:
names, emails, phone numbers, departments, and job titles.

Example:
    >>> from humanmint import mint
    Examples:
        Structured input (deterministic):
            >>> result = mint(
            ...     name="Dr. Alex J. Mercer, PhD",
            ...     email="ALEX.MERCER@CITY.GOV",
            ...     phone="(201) 555-0123 x 101",
            ...     department="005 - Public Works Dept",
            ...     title="Dir. of Public Works"
            ... )
            >>> result.name_standardized
            'Alex J Mercer Phd'
            >>> result.title_canonical
            'public works director'

        Unstructured text + GLiNER (optional, requires gliner2 installed):
            >>> text = \"\"\"John A. Miller
            ... Deputy Director of Public Works
            ... City of Springfield, Missouri
            ... Phone: (417) 864-1234
            ... Email: jmiller@springfieldmo.gov\"\"\"
            >>> result = mint(text=text, use_gliner=True)
            >>> result.name_standardized
            'John A Miller'
            >>> result.title_canonical
            'deputy director'
"""

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Union

from . import gliner
from .processors import (
    process_address,
    process_department,
    process_email,
    process_name,
    process_organization,
    process_phone,
    process_title,
)
from .types import (
    AddressResult,
    DepartmentResult,
    EmailResult,
    NameResult,
    OrganizationResult,
    PhoneResult,
    TitleResult,
)

# Input length limits to prevent DoS and data validation
MAX_NAME_LENGTH = 1000
MAX_EMAIL_LENGTH = 254  # RFC 5321 standard
MAX_PHONE_LENGTH = 30
MAX_DEPT_LENGTH = 500
MAX_TITLE_LENGTH = 500
MAX_ADDRESS_LENGTH = 1000
MAX_ORG_LENGTH = 500


@dataclass
class MintResult:
    """Result of unified data cleaning and normalization."""

    name: Optional[NameResult] = None
    email: Optional[EmailResult] = None
    phone: Optional[PhoneResult] = None
    department: Optional[DepartmentResult] = None
    title: Optional[TitleResult] = None
    address: Optional[AddressResult] = None
    organization: Optional[OrganizationResult] = None

    def model_dump(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "title": self.title,
            "address": self.address,
            "organization": self.organization,
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
            lines.append(f"  department: {self.department.get('canonical')}")
        else:
            lines.append("  department: None")

        if self.title:
            lines.append("  title:")
            lines.append(f"    raw: {self.title.get('raw')}")
            lines.append(f"    normalized: {self.title.get('normalized')}")
            lines.append(f"    canonical: {self.title.get('canonical')}")
        else:
            lines.append("  title: None")

        if self.address:
            lines.append(
                f"  address: {self.address.get('canonical') or self.address.get('street')}"
            )
        else:
            lines.append("  address: None")

        if self.organization:
            lines.append(f"  organization: {self.organization.get('canonical')}")
        else:
            lines.append("  organization: None")

        lines.append(")")
        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return the same as __str__ for interactive use."""
        return self.__str__()

    # Convenience properties for simple access
    @property
    def name_standardized(self) -> Optional[str]:
        """Get standardized full name, or None."""
        return self.name["full"] if self.name else None

    @property
    def name_nickname(self) -> Optional[str]:
        """Get detected nickname, or None."""
        return self.name.get("nickname") if self.name else None

    @property
    def name_suffix_type(self) -> Optional[str]:
        """Get suffix classification (e.g., generational), or None."""
        return self.name.get("suffix_type") if self.name else None

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
    def email_standardized(self) -> Optional[str]:
        """Get normalized email, or None."""
        return self.email["normalized"] if self.email else None

    @property
    def email_domain(self) -> Optional[str]:
        """Get email domain, or None."""
        return self.email["domain"] if self.email else None

    @property
    def email_is_valid(self) -> Optional[bool]:
        """Check if email is valid, or None."""
        return self.email.get("is_valid") if self.email else None

    @property
    def email_is_generic_inbox(self) -> Optional[bool]:
        """Check if email is generic inbox, or None."""
        return self.email.get("is_generic_inbox") if self.email else None

    @property
    def email_is_free_provider(self) -> Optional[bool]:
        """Check if email is from free provider, or None."""
        return self.email.get("is_free_provider") if self.email else None

    @property
    def phone_standardized(self) -> Optional[str]:
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
    def phone_is_valid(self) -> Optional[bool]:
        """Check if phone is valid number, or None."""
        return self.phone.get("is_valid") if self.phone else None

    @property
    def phone_type(self) -> Optional[str]:
        """Get phone type (MOBILE, FIXED_LINE, etc), or None."""
        return self.phone.get("type") if self.phone else None

    @property
    def department_canonical(self) -> Optional[str]:
        """Get canonical department name, or None."""
        return self.department.get("canonical") if self.department else None

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
        return self.department.get("is_override") if self.department else None

    @property
    def title_canonical(self) -> Optional[str]:
        """Get canonical title."""
        return self.title.get("canonical") if self.title else None

    @property
    def title_raw(self) -> Optional[str]:
        """Get raw title, or None."""
        return self.title["raw"] if self.title else None

    @property
    def title_normalized(self) -> Optional[str]:
        """Get normalized (intermediate) title, or None."""
        return self.title["normalized"] if self.title else None

    @property
    def title_is_valid(self) -> Optional[bool]:
        """Check if title is valid match, or None."""
        return self.title.get("is_valid") if self.title else None

    @property
    def title_confidence(self) -> float:
        """Get title confidence score, or 0.0."""
        return self.title["confidence"] if self.title else 0.0

    @property
    def title_seniority(self) -> Optional[str]:
        """Get seniority level (Senior, Lead, Principal, etc.), or None."""
        return self.title.get("seniority") if self.title else None

    @property
    def address_raw(self) -> Optional[str]:
        """Get raw address, or None."""
        return self.address.get("raw") if self.address else None

    @property
    def address_street(self) -> Optional[str]:
        """Get street address, or None."""
        return self.address.get("street") if self.address else None

    @property
    def address_unit(self) -> Optional[str]:
        """Get unit/apt number, or None."""
        return self.address.get("unit") if self.address else None

    @property
    def address_city(self) -> Optional[str]:
        """Get city, or None."""
        return self.address.get("city") if self.address else None

    @property
    def address_state(self) -> Optional[str]:
        """Get state, or None."""
        return self.address.get("state") if self.address else None

    @property
    def address_zip(self) -> Optional[str]:
        """Get ZIP code, or None."""
        return self.address.get("zip") if self.address else None

    @property
    def address_country(self) -> Optional[str]:
        """Get country, or None."""
        return self.address.get("country") if self.address else None

    @property
    def address_canonical(self) -> Optional[str]:
        """Get canonical address string, or None."""
        return self.address.get("canonical") if self.address else None

    @property
    def organization_raw(self) -> Optional[str]:
        """Get raw organization name, or None."""
        return self.organization.get("raw") if self.organization else None

    @property
    def organization_normalized(self) -> Optional[str]:
        """Get normalized organization name, or None."""
        return self.organization.get("normalized") if self.organization else None

    @property
    def organization_canonical(self) -> Optional[str]:
        """Get canonical organization name, or None."""
        return self.organization.get("canonical") if self.organization else None

    @property
    def organization_confidence(self) -> float:
        """Get organization confidence score, or 0.0."""
        return self.organization.get("confidence", 0.0) if self.organization else 0.0

    def get(self, field: str, default=None) -> any:
        """
        Safely access nested fields within result objects.

        Supports dot notation for nested access (e.g., "name.first", "email.normalized").

        Args:
            field: Field path using dot notation. Examples:
                - "name" → returns the full name dict
                - "name.first" → returns the first name string
                - "email.domain" → returns the email domain
                - "phone.e164" → returns the E.164 phone format
                - "department.canonical" → returns the canonical department name

            default: Value to return if field doesn't exist or is None.

        Returns:
            The requested field value, or default if not found.

        Examples:
            >>> result = mint(name="John Smith", email="john@example.com")
            >>> result.get("name.first")
            'John'
            >>> result.get("email.domain")
            'example.com'
            >>> result.get("phone.e164")  # Returns None (no phone provided)
            >>> result.get("phone.e164", "+1 000-000-0000")  # Returns default
            '+1 000-000-0000'
        """
        # Split on dot for nested access
        parts = field.split(".", 1)
        root = parts[0]

        # Map root field name to the actual attribute
        field_map = {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "title": self.title,
            "address": self.address,
            "organization": self.organization,
        }

        # Get the root object
        obj = field_map.get(root)
        if obj is None:
            return default

        # If no nested access, return the object itself
        if len(parts) == 1:
            return obj

        # Navigate to nested field
        nested_field = parts[1]
        if isinstance(obj, dict):
            return obj.get(nested_field, default)

        return default


def mint(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    department: Optional[str] = None,
    title: Optional[str] = None,
    organization: Optional[str] = None,
    title_overrides: Optional[dict[str, str]] = None,
    dept_overrides: Optional[dict[str, str]] = None,
    aggressive_clean: bool = False,
    split_multi: bool = False,
    text: Optional[str] = None,
    texts: Optional[list[str]] = None,
    use_gliner: bool = False,
    gliner_cfg: Optional["gliner.GlinerConfig"] = None,
) -> Union[MintResult, list[MintResult]]:
    """
    Clean and normalize human-centric data in one call.

    Processes name, email, phone, department, and title fields through their
    respective normalization and enrichment pipelines. Returns a structured
    result with cleaned and validated data.

    Args:
        name: Full name or first/last name.
        email: Email address.
        phone: Phone number in any format.
        address: Postal address string (US-focused parsing).
        department: Department name (with or without noise).
        title: Job title (with or without noise, name prefixes, codes).
        organization: Organization/agency name.
        title_overrides: Custom title mappings applied before canonical matching.
        dept_overrides: Custom department mappings (e.g., {"Revenue Operations": "Sales"}).
            Overrides are applied after normalization, before canonical matching.
            If a normalized department matches a key in overrides, the override value is used.
            Otherwise, normal canonical matching applies.
        aggressive_clean: If True, strips SQL artifacts and corruption markers from names.
            Only use if data comes from genuinely untrusted sources (e.g., raw database
            exports, CRM dumps with injection artifacts). Default False to preserve
            legitimate names. WARNING: May remove legitimate content in edge cases.
        split_multi: If True, splits multi-person name strings (e.g., "John and Jane Smith")
            into separate MintResult objects.
        text: Unstructured text to extract from using GLiNER2 (optional; requires gliner2).
        texts: List of unstructured texts to extract from using GLiNER2 (optional; requires gliner2, returns list).
        use_gliner: If True, run GLiNER2 extraction on provided text(s) and fill only missing fields.
            Structured fields you pass are never overridden. Raises if multiple people are detected.
        gliner_cfg: Optional GLiNER configuration object (schema/threshold/extractor/use_gpu). If omitted,
            defaults are used and the model runs on CPU when loaded.

    Raises:
        ValueError: If any input field exceeds maximum length limits, or if use_gliner=True
            is set without text(s), or if multiple people are detected in GLiNER output.
        ImportError: If use_gliner=True but gliner2 is not installed.

        Returns:
            MintResult or list[MintResult]: Structured result(s) with cleaned fields. Returns a list
                when split_multi is triggered or when texts (list) are provided, or when GLiNER
                processes multiple texts.

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
    # Validate GLiNER usage
    if use_gliner and not (text or texts):
        raise ValueError("use_gliner=True requires text=... or texts=[...] input")

    # Validate input field lengths to prevent DoS attacks
    # Note: Check isinstance(x, str) to handle NaN from pandas DataFrames
    if isinstance(name, str) and len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Name exceeds maximum length of {MAX_NAME_LENGTH} characters")
    if isinstance(email, str) and len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(
            f"Email exceeds maximum length of {MAX_EMAIL_LENGTH} characters"
        )
    if isinstance(phone, str) and len(phone) > MAX_PHONE_LENGTH:
        raise ValueError(
            f"Phone exceeds maximum length of {MAX_PHONE_LENGTH} characters"
        )
    if isinstance(department, str) and len(department) > MAX_DEPT_LENGTH:
        raise ValueError(
            f"Department exceeds maximum length of {MAX_DEPT_LENGTH} characters"
        )
    if isinstance(title, str) and len(title) > MAX_TITLE_LENGTH:
        raise ValueError(
            f"Title exceeds maximum length of {MAX_TITLE_LENGTH} characters"
        )
    if isinstance(address, str) and len(address) > MAX_ADDRESS_LENGTH:
        raise ValueError(
            f"Address exceeds maximum length of {MAX_ADDRESS_LENGTH} characters"
        )
    if isinstance(organization, str) and len(organization) > MAX_ORG_LENGTH:
        raise ValueError(
            f"Organization exceeds maximum length of {MAX_ORG_LENGTH} characters"
        )

    # Detect multi-person names and split if requested
    def _split_multi_person_names(raw: str) -> Optional[list[str]]:
        # If it's a single "Last, First ..." format (one comma, no connectors), don't split
        if (
            raw.count(",") == 1
            and not re.search(r"\b(?:and|&|/|\+|;)\b", raw, flags=re.IGNORECASE)
            and re.match(r"^\s*[^,]+,\s*[^,]+", raw)
        ):
            return None

        # Normalize common connectors (commas, ampersand, slash, plus) to "and"
        cleaned = re.sub(r"[,&/+;]", " and ", raw)
        connectors = re.compile(r"\s+(?:and|&|/|\+|;)\s+", re.IGNORECASE)
        parts = [p.strip(" ,") for p in connectors.split(cleaned) if p.strip(" ,")]
        if len(parts) < 2:
            return None

        # If the last part has a last name, share it with earlier single-token parts
        last_tokens = parts[-1].split()
        shared_last = last_tokens[-1] if len(last_tokens) >= 2 else None
        rebuilt: list[str] = []
        for idx, part in enumerate(parts):
            tokens = part.split()
            if len(tokens) == 1 and shared_last and idx < len(parts) - 1:
                rebuilt.append(f"{tokens[0]} {shared_last}")
            else:
                rebuilt.append(part)
        return rebuilt

    if split_multi and isinstance(name, str):
        split_names = _split_multi_person_names(name)
        if split_names:
            # Process each name separately; reuse other fields; avoid recursive splitting
            results_split: list[MintResult] = []
            for nm in split_names:
                results_split.append(
                    mint(
                        name=nm,
                        email=email,
                        phone=phone,
                        address=address,
                        department=department,
                        title=title,
                        organization=organization,
                        title_overrides=title_overrides,
                        dept_overrides=dept_overrides,
                        aggressive_clean=aggressive_clean,
                        split_multi=False,
                    )
                )  # type: ignore[arg-type]
            return results_split

    # If GLiNER is requested, extract missing fields from unstructured text
    if use_gliner and (text or texts):
        texts_to_use = texts if texts else [text]  # type: ignore[list-item]
        results_gliner: list[MintResult] = []
        for t in texts_to_use:
            extracted_fields = gliner.extract_fields_from_text(
                t or "",
                config=gliner_cfg,
            )
            # User-supplied fields take precedence; fill only missing ones
            nm = name or extracted_fields.get("name")
            em = email or extracted_fields.get("email")
            ph = phone or extracted_fields.get("phone")
            addr_parts = [
                extracted_fields.get("street"),
                extracted_fields.get("city"),
                extracted_fields.get("state"),
                extracted_fields.get("zip"),
            ]
            addr_combined = " ".join([p for p in addr_parts if p])
            addr = (
                address
                or extracted_fields.get("address")
                or extracted_fields.get("location")
                or (addr_combined if addr_combined else None)
            )
            dept_val = department or extracted_fields.get("department")
            ttl = title or extracted_fields.get("title")
            org = organization or extracted_fields.get("organization")

            department_result = process_department(dept_val, dept_overrides)
            dept_canonical = (
                department_result["canonical"] if department_result else None
            )

            results_gliner.append(
                MintResult(
                    name=process_name(nm, aggressive_clean=aggressive_clean),
                    email=process_email(em),
                    phone=process_phone(ph),
                    department=department_result,
                    title=process_title(
                        ttl, dept_canonical=dept_canonical, overrides=title_overrides
                    ),
                    address=process_address(addr),
                    organization=process_organization(org),
                )
            )
        if len(results_gliner) == 1:
            return results_gliner[0]
        return results_gliner

    department_result = process_department(department, dept_overrides)
    dept_canonical = department_result["canonical"] if department_result else None

    return MintResult(
        name=process_name(name, aggressive_clean=aggressive_clean),
        email=process_email(email),
        phone=process_phone(phone),
        department=department_result,
        title=process_title(
            title, dept_canonical=dept_canonical, overrides=title_overrides
        ),
        address=process_address(address),
        organization=process_organization(organization),
    )


def bulk(
    records: Iterable[dict],
    workers: int = 4,
    progress: Optional[Union[bool, str, Callable[[], None]]] = False,
    deduplicate: bool = True,
) -> list[MintResult]:
    """
    Process multiple records (dicts accepted by mint) in parallel using threads.

    Args:
        records: Iterable of dicts accepted by mint().
        workers: Max worker threads.
        progress: If truthy, display progress. Uses Rich when available, otherwise
                  a simple stdout ticker. You can also pass a callable to be
                  invoked on each completed record.
        deduplicate: If True, deduplicates inputs before processing and expands
                    results back. Reduces redundant fuzzy matching by ~50% on
                    typical government datasets with duplicates. Default True.

    Returns:
        list[MintResult]: Processed results in same order as input records.
    """

    def _noop() -> None:
        return None

    # If progress or deduplication requested, realize iterable
    materialized = None
    if progress or deduplicate:
        materialized = list(records)
        records = materialized

    total = len(materialized) if materialized is not None else None

    progress_tick: Optional[Callable[[], None]] = None
    progress_start: Callable[[], None] = _noop
    progress_stop: Callable[[], None] = _noop

    if progress:
        if callable(progress):
            progress_tick = progress
        else:
            # Prefer Rich, then tqdm, then a simple ticker.
            try:
                from rich.progress import (  # type: ignore
                    BarColumn,
                    MofNCompleteColumn,
                    Progress,
                    SpinnerColumn,
                    TextColumn,
                    TimeElapsedColumn,
                    TimeRemainingColumn,
                )

                rp = Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                )
                task_id = rp.add_task("Bulk minting", total=total)

                def _progress_start() -> None:
                    rp.start()

                def _progress_stop() -> None:
                    rp.stop()

                def _progress_tick() -> None:
                    rp.advance(task_id, 1)

                progress_start = _progress_start
                progress_stop = _progress_stop
                progress_tick = _progress_tick
            except Exception:
                try:
                    from tqdm import tqdm  # type: ignore

                    bar = tqdm(total=total, desc="Bulk minting", unit="rec")

                    def _progress_tick() -> None:
                        bar.update(1)

                    def _progress_stop() -> None:
                        bar.close()

                    progress_tick = _progress_tick
                    progress_start = _noop
                    progress_stop = _progress_stop
                except Exception:
                    processed = [0]
                    step = max(1, (total or 1) // 20)

                    def _progress_tick() -> None:
                        processed[0] += 1
                        if processed[0] % step == 0 or processed[0] == total:
                            print(f"Processed {processed[0]}/{total or '?'}")

                    def _progress_start() -> None:
                        print("Starting bulk mint...")

                    def _progress_stop() -> None:
                        print("Bulk mint complete.")

                    progress_start = _progress_start
                    progress_stop = _progress_stop
                    progress_tick = _progress_tick

    def _run_mint(rec: dict) -> MintResult:
        return mint(**rec)

    from concurrent.futures import ThreadPoolExecutor

    # Handle deduplication if enabled
    if deduplicate and materialized:
        # Create deduplication keys from record values
        unique_records: dict[str, dict] = {}
        record_map: list[str] = []  # Maps original index → dedup key

        for rec in materialized:
            # Create canonical key from all field values (lowercased, stripped)
            key_parts = []
            for field in [
                "name",
                "email",
                "phone",
                "department",
                "title",
                "address",
                "organization",
            ]:
                val = rec.get(field)
                if val:
                    key_parts.append(str(val).lower().strip())

            key = "|".join(key_parts)
            record_map.append(key)

            if key not in unique_records:
                unique_records[key] = rec

        # Log deduplication if significant reduction
        unique_count = len(unique_records)
        if unique_count < len(materialized):
            reduction_pct = 100 * (1 - unique_count / len(materialized))
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"Deduplicating {len(materialized)} → {unique_count} records ({reduction_pct:.1f}% reduction)"
            )

        # Process only unique records
        unique_list = list(unique_records.values())
        results_unique: list[MintResult] = []
        progress_start()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            for res in executor.map(_run_mint, unique_list):
                results_unique.append(res)
                if progress_tick:
                    progress_tick()
        progress_stop()

        # Expand results back to original order by mapping keys
        result_cache = dict(zip(unique_records.keys(), results_unique))
        results = [result_cache[key] for key in record_map]
        return results

    # Standard processing without deduplication
    results: list[MintResult] = []
    progress_start()
    records_to_process = records if materialized is None else materialized
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(_run_mint, records_to_process):
            results.append(res)
            if progress_tick:
                progress_tick()
    progress_stop()
    return results
