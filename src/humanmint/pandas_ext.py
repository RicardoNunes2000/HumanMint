"""
Pandas DataFrame accessor for HumanMint.

Usage:
    import humanmint  # auto-registers if pandas installed
    # or: import humanmint.pandas
    df_clean = df.humanmint.clean()
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional, Union

import pandas as pd
from .column_guess import COLUMN_GUESSES  # noqa: F401


@pd.api.extensions.register_dataframe_accessor("humanmint")
class HumanMintAccessor:
    """Pandas accessor for batch-cleaning DataFrame columns with humanmint."""

    def __init__(self, pandas_obj: pd.DataFrame):
        self._obj = pandas_obj

    def clean(
        self,
        name_col: Optional[str] = None,
        email_col: Optional[str] = None,
        phone_col: Optional[str] = None,
        address_col: Optional[str] = None,
        org_col: Optional[str] = None,
        dept_col: Optional[str] = None,
        title_col: Optional[str] = None,
        cols: Optional[Iterable[str]] = None,
        use_bulk: bool = False,
        workers: int = 4,
        progress: Union[bool, str, Callable[[], None]] = False,
    ) -> pd.DataFrame:
        """
        Clean a DataFrame using humanmint.mint with optional column auto-detection.

        Args:
            name_col: Column containing names (auto-detected if None).
            email_col: Column containing emails (auto-detected if None).
            phone_col: Column containing phone numbers (auto-detected if None).
            address_col: Column containing addresses (auto-detected if None).
            org_col: Column containing organization/agency names (auto-detected if None).
            dept_col: Column containing department values (auto-detected if None).
            title_col: Column containing job titles (auto-detected if None).
            cols: Optional iterable of column names to limit auto-detection.
            use_bulk: If True, use threaded bulk() for processing instead of per-row apply.
            workers: Worker threads for bulk mode.
            progress: Pass-through to bulk() progress (True/"rich"/callable).

        Returns:
            New DataFrame with added hm_* columns for normalized data.
        """
        from .column_guess import COLUMN_GUESSES, guess_column
        from .mint import bulk, mint

        df = self._obj.copy()
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        df_cols = list(df.columns)
        allowed = set(df_cols) if cols is None else {c for c in cols if c in df.columns}

        name_col = guess_column(df_cols, name_col, COLUMN_GUESSES["name"], allowed)
        email_col = guess_column(df_cols, email_col, COLUMN_GUESSES["email"], allowed)
        phone_col = guess_column(df_cols, phone_col, COLUMN_GUESSES["phone"], allowed)
        address_col = guess_column(
            df_cols, address_col, COLUMN_GUESSES["address"], allowed
        )
        org_col = guess_column(
            df_cols, org_col, COLUMN_GUESSES["organization"], allowed
        )
        dept_col = guess_column(
            df_cols, dept_col, COLUMN_GUESSES["department"], allowed
        )
        title_col = guess_column(df_cols, title_col, COLUMN_GUESSES["title"], allowed)

        if use_bulk:
            records = [
                {
                    "name": row[name_col] if name_col else None,
                    "email": row[email_col] if email_col else None,
                    "phone": row[phone_col] if phone_col else None,
                    "address": row[address_col] if address_col else None,
                    "department": row[dept_col] if dept_col else None,
                    "title": row[title_col] if title_col else None,
                    "organization": row[org_col] if org_col else None,
                }
                for _, row in df.iterrows()
            ]
            results = bulk(records, workers=workers, progress=progress)
        else:
            results = [
                mint(
                    name=row[name_col] if name_col else None,
                    email=row[email_col] if email_col else None,
                    phone=row[phone_col] if phone_col else None,
                    address=row[address_col] if address_col else None,
                    department=row[dept_col] if dept_col else None,
                    title=row[title_col] if title_col else None,
                    organization=row[org_col] if org_col else None,
                )
                for _, row in df.iterrows()
            ]

        cleaned = pd.DataFrame(
            [
                {
                    "hm_name_full": (result.name or {}).get("full")
                    if result.name
                    else None,
                    "hm_name_first": (result.name or {}).get("first")
                    if result.name
                    else None,
                    "hm_name_last": (result.name or {}).get("last")
                    if result.name
                    else None,
                    "hm_name_gender": (result.name or {}).get("gender")
                    if result.name
                    else None,
                    "hm_email": (result.email or {}).get("normalized")
                    if result.email
                    else None,
                    "hm_email_domain": (result.email or {}).get("domain")
                    if result.email
                    else None,
                    "hm_email_is_generic": (result.email or {}).get("is_generic_inbox")
                    if result.email
                    else None,
                    "hm_email_is_free_provider": (result.email or {}).get(
                        "is_free_provider"
                    )
                    if result.email
                    else None,
                    "hm_phone": (result.phone or {}).get("pretty")
                    if result.phone
                    else None,
                    "hm_address_canonical": (result.address or {}).get("canonical")
                    if result.address
                    else None,
                    "hm_address_city": (result.address or {}).get("city")
                    if result.address
                    else None,
                    "hm_address_state": (result.address or {}).get("state")
                    if result.address
                    else None,
                    "hm_address_zip": (result.address or {}).get("zip")
                    if result.address
                    else None,
                    "hm_organization": (result.organization or {}).get("canonical")
                    if result.organization
                    else None,
                    "hm_department": (result.department or {}).get("canonical")
                    if result.department
                    else None,
                    "hm_department_category": (result.department or {}).get("category")
                    if result.department
                    else None,
                    "hm_title_canonical": (result.title or {}).get("canonical")
                    if result.title
                    else None,
                    "hm_title_is_valid": (result.title or {}).get("is_valid")
                    if result.title
                    else None,
                }
                for result in results
            ],
            index=df.index,
        )

        return pd.concat([df, cleaned], axis=1)
