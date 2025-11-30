"""
Centralized utilities for loading data from the humanmint.data package.

Provides unified handling for:
- Python version detection (importlib.resources vs importlib_resources)
- Package resource file loading
- GZIP decompression
- JSON parsing (with orjson for performance)

This module eliminates repeated boilerplate across data loaders.
"""

import sys
import gzip
from typing import Any
from pathlib import Path

import orjson

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


def load_package_json_gz(filename: str) -> Any:
    """
    Load and decompress a JSON.gz file from the humanmint.data package.

    Optimized with orjson for fast parsing directly from bytes, skipping
    expensive UTF-8 decoding step. Attempts to load from package resources
    first, then falls back to a local file path for development/testing.

    Args:
        filename: Name of the .json.gz file to load (e.g., "departments.json.gz").

    Returns:
        Parsed JSON content as a Python object (dict, list, etc.).

    Raises:
        FileNotFoundError: If the file cannot be found in either location.
        ValueError: If the JSON is malformed.

    Example:
        >>> data = load_package_json_gz("department_mappings_list.json.gz")
        >>> isinstance(data, dict)
        True
    """
    try:
        # Try package resource first
        data_path = files("humanmint.data").joinpath(filename)
        # orjson.loads() accepts bytes directly (no .decode() needed)
        compressed_bytes = data_path.read_bytes()
        decompressed_bytes = gzip.decompress(compressed_bytes)
        return orjson.loads(decompressed_bytes)
    except (FileNotFoundError, AttributeError, TypeError, ModuleNotFoundError):
        pass

    # Fallback for development/testing (direct path relative to this file)
    local_path = Path(__file__).parent / filename
    if local_path.exists():
        # orjson.loads() accepts bytes directly (no .decode() needed)
        compressed_bytes = local_path.read_bytes()
        decompressed_bytes = gzip.decompress(compressed_bytes)
        return orjson.loads(decompressed_bytes)

    raise FileNotFoundError(f"Could not load data file: {filename}")
