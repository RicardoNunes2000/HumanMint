"""HumanMint: Clean, functional data processing for human-centric applications."""

from . import (addresses, departments, emails, names, organizations, phones,
               titles)
from .compare import compare
from .export import export_csv, export_json, export_parquet, export_sql
from .mint import MintResult, bulk, mint

__version__ = "2.0.0b8"
__all__ = [
    "emails",
    "phones",
    "names",
    "departments",
    "titles",
    "addresses",
    "organizations",
    "mint",
    "bulk",
    "MintResult",
    "compare",
    "export_json",
    "export_csv",
    "export_parquet",
    "export_sql",
]

# Optional pandas accessor registration
try:  # pragma: no cover - optional dependency
    import pandas as _pd  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover
    _pd = None
else:  # pragma: no cover
    try:
        from . import pandas_ext  # noqa: F401
    except Exception:
        # Avoid breaking base import if pandas or accessor cannot load
        pass
