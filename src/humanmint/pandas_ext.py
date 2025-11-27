"""
Pandas DataFrame accessor for HumanMint.

Usage:
    import humanmint  # auto-registers if pandas installed
    # or: import humanmint.pandas
    df_clean = df.humanmint.clean()
"""

from __future__ import annotations

from typing import Iterable, Optional
import pandas as pd

from .mint import mint
from .column_guess import COLUMN_GUESSES, guess_column


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
        dept_col: Optional[str] = None,
        title_col: Optional[str] = None,
        cols: Optional[Iterable[str]] = None,
    ) -> pd.DataFrame:
        """
        Clean a DataFrame using humanmint.mint with optional column auto-detection.

        Args:
            name_col: Column containing names (auto-detected if None).
            email_col: Column containing emails (auto-detected if None).
            phone_col: Column containing phone numbers (auto-detected if None).
            dept_col: Column containing department values (auto-detected if None).
            title_col: Column containing job titles (auto-detected if None).
            cols: Optional iterable of column names to limit auto-detection.

        Returns:
            New DataFrame with added hm_* columns for normalized data.
        """
        df = self._obj.copy()
        df_cols = list(df.columns)
        allowed = set(df_cols) if cols is None else {c for c in cols if c in df.columns}

        name_col = guess_column(df_cols, name_col, COLUMN_GUESSES["name"], allowed)
        email_col = guess_column(df_cols, email_col, COLUMN_GUESSES["email"], allowed)
        phone_col = guess_column(df_cols, phone_col, COLUMN_GUESSES["phone"], allowed)
        dept_col = guess_column(df_cols, dept_col, COLUMN_GUESSES["department"], allowed)
        title_col = guess_column(df_cols, title_col, COLUMN_GUESSES["title"], allowed)

        def apply_mint(row: pd.Series) -> pd.Series:
            result = mint(
                name=row[name_col] if name_col else None,
                email=row[email_col] if email_col else None,
                phone=row[phone_col] if phone_col else None,
                department=row[dept_col] if dept_col else None,
                title=row[title_col] if title_col else None,
            )

            return pd.Series(
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
                    "hm_email": (result.email or {}).get("normalized") if result.email else None,
                    "hm_email_domain": (result.email or {}).get("domain") if result.email else None,
                    "hm_email_is_generic": (result.email or {}).get("is_generic") if result.email else None,
                    "hm_phone": (result.phone or {}).get("pretty") if result.phone else None,
                    "hm_department": (result.department or {}).get("canonical") if result.department else None,
                    "hm_department_category": (result.department or {}).get("category") if result.department else None,
                    "hm_title_canonical": (result.title or {}).get("canonical")
                    if result.title
                    else None,
                    "hm_title_is_valid": (result.title or {}).get("is_valid")
                    if result.title
                    else None,
                }
            )

        cleaned = df.apply(apply_mint, axis=1)
        return pd.concat([df, cleaned], axis=1)
