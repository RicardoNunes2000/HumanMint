"""HumanMint: Clean, functional data processing for human-centric applications."""

from __future__ import annotations

import importlib
from typing import Any, Dict

__version__ = "2.0.1"

# Lazy module/function map to avoid heavy imports on initial import humanmint
_LAZY_MODULES: Dict[str, str] = {
    "emails": "humanmint.emails",
    "phones": "humanmint.phones",
    "names": "humanmint.names",
    "departments": "humanmint.departments",
    "titles": "humanmint.titles",
    "addresses": "humanmint.addresses",
    "organizations": "humanmint.organizations",
    "compare": "humanmint.compare",
    "mint": "humanmint.mint",
    "bulk": "humanmint.mint",
    "MintResult": "humanmint.mint",
    "extract_phones": "humanmint.phones",
    "export_json": "humanmint.export",
    "export_csv": "humanmint.export",
    "export_parquet": "humanmint.export",
    "export_sql": "humanmint.export",
}

# Eagerly bind common callables to avoid submodule shadowing (e.g., `from humanmint import mint`)
try:  # pragma: no cover - safe eager binding
    _mint_mod = importlib.import_module("humanmint.mint")
    mint = _mint_mod.mint
    bulk = _mint_mod.bulk
    MintResult = _mint_mod.MintResult
except Exception:
    pass


def __getattr__(name: str) -> Any:
    """Lazy-load heavy modules/functions on first access.

    Args:
        name: The attribute name to load.

    Returns:
        The requested module, function, or class.

    Raises:
        AttributeError: If the attribute does not exist in _LAZY_MODULES.

    Example:
        >>> from humanmint import mint  # triggers __getattr__
        >>> result = mint(name="John Doe")
    """
    if name in _LAZY_MODULES:
        module = importlib.import_module(_LAZY_MODULES[name])
        attr = getattr(module, name) if hasattr(module, name) else module
        # If we intended a function/class but got the module, try common exports
        if attr is module and name in {"mint", "bulk", "MintResult"}:
            attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(f"module 'humanmint' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Return list of public attributes and lazy-loaded modules.

    Returns:
        Sorted list of all available module attributes and lazy-loadable names.

    Example:
        >>> 'mint' in dir(humanmint)
        True
    """
    return sorted(list(globals().keys()) + list(_LAZY_MODULES.keys()))


__all__ = list(_LAZY_MODULES.keys()) + ["__version__"]
# Optional pandas accessor registration (graceful if pandas not installed)
try:  # pragma: no cover - optional dependency
    importlib.import_module("humanmint.pandas_ext")  # noqa: F401
except Exception:
    pass
