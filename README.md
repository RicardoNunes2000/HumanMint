# HumanMint

Clean, functional data processing for human-centric applications. Normalize and standardize names, emails, phones, addresses, departments, job titles, and organizations with a single unified API.

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
    phone="(202) 555-0173",  # Use real area codes; 555 is reserved for fictional use
    address="123 Main St, Springfield, IL 62701",
    department="Public Works 850-123-1234 ext 200",
    title="Chief of Police"
)

print(result.name)              # {'full': 'John Smith', 'first': 'John', 'last': 'Smith', 'gender': 'Male'}
print(result.email)             # 'john.smith@city.gov'
print(result.phone)             # '+1 202-555-0173'
print(result.address)           # {'street': '123 Main St', 'city': 'Springfield', 'state': 'IL', 'zip': '62701'}
print(result.department)        # 'Public Works'
print(result.department_category) # 'Infrastructure'
print(result.title)             # {'canonical': 'police chief', 'is_valid': True, ...}
```

## Why HumanMint?

### Problem
Real-world contact data is messy:
- Names with titles: "Dr. Jane Smith, PhD"
- Phone numbers in various formats: "(202) 555-0123" vs "202.555.0123" (use real area codes; 555 is reserved for fiction)
- Departments with codes and noise: "000171 - Public Works 202-555-0150 ext 200"
- Job titles that need standardization: "Chief of Police" -> canonical form
- Emails with inconsistent casing: "JOHN.SMITH@EXAMPLE.COM"
- Single names that need gender inference: "Jo", "Al", "Ty"

### Solution
HumanMint cleans and standardizes everything in one call.

## Features

- **Unified API:** One `mint()` call to normalize names, emails, phones, addresses, departments, titles, and organizations.
- **Rich names:** Normalize, enrich, infer gender, detect nicknames; handles single, hyphenated, and titled names.
- **Emails:** Lowercasing, validation, generic inbox detection, domain extraction, free provider detection.
- **Phones:** E164/pretty formats, extension extraction, validation, type detection (mobile/landline/fax), VoIP and impossible number detection.
- **Addresses:** US postal address parsing (street, city, state, ZIP).
- **Departments:** 23,452 mappings to 64 canonicals with fuzzy matching, categorization, and custom overrides.
- **Titles:** Canonicalization and fuzzy matching against curated heuristics with confidence scores.
- **Organizations:** Normalize agency/organization names by removing civic prefixes and suffixes.
- **Pandas:** `df.humanmint.clean(...)` accessor with heuristic column guessing or explicit `name_col/email_col/...` mapping.
- **CLI:** `humanmint clean input.csv output.csv` with auto-guessing or explicit column flags.
- **Batch processing:** Parallel processing with `bulk()` for handling large datasets.
- **Gzip-backed data:** Reference data ships as `.json.gz` caches for fast loads; raw sources live under `src/humanmint/data/original/`.
- **Ethics:** Gender inference is probabilistic from historical name data and not a determination of identity; downstream use should respect that.

## API Reference

### Core Functions

#### `mint(name, email, phone, address, department, title, organization, ...)`

One function. All your data cleaned.

```python
from humanmint import mint

result = mint(
    name="Jane Doe",                    # optional
    email="jane@example.com",           # optional
    phone="(202) 555-0172",             # optional (use real area codes)
    address="123 Main St, City, ST ZIP", # optional
    department="Water Utilities",       # optional
    title="Chief of Water",             # optional
    organization="City of Springfield"  # optional
)

# Access cleaned data
result.name                 # dict: {full, first, last, middle, suffix, gender}
result.email                # str
result.phone                # str (E.164 format)
result.address              # dict: {street, city, state, zip}
result.department           # str (canonical)
result.department_category  # str
result.title                # dict: {raw, cleaned, canonical, is_valid, confidence}
result.organization         # dict: {raw, normalized, canonical, confidence}

# Convert to dict for JSON
result.model_dump()
```

#### `bulk(records, workers=4, progress=False)`

Process multiple records in parallel.

```python
from humanmint import bulk

records = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
]

results = bulk(records, workers=4, progress=True)
# Returns: list[MintResult]
```

#### `compare(result_a, result_b)`

Compare two normalized records and return similarity score (0-100).

```python
from humanmint import mint, compare

r1 = mint(name="John Smith", email="john@example.com")
r2 = mint(name="Jon Smith", email="john.smith@example.com")

