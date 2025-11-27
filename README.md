# HumanMint

Clean, functional data processing for human-centric applications. Normalize and standardize names, emails, phones, departments, and job titles with a single unified API.

## Installation

```bash
pip install humanmint
```

## Quick Start

```python
from humanmint import mint

result = mint(
    name="Dr. John Smith",
    email="JOHN.SMITH@CITY.GOV",
    phone="(555) 123-4567",
    department="Public Works 850-123-1234 ext 200",
    title="Chief of Police"
)

print(result.name)              # {'full': 'John Smith', 'first': 'John', 'last': 'Smith', 'gender': 'Male'}
print(result.email)             # 'john.smith@city.gov'
print(result.phone)             # '+1 555-123-4567'
print(result.department)        # 'Public Works'
print(result.department_category) # 'Infrastructure'
print(result.title)             # {'canonical': 'police chief', 'is_valid': True, ...}
```

## Why HumanMint?

### Problem
Real-world contact data is messy:
- Names with titles: "Dr. Jane Smith, PhD"
- Phone numbers in various formats: "(555) 123-4567" vs "555.123.4567"
- Departments with codes and noise: "000171 - Public Works 555-123-1234 ext 200"
- Job titles that need standardization: "Chief of Police" -> canonical form
- Emails with inconsistent casing: "JOHN.SMITH@EXAMPLE.COM"
- Single names that need gender inference: "Jo", "Al", "Ty"

### Solution
HumanMint cleans and standardizes everything in one call.

## Features

- Unified API: One `mint()` call to normalize names, emails, phones, departments, and titles.
- Rich names: Normalize, enrich, and infer gender; handles single, hyphenated, and titled names.
- Emails: Lowercasing, validation, generic inbox detection, domain extraction.
- Phones: Pretty/E164 formats, extension extraction, validation.
- Departments: 23,452 mappings to 63 canonicals with fuzzy matching and category tagging.
- Titles: Canonicalization and fuzzy matching against curated heuristics.
- Pandas: `df.humanmint.clean(...)` accessor with heuristic column guessing or explicit `name_col/email_col/...` mapping.
- CLI: `humanmint clean input.csv output.csv` with auto-guessing or explicit `--name-col/--email-col/--phone-col/--dept-col/--title-col`.
- Gzip-backed data: Reference data ships as `.json.gz` caches for fast loads; raw sources live under `src/humanmint/data/original/`.
- Ethics: Gender inference is probabilistic from historical name data and not a determination of identity; downstream use should respect that.

## API Reference

### `mint(name, email, phone, department, title)`

One function. All your data cleaned.

```python
result = mint(
    name="Jane Doe",              # optional
    email="jane@example.com",     # optional
    phone="(555) 555-5555",       # optional
    department="Water Utilities", # optional
    title="Chief of Water"        # optional
)

# Access cleaned data
result.name              # dict: {full, first, last, gender}
result.email            # str
result.phone            # str
result.department       # str (canonical)
result.department_category  # str
result.title            # dict: {raw, cleaned, canonical, is_valid}

# Convert to dict for JSON
result.model_dump()
```

## Customization

You can steer canonicals without forking data files:

- **Department overrides:** Map normalized departments to your preferred canonical. Example: `mint(department="RevOps", dept_overrides={"revenue operations": "Sales"})` or pass the same dict into `bulk()`/pandas/CLI.
- **Title overrides / ignores:** Map cleaned titles to a canonical string with `title_overrides`. To ignore a title, set it to `None` and drop records where `result.title` is `None` or `result.title["is_valid"]` is `False`.

## Examples

### Government Contact
```python
result = mint(
    name="Chief Robert Patterson",
    email="robert.patterson@police.gov",
    phone="(555) 123-4567",
    department="000171 - Police",
    title="Chief of Police"
)

# Cleaned:
# name: {'full': 'Robert Patterson', 'first': 'Robert', 'last': 'Patterson', 'gender': 'Male'}
# email: 'robert.patterson@police.gov'
# phone: '+1 555-123-4567'
# department: 'Police' (category: 'Public Safety')
# title: {'canonical': 'police chief', 'is_valid': True}
```

### Messy Data
```python
result = mint(
    name="Dr. Jane Smith, PhD",
    email="JANE@EXAMPLE.COM",
    phone="555 123 4567",
    department="Planning and Development 555-123-4567 ext 200"
)

# Cleaned:
# name: {'full': 'Jane Smith', 'first': 'Jane', 'last': 'Smith', 'gender': 'Female'}
# email: 'jane@example.com'
# phone: '+1 555-123-4567'
# department: 'Planning' (category: 'Planning & Development')
```

### Single Names
```python
result = mint(name="Madonna")
# name: {'full': 'Madonna', 'first': 'Madonna', 'last': '', 'gender': 'Female'}

result = mint(name="Jo")
# name: {'full': 'Jo', 'first': 'Jo', 'last': '', 'gender': 'Female'}
```

## Advanced Usage

Use individual modules for specific needs:

```python
from humanmint.names import normalize_name, infer_gender
from humanmint.emails import normalize_email
from humanmint.phones import normalize_phone
from humanmint.departments import find_best_match, get_department_category
from humanmint.titles import normalize_title_full, find_best_match as match_title
```

## Testing

```bash
pytest -q unittests
```

## CLI

Clean a CSV (auto-detecting columns, or override with flags):

```bash
humanmint clean input.csv output.csv --name-col name --email-col email
```

## Regenerating data caches

If you edit the raw datasets in `src/humanmint/data/original/`, rebuild the packaged `.json.gz` caches with:

```bash
python scripts/build_caches.py
```

## Performance

- **Batch processing:** ~0.1-0.2ms per contact
- **10 contacts:** ~1-2ms
- **100 contacts:** ~10-20ms

## What Gets Cleaned

| Input | Output |
|-------|--------|
| `name="Dr. Jane Smith, PhD"` | `first='Jane', last='Smith'` |
| `email="JOHN@EXAMPLE.COM"` | `john@example.com` |
| `phone="(555) 123-4567 x101"` | `+1 555-123-4567`, extension: `101` |
| `department="000171 - Public Works 555-123-1234 ext 200"` | `Public Works` (category: Infrastructure) |
| `title="0001 - Chief of Police (Downtown)"` | `police chief` |
| `name="Jo"` | `first='Jo'`, gender: Female |

## Version

0.1.0

## License

MIT
