"""Convenience module to register the pandas accessor."""

try:
    from .pandas_ext import COLUMN_GUESSES, HumanMintAccessor
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "humanmint pandas integration requires pandas to be installed. "
        "Install with: pip install humanmint[pandas]"
    ) from exc

__all__ = ["COLUMN_GUESSES", "HumanMintAccessor"]