similarity = compare(r1, r2)  # Returns float 0-100
```

### Names Module

Import: `from humanmint.names import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_name(raw)` | Parse and normalize a full name | Dict: {first, last, middle, suffix, full, canonical, is_valid} |
| `infer_gender(first_name, confidence=False)` | Infer gender from first name | Dict: {gender, confidence} or str |
| `enrich_name(normalized_dict, include_gender=True)` | Add gender/enrichment data to normalized name | Dict with enriched fields |
| `detect_nickname(first_name)` | Detect if a name is a nickname, return canonical form | Optional[str] |
| `get_nickname_variants(canonical_name)` | Get all known nicknames for a name | set[str] |
| `get_name_equivalents(name)` | Get all equivalent forms (nicknames + canonicals) | set[str] |
| `compare_first_names(name1, name2, use_nicknames=True)` | Compare two first names with fuzzy matching | float (0-1) |
| `compare_last_names(last1, last2)` | Compare two last names | float (0-1) |
| `match_names(raw1, raw2, strict=False)` | Full name matching with detailed scoring | Dict: {score, is_match, reasons, ...} |

**Examples:**

```python
from humanmint.names import normalize_name, infer_gender, detect_nickname

# Normalize
result = normalize_name("Dr. Jane Smith, PhD")
# {'first': 'Jane', 'last': 'Smith', 'full': 'Jane Smith', 'gender': None, ...}

# Infer gender
gender = infer_gender("Jane")  # {'gender': 'Female', 'confidence': 0.98}

# Detect nickname
canonical = detect_nickname("Bobby")  # 'Robert'
variants = get_name_equivalents("Robert")  # {'Robert', 'Bob', 'Bobby', 'Rob', ...}
```

### Emails Module

Import: `from humanmint.emails import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_email(raw, generic_inboxes=None)` | Normalize email and extract metadata | Dict: {email, local, domain, is_generic, is_free_provider, is_valid} |
| `is_free_provider(domain)` | Check if domain is a free email provider | bool |
| `guess_email(name, domain, known=[])` | Guess likely email pattern from known examples | str (email or empty) |
| `get_pattern_scores(known)` | Analyze known emails and return detected patterns | list[(pattern_id, confidence)] |
| `describe_pattern(pattern_id)` | Get documentation for an email pattern | Optional[Dict] |

**Examples:**

```python
from humanmint.emails import normalize_email, guess_email, is_free_provider

# Normalize
result = normalize_email("JOHN.SMITH@GMAIL.COM")
# {'email': 'john.smith@gmail.com', 'domain': 'gmail.com', 'is_free_provider': True, ...}

# Check if free
is_free = is_free_provider("gmail.com")  # True

# Guess email pattern
known = [("John Smith", "jsmith@company.com"), ("Jane Doe", "jdoe@company.com")]
guess = guess_email("Bob Jones", "company.com", known)  # 'bjones@company.com'
```

### Phones Module

Import: `from humanmint.phones import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_phone(raw, country="US")` | Normalize phone to E.164 format | Dict: {e164, pretty, extension, country, type, is_valid} |
| `detect_impossible(phone_dict)` | Detect if phone appears impossible/test/fake | bool |
| `detect_fax_pattern(phone_dict)` | Detect if phone matches known fax patterns | bool |
| `detect_voip_pattern(phone_dict)` | Detect if phone matches VoIP provider patterns | bool |

**Examples:**

```python
from humanmint.phones import normalize_phone, detect_fax_pattern

# Normalize
result = normalize_phone("(202) 555-0123 ext 201")
# {'e164': '+12025550123', 'pretty': '+1 202-555-0123', 'extension': '201', 'type': 'mobile', ...}

# Detect fax
fax = detect_fax_pattern(result)  # False
```

### Departments Module

Import: `from humanmint.departments import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_department(raw_dept)` | Normalize dept name (remove noise, standardize format) | str |
| `find_best_match(dept_name, threshold=0.6, normalize=True)` | Find best canonical match | Optional[str] |
| `find_all_matches(dept_name, threshold=0.6, top_n=3, normalize=True)` | Find all matches ranked by similarity | list[str] |
| `match_departments(dept_names, threshold=0.6, normalize=True)` | Match multiple depts at once | dict[str, Optional[str]] |
| `get_similarity_score(dept1, dept2)` | Calculate similarity between two depts | float (0-1) |
| `get_department_category(dept)` | Get category for canonical dept | Optional[str] |
| `get_all_categories()` | Get all available categories | set[str] |
| `get_departments_by_category(category)` | Get depts in a specific category | list[str] |
| `categorize_departments(depts)` | Categorize multiple depts | dict[str, Optional[str]] |
| `get_canonical_departments()` | Get all canonical dept names | list[str] |
| `is_canonical(dept)` | Check if dept is canonical | bool |
| `load_mappings()` | Load all dept mappings | dict[str, list[str]] |
| `get_mapping_for_original(original)` | Get canonical for original name | Optional[str] |
| `get_originals_for_canonical(canonical)` | Get all original names for canonical | list[str] |

**Examples:**

```python
from humanmint.departments import normalize_department, find_best_match, get_department_category

# Normalize
clean = normalize_department("000171 - Police Department")  # 'Police'

# Find match
match = find_best_match("Police Dept")  # 'Police'
category = get_department_category("Police")  # 'Public Safety'

