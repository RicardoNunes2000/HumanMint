# HumanMint

**Clean, normalized contact data in one line of code.**

Standardize names, emails, phones, addresses, departments, job titles, and organizations with intelligent parsing and fuzzy matching.

```python
from humanmint import mint

result = mint(
    name="Dr. John Q. Smith, PhD",
    email="JOHN.SMITH@CITY.GOV",
    phone="(202) 555-0173 ext 456",
    department="001 - Public Works Dept",
    title="Chief of Police"
)

print(result.name_str)          # "John Q Smith"
print(result.email_str)         # "john.smith@city.gov"
print(result.phone_str)         # "+1 202-555-0173"
print(result.department_str)    # "Public Works"
print(result.title_str)         # "police chief"
```

## Why HumanMint?

Real-world contact data is **messy**:
- Names with titles: `"Dr. Jane Smith, PhD"`
- Inconsistent formatting: `"JOHN@EXAMPLE.COM"` vs `"john.smith@example.com"`
- Phone number variations: `"(202) 555-0101 x101"` vs `"202.555.0101"`
- Departments with noise: `"000171 - Public Works 202-555-0150 ext 200"`
- Abbreviated titles: `"Sr. Water Engr."`

**HumanMint handles all of this** with zero configuration.

## Installation

```bash
pip install humanmint
```

## Key Features

- **Names:** Parse, normalize, infer gender, detect nicknames, strip titles
- **Emails:** Validate, normalize, detect free providers (Gmail, Yahoo, etc.)
- **Phones:** Format (E.164), extract extensions, validate, detect type (mobile/landline)
- **Departments:** Canonicalize, categorize, fuzzy match (23K+ dept names → 64 categories)
- **Titles:** Standardize, match against curated list (100K+ job titles), confidence scores
- **Addresses:** Parse US postal addresses (street, city, state, ZIP)
- **Organizations:** Normalize agency/org names
- **Comparison:** `compare(result_a, result_b)` for deduplication with 0-100 similarity scores
- **Batch:** Parallel processing with `bulk(records, workers=4)` for high throughput
- **Export:** JSON, CSV, Parquet, SQL with flatten option for direct database import

## Quick Examples

### Field Accessor Reference

All fields provide three access patterns:

| Pattern | Example | Description |
|---------|---------|-------------|
| Dict access | `result.title["canonical"]` | Access specific processing stages |
| Property | `result.title_str` | Shorthand for canonical/standardized form |
| Full dict | `result.title` | All stages: raw, normalized, canonical, is_valid |

Common `_str` properties: `name_str`, `email_str`, `phone_str`, `department_str`, `title_str`

### Accessing title fields

```python
result = mint(title="Chief of Police")

# Dict access - different processing stages
result.title["raw"]         # "Chief of Police" (original input)
result.title["normalized"]  # "Chief of Police" (cleaned)
result.title["canonical"]   # "police chief" (standardized form)
result.title["is_valid"]    # True

# Shorthand properties
result.title_str            # "police chief" (same as canonical)
result.title_normalized     # "Chief of Police"
```

### Comparing records

```python
from humanmint import compare

r1 = mint(name="John Smith", email="john@example.com")
r2 = mint(name="Jon Smith", email="john.smith@example.com")

score = compare(r1, r2)  # Returns 0-100 similarity score
# Typically: >85 = likely duplicate, >70 = similar, <50 = different
```

### Batch processing

```python
from humanmint import bulk

records = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
]

results = bulk(records, workers=4, progress=True)
```

## Performance

| Dataset | Time | Per Record | Throughput |
|---------|------|-----------|-----------|
| 1,000 | 561 ms | 0.56 ms | 1,783 rec/sec |
| 10,000 | 3.1 s | 0.31 ms | 3,178 rec/sec |
| 50,000 | 14.0 s | 0.28 ms | 3,576 rec/sec |

## Documentation

- **[API Reference](docs/API.md)** — Full function documentation
- **[Use Cases](docs/use_cases/)** — Real-world examples (Government contacts, HR, Salesforce, etc.)
- **[Fields Guide](docs/FIELDS.md)** — Access all returned fields
- **[Advanced](docs/ADVANCED.md)** — Custom weights, overrides, batch export

## CLI

```bash
humanmint clean input.csv output.csv --name-col name --email-col email
```

## Testing

```bash
pytest -q unittests
```

## License

MIT
