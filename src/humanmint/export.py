"""
Export utilities for batch-processed results.

Provides functions to export cleaned and normalized data to various formats
(JSON, CSV, Parquet, SQL) for downstream processing and analysis.

Example:
    >>> from humanmint import bulk, export_json
    >>> records = [{"name": "John Doe", "email": "john@example.com"}, ...]
    >>> results = bulk(records)
    >>> export_json(results, "cleaned.json")
"""

import json
import csv
from pathlib import Path
from typing import List, Any, Dict

from .mint import MintResult


def export_json(results: List[MintResult], filepath: str) -> None:
    """
    Export normalized results to JSON file.

    Args:
        results: List of MintResult objects from mint() or bulk().
        filepath: Path to write JSON file to.

    Example:
        >>> from humanmint import bulk, export_json
        >>> results = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        >>> export_json(results, "cleaned.json")
    """
    output_path = Path(filepath)
    data = [result.model_dump() for result in results]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_csv(
    results: List[MintResult],
    filepath: str,
    flatten: bool = True,
) -> None:
    """
    Export normalized results to CSV file.

    Flattens nested dictionaries by default (e.g., name.first becomes name_first).
    Set flatten=False to export each field as JSON strings.

    Args:
        results: List of MintResult objects from mint() or bulk().
        filepath: Path to write CSV file to.
        flatten: If True, flatten nested dicts (name_first, email_domain, etc.).
                If False, keep nested structure as JSON strings.

    Example:
        >>> from humanmint import bulk, export_csv
        >>> results = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        >>> export_csv(results, "cleaned.csv")
    """
    if not results:
        return

    output_path = Path(filepath)

    if flatten:
        rows = [_flatten_result(result) for result in results]
    else:
        rows = [result.model_dump() for result in results]

    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_parquet(
    results: List[MintResult],
    filepath: str,
    flatten: bool = True,
) -> None:
    """
    Export normalized results to Parquet file (Apache Parquet format).

    Requires pyarrow or fastparquet to be installed.
    Flattens nested dictionaries by default.

    Args:
        results: List of MintResult objects from mint() or bulk().
        filepath: Path to write Parquet file to.
        flatten: If True, flatten nested dicts (name_first, email_domain, etc.).
                If False, keep nested structure as JSON strings.

    Raises:
        ImportError: If pandas and pyarrow are not installed.

    Example:
        >>> from humanmint import bulk, export_parquet
        >>> results = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        >>> export_parquet(results, "cleaned.parquet")
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "export_parquet requires pandas. Install with: pip install pandas pyarrow"
        )

    if not results:
        return

    if flatten:
        rows = [_flatten_result(result) for result in results]
    else:
        rows = [result.model_dump() for result in results]

    df = pd.DataFrame(rows)
    df.to_parquet(filepath, index=False)


def export_sql(
    results: List[MintResult],
    connection: Any,
    table_name: str,
    if_exists: str = "replace",
    flatten: bool = True,
) -> None:
    """
    Export normalized results to SQL database.

    Requires sqlalchemy to be installed.
    Flattens nested dictionaries by default.

    Args:
        results: List of MintResult objects from mint() or bulk().
        connection: SQLAlchemy connection or engine object.
        table_name: Name of table to write to.
        if_exists: How to behave if table exists ("fail", "replace", "append").
        flatten: If True, flatten nested dicts (name_first, email_domain, etc.).
                If False, keep nested structure as JSON strings.

    Raises:
        ImportError: If pandas and sqlalchemy are not installed.

    Example:
        >>> from humanmint import bulk, export_sql
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine("sqlite:///cleaned.db")
        >>> results = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        >>> export_sql(results, engine, "cleaned_contacts")
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "export_sql requires pandas. Install with: pip install pandas sqlalchemy"
        )

    if not results:
        return

    if flatten:
        rows = [_flatten_result(result) for result in results]
    else:
        rows = [result.model_dump() for result in results]

    df = pd.DataFrame(rows)
    df.to_sql(table_name, connection, if_exists=if_exists, index=False)


def _flatten_result(result: MintResult) -> Dict[str, Any]:
    """
    Flatten a MintResult object into a single-level dictionary.

    Nested fields become underscore-separated keys:
    - name.first → name_first
    - email.domain → email_domain
    - phone.e164 → phone_e164
    """
    flat = {}

    for field_name in [
        "name",
        "email",
        "phone",
        "department",
        "title",
        "address",
        "organization",
    ]:
        field_value = getattr(result, field_name, None)

        if field_value is None:
            flat[field_name] = None
        elif isinstance(field_value, dict):
            for key, val in field_value.items():
                flat_key = f"{field_name}_{key}"
                flat[flat_key] = val
        else:
            flat[field_name] = field_value

    return flat