# Find all matches
all_matches = find_all_matches("Finance", threshold=0.7)  # ['Finance', 'Budget']
```

### Titles Module

Import: `from humanmint.titles import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_title_full(raw_title, threshold=0.6, dept_canonical=None, overrides=None)` | Full normalization with confidence | TitleResult Dict: {raw, cleaned, canonical, is_valid, confidence} |
| `normalize_title(raw_title)` | Core title cleaning | str |
| `find_best_match(title, threshold=0.6, normalize=True)` | Find best canonical match | tuple[Optional[str], float] |
| `find_all_matches(title, threshold=0.6, top_n=3)` | Find all matches | list[str] |
| `get_similarity_score(title1, title2)` | Calculate similarity | float (0-1) |
| `get_canonical_titles()` | Get all canonical titles | list[str] |
| `is_canonical(title)` | Check if title is canonical | bool |
| `get_mapping_for_variant(variant)` | Get canonical for variant | Optional[str] |
| `get_all_mappings()` | Get all title mappings | dict[str, str] |

**Examples:**

```python
from humanmint.titles import normalize_title_full, find_best_match, get_canonical_titles

# Full normalization
result = normalize_title_full("0001 - Chief of Police (Downtown)")
# {'raw': '0001 - Chief of Police (Downtown)', 'cleaned': 'Chief of Police', 'canonical': 'police chief', ...}

# Find match with confidence
title, confidence = find_best_match("Police Chief", threshold=0.7)
# ('police chief', 0.95)
```

### Addresses Module

Import: `from humanmint.addresses import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_address(raw)` | Parse US postal address | Optional[Dict]: {street, city, state, zip, canonical} |

**Examples:**

```python
from humanmint.addresses import normalize_address

result = normalize_address("123 Main St, Springfield, IL 62701")
# {'street': '123 Main St', 'city': 'Springfield', 'state': 'IL', 'zip': '62701', ...}
```

### Organizations Module

Import: `from humanmint.organizations import ...`

| Function | Purpose | Returns |
|----------|---------|---------|
| `normalize_organization(raw)` | Normalize agency/org name (remove civic suffixes) | Optional[Dict]: {raw, normalized, canonical, confidence} |

**Examples:**

```python
from humanmint.organizations import normalize_organization

result = normalize_organization("City of Springfield")
# {'raw': 'City of Springfield', 'normalized': 'Springfield', 'canonical': 'Springfield', ...}
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
    phone="(202) 555-0178",  # Real area code; 555 is reserved
    department="000171 - Police",
    title="Chief of Police"
)

# Cleaned:
# name: {'full': 'Robert Patterson', 'first': 'Robert', 'last': 'Patterson', 'gender': 'Male'}
# email: 'robert.patterson@police.gov'
# phone: '+1 202-555-0178'
# department: 'Police' (category: 'Public Safety')
# title: {'canonical': 'police chief', 'is_valid': True}
```

### Messy Data
```python
result = mint(
    name="Dr. Jane Smith, PhD",
    email="JANE@EXAMPLE.COM",
    phone="415 555 0123",  # Real area code; 555 is reserved
    department="Planning and Development 415-555-0123 ext 200"
)

# Cleaned:
# name: {'full': 'Jane Smith', 'first': 'Jane', 'last': 'Smith', 'gender': 'Female'}
# email: 'jane@example.com'
# phone: '+1 415-555-0123'
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

Use individual modules for specific needs. See **API Reference** above for the complete list of functions across all modules:

```python
# Names: normalize, enrich, infer gender, detect nicknames
from humanmint.names import normalize_name, infer_gender, detect_nickname

# Emails: validate, detect free providers, guess patterns
from humanmint.emails import normalize_email, is_free_provider, guess_email

# Phones: normalize, detect types, identify fax/VoIP/test numbers
from humanmint.phones import normalize_phone, detect_fax_pattern, detect_voip_pattern

# Departments: normalize, match, categorize
from humanmint.departments import normalize_department, find_best_match, get_department_category

# Titles: normalize, match, get mappings
from humanmint.titles import normalize_title_full, find_best_match as match_title

# Addresses: parse and normalize
from humanmint.addresses import normalize_address

# Organizations: normalize and extract canonical names
from humanmint.organizations import normalize_organization

# Batch processing and comparison
from humanmint import bulk, compare
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
| `phone="(202) 555-0101 x101"` | `+1 202-555-0101`, extension: `101` |
| `address="123 Main St, Springfield, IL 62701"` | `street='123 Main St', city='Springfield', state='IL', zip='62701'` |
| `department="000171 - Public Works 202-555-0150 ext 200"` | `Public Works` (category: Infrastructure) |
| `title="0001 - Chief of Police (Downtown)"` | `police chief` |
| `organization="City of Springfield Police"` | `normalized='Springfield', canonical='Springfield'` |
| `name="Jo"` | `first='Jo'`, gender: Female |

## Version

0.1.0

## License

MIT
