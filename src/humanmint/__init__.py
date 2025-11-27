"""HumanMint: Clean, functional data processing for human-centric applications."""

from . import emails, phones, names, departments, titles
from .mint import mint, MintResult

__version__ = "0.1.0"
__all__ = ["emails", "phones", "names", "departments", "titles", "mint", "MintResult"]

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
