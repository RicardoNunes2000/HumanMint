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
    txt_path = ORIGINAL_DIR / "department_mappings_list.txt"
    csv_path = ORIGINAL_DIR / "department_mappings_list.csv"
    cache_path = DATA_DIR / "department_mappings_list.json.gz"

    mappings: Dict[str, List[str]] = {}
    reverse: Dict[str, str] = {}

    if txt_path.exists():
        with open(txt_path, "r", encoding="utf-8", newline="") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "\t" in line:
                    canonical, original = [p.strip() for p in line.split("\t", 1)]
                else:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 2:
                        canonical, original = parts[0], parts[1]
                    else:
                        continue
                if not canonical or not original:
                    continue
                mappings.setdefault(canonical, []).append(original)
                reverse[original.lower()] = canonical
    else:
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
    txt_path = ORIGINAL_DIR / "names.txt"
    csv_path = ORIGINAL_DIR / "names.csv"
    cache_path = DATA_DIR / "names.json.gz"

    genders: Dict[str, str] = {}
    if txt_path.exists():
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "\t" in line:
                    name, gender = [p.strip() for p in line.split("\t", 1)]
                else:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 2:
                        name, gender = parts[0], parts[1]
                    else:
                        continue
                name = name.lower()
                gender = gender.upper()
                if name and gender in ("M", "F"):
                    genders[name] = gender
    else:
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


def build_title_constants() -> tuple[Path, Path, Path]:
    """Build title abbreviation/stopword/preserve caches."""
    _ensure_dirs()
    abbr_path = ORIGINAL_DIR / "title_abbreviations.txt"
    stop_path = ORIGINAL_DIR / "title_stopwords.txt"
    preserve_path = ORIGINAL_DIR / "title_preserve_abbreviations.txt"

    abbr_cache = DATA_DIR / "title_abbreviations.json.gz"
    stop_cache = DATA_DIR / "title_stopwords.json.gz"
    preserve_cache = DATA_DIR / "title_preserve_abbreviations.json.gz"

    if not abbr_path.exists():
        raise FileNotFoundError(f"Missing title abbreviations file: {abbr_path}")
    if not stop_path.exists():
        raise FileNotFoundError(f"Missing title stopwords file: {stop_path}")
    if not preserve_path.exists():
        raise FileNotFoundError(f"Missing title preserve abbreviations file: {preserve_path}")

    def _read_kv(path: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                k, v = [p.strip() for p in line.split(",", 1)]
            else:
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) >= 2:
                    k, v = parts[0], " ".join(parts[1:])
                else:
                    continue
            if k and v:
                out[k.lower()] = v
        return out

    abbreviations = _read_kv(abbr_path)
    stopwords = [
        line.strip()
        for line in stop_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    preserve = [
        line.strip()
        for line in preserve_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    abbr_cache.write_bytes(gzip.compress(json.dumps(abbreviations).encode("utf-8")))
    stop_cache.write_bytes(gzip.compress(json.dumps(stopwords).encode("utf-8")))
    preserve_cache.write_bytes(gzip.compress(json.dumps(preserve).encode("utf-8")))

    return abbr_cache, stop_cache, preserve_cache


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


def build_seniority_keywords_pickle() -> Path:
    """Build ordered seniority keyword list cache."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "seniority_keywords.txt"
    cache_path = DATA_DIR / "seniority_keywords.json.gz"

    if not txt_path.exists():
        raise FileNotFoundError(f"Missing seniority keywords file: {txt_path}")

    keywords: list[str] = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            keywords.append(stripped)

    cache_path.write_bytes(gzip.compress(json.dumps(keywords).encode("utf-8")))
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


def build_name_constants() -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    """Build name-related constant caches."""
    _ensure_dirs()
    paths = {
        "gen": ORIGINAL_DIR / "name_generational_suffixes.txt",
        "cred": ORIGINAL_DIR / "name_credential_suffixes.txt",
        "corp": ORIGINAL_DIR / "name_corporate_terms.txt",
        "non_person": ORIGINAL_DIR / "name_non_person_phrases.txt",
        "roman": ORIGINAL_DIR / "name_roman_numerals.txt",
        "prefixes": ORIGINAL_DIR / "name_title_prefixes.txt",
        "placeholders": ORIGINAL_DIR / "name_placeholder_names.txt",
    }
    for label, p in paths.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing name constants file: {p}")

    caches = {
        "gen": DATA_DIR / "name_generational_suffixes.json.gz",
        "cred": DATA_DIR / "name_credential_suffixes.json.gz",
        "corp": DATA_DIR / "name_corporate_terms.json.gz",
        "non_person": DATA_DIR / "name_non_person_phrases.json.gz",
        "roman": DATA_DIR / "name_roman_numerals.json.gz",
        "prefixes": DATA_DIR / "name_title_prefixes.json.gz",
        "placeholders": DATA_DIR / "name_placeholder_names.json.gz",
    }

    def _read_list(path: Path) -> list[str]:
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def _read_kv(path: Path) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "," in line:
                k, v = [p.strip() for p in line.split(",", 1)]
            else:
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) >= 2:
                    k, v = parts[0], " ".join(parts[1:])
                else:
                    continue
            if k and v:
                out[k.lower()] = v
        return out

    gen = _read_list(paths["gen"])
    cred = _read_list(paths["cred"])
    corp = _read_list(paths["corp"])
    non_person = _read_list(paths["non_person"])
    roman = _read_kv(paths["roman"])
    prefixes = _read_list(paths["prefixes"])
    placeholders = _read_list(paths["placeholders"])

    caches["gen"].write_bytes(gzip.compress(json.dumps(gen).encode("utf-8")))
    caches["cred"].write_bytes(gzip.compress(json.dumps(cred).encode("utf-8")))
    caches["corp"].write_bytes(gzip.compress(json.dumps(corp).encode("utf-8")))
    caches["non_person"].write_bytes(
        gzip.compress(json.dumps(non_person).encode("utf-8"))
    )
    caches["roman"].write_bytes(gzip.compress(json.dumps(roman).encode("utf-8")))
    caches["prefixes"].write_bytes(
        gzip.compress(json.dumps(prefixes).encode("utf-8"))
    )
    caches["placeholders"].write_bytes(
        gzip.compress(json.dumps(placeholders).encode("utf-8"))
    )

    return tuple(caches.values())


def build_semantic_tokens_pickle() -> Path:
    """Build semantic tokens cache for domain-based semantic validation."""
    _ensure_dirs()
    txt_path = ORIGINAL_DIR / "semantic_tokens.txt"
    json_path = ORIGINAL_DIR / "semantic_tokens.json"
    cache_path = DATA_DIR / "semantic_tokens.json.gz"

    data: Dict[str, str] = {}
    if txt_path.exists():
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "\t" in line:
                    token, domain = [p.strip() for p in line.split("\t", 1)]
                else:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 2:
                        token, domain = parts[0], parts[1]
                    else:
                        continue
                if token and domain:
                    data[token] = domain
    else:
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
        ("Title constants", lambda: build_title_constants()[0]),
        ("Name constants", lambda: build_name_constants()[0]),
        ("Semantic tokens", build_semantic_tokens_pickle),
        ("Department abbreviations", build_department_abbreviations_pickle),
        ("Generic inboxes", build_generic_inboxes_pickle),
        ("Seniority keywords", build_seniority_keywords_pickle),
        ("Free email providers", build_free_email_providers_pickle),
    )

    print(f"Data directory: {DATA_DIR}")
    for label, fn in builders:
        path = fn()
        print(f"[ok] {label} -> {path}")


if __name__ == "__main__":
    main()
