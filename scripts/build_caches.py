"""
Utility script to precompute compressed JSON caches for packaged data.

Reads raw assets from the top-level `original/` folder (CSV/TXT) and writes
`.json.gz` files into `src/humanmint/data` for runtime use. Safe to run
repeatedly; files are overwritten.
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Callable, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "humanmint" / "data"
# Try root-level original/ first, then fall back to src/humanmint/data/original/
ORIGINAL_DIR = ROOT / "original"
if not ORIGINAL_DIR.exists():
    ORIGINAL_DIR = DATA_DIR / "original"


def _ensure_dirs() -> None:
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ORIGINAL_DIR.exists():
        raise FileNotFoundError(f"Original data directory not found: {ORIGINAL_DIR}")


def build_department_pickle() -> Path:
    """Build department mappings cache."""
    _ensure_dirs()
    csv_path = ORIGINAL_DIR / "department_mappings_list.csv"
    cache_path = DATA_DIR / "department_mappings_list.json.gz"

    mappings: Dict[str, List[str]] = {}
    reverse: Dict[str, str] = {}

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            canonical = row["standardized_name"].strip()
            original = row["original_name"].strip()
            if not canonical or not original:
                continue
            mappings.setdefault(canonical, []).append(original)
            reverse[original.lower()] = canonical

    payload = {"mappings": mappings, "reverse": reverse}
    cache_path.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))
    return cache_path


def build_names_pickle() -> Path:
    """Build names gender cache."""
    _ensure_dirs()
    csv_path = ORIGINAL_DIR / "names.csv"
    cache_path = DATA_DIR / "names.json.gz"

    genders: Dict[str, str] = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip().lower()
            gender = row.get("gender", "").strip().upper()
            if name and gender in ("M", "F"):
                genders[name] = gender

    cache_path.write_bytes(gzip.compress(json.dumps(genders).encode("utf-8")))
    return cache_path


def build_titles_pickle() -> Path:
    """Build title heuristics cache."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "title_heuristics.txt"
    cache_path = DATA_DIR / "title_heuristics.json.gz"

    canonicals: List[str] = []
    mappings: Dict[str, str] = {}

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if not parts:
                continue
            canonical = parts[0]
            canonicals.append(canonical)
            mappings[canonical.lower()] = canonical
            for variant in parts[1:]:
                mappings[variant.lower()] = canonical

    payload = {"canonicals": canonicals, "mappings": mappings}
    cache_path.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))
    return cache_path


def build_generic_inboxes_pickle() -> Path:
    """Build generic inboxes cache."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "generic_inboxes.txt"
    cache_path = DATA_DIR / "generic_inboxes.json.gz"

    inboxes: Set[str] = set()
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            inbox = line.strip().lower()
            if inbox:
                inboxes.add(inbox)

    cache_path.write_bytes(gzip.compress(json.dumps(sorted(inboxes)).encode("utf-8")))
    return cache_path


def build_free_email_providers_pickle() -> Path:
    """Build free email providers cache."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "free_email_providers.txt"
    cache_path = DATA_DIR / "free_email_providers.json.gz"

    providers: Set[str] = set()
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            provider = line.strip().lower()
            if provider:
                providers.add(provider)

    cache_path.write_bytes(gzip.compress(json.dumps(sorted(providers)).encode("utf-8")))
    return cache_path


def build_semantic_tokens_pickle() -> Path:
    """Build semantic tokens cache for domain-based semantic validation."""
    _ensure_dirs()
    json_path = ORIGINAL_DIR / "semantic_tokens.json"
    cache_path = DATA_DIR / "semantic_tokens.json.gz"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cache_path.write_bytes(gzip.compress(json.dumps(data).encode("utf-8")))
    return cache_path


def build_department_abbreviations_pickle() -> Path:
    """Build department abbreviation cache (abbr -> expansion)."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "department_abbreviations.txt"
    cache_path = DATA_DIR / "department_abbreviations.json.gz"

    if not txt_path.exists():
        raise FileNotFoundError(f"Missing department abbreviations file: {txt_path}")

    mappings: Dict[str, str] = {}
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                key, value = [p.strip() for p in line.split(",", 1)]
            elif "\t" in line:
                key, value = [p.strip() for p in line.split("\t", 1)]
            else:
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) >= 2:
                    key, value = parts[0], " ".join(parts[1:])
                else:
                    continue
            if key and value:
                mappings[key.lower()] = value

    cache_path.write_bytes(gzip.compress(json.dumps(mappings).encode("utf-8")))
    return cache_path


def main() -> None:
    builders: Tuple[tuple[str, Callable[[], Path]], ...] = (
        ("Departments", build_department_pickle),
        ("Names", build_names_pickle),
        ("Titles", build_titles_pickle),
        ("Semantic tokens", build_semantic_tokens_pickle),
        ("Department abbreviations", build_department_abbreviations_pickle),
        ("Generic inboxes", build_generic_inboxes_pickle),
        ("Free email providers", build_free_email_providers_pickle),
    )

    print(f"Data directory: {DATA_DIR}")
    for label, fn in builders:
        path = fn()
        print(f"[ok] {label} -> {path}")


if __name__ == "__main__":
    main()
