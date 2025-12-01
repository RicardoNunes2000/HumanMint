# HumanMint v2

HumanMint cleans and normalizes messy contact data with one line of code. It standardizes names, emails, phones, addresses, departments, titles, and organizations using curated public-sector mappings you won’t find anywhere else.

```python
from humanmint import mint

result = mint(
    name="Dr. John Q. Smith, PhD",
    email="JOHN.SMITH@CITY.GOV",
    phone="(202) 555-0173 ext 456",
    department="001 - Public Works Dept",
    title="Chief of Police",
    address="123 N. Main St Apt 4B, Madison, WI 53703",
    organization="City of Madison Police Department",
)

result.name_standardized          # "John Q Smith"
result.email_standardized         # "john.smith@city.gov"
result.phone_pretty               # "+1 202-555-0173"
result.department_canonical       # "Public Works"
result.title_canonical            # "police chief"
result.address_canonical          # "123 N. Main St Apt 4B Madison WI 53703 US"

# Split multi-person names when needed
results = mint(name="John and Jane Smith", split_multi=True)
# returns [MintResult(John Smith), MintResult(Jane Smith)]
```

## Why HumanMint
- Real-world chaos: titles inside names, departments with numbers/phone extensions, strange-casing emails, smashed-together addresses.
- Unique data: 23K+ department variants → 64 categories; 73K+ titles with curated canonicals + BLS; context-aware (dept-informed) title mapping not available off-the-shelf.
- Safe defaults: length guards, optional aggressive cleaning, semantic conflict checks, bulk dedupe, and optional multi-person name splitting.

### Department & Title mapping you can’t get elsewhere
Curated public-sector mappings that solve the “impossible to Google” parts of contact normalization.
```
"City Administration"    -> "Administration"       [administration]
"Finance Department"     -> "Finance"              [finance]
"Public Works"           -> "Public Works"         [infrastructure]
"Police Department"      -> "Police"               [public safety]
```
Titles get similar treatment across 73K standardized forms with optional department context to boost accuracy.

### All fields in one library
Names, emails, phones, addresses, departments, titles, organizations—one pipeline. Most libraries cover one field; HumanMint returns the whole record with canonicalization, categorization, and confidence.

### Fast
Typical workloads run sub-millisecond per record with multithreading and built-in dedupe.

## Installation
```bash
pip install humanmint
```

## Quickstart
```python
from humanmint import mint, compare, bulk

r1 = mint(name="Jane Doe", email="jane.doe@city.gov", department="Public Works", title="Engineer")
r2 = mint(name="J. Doe",  email="JANE.DOE@CITY.GOV", department="PW Dept",       title="Public Works Engineer")

score = compare(r1, r2)  # similarity 0–100
# Or with explanation:
score, why = compare(r1, r2, explain=True)
print("\n".join(why))

records = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob",   "email": "bob@example.com"},
]
results = bulk(records, workers=4)
```

## Access Patterns
- Dict access: `result.title["canonical"]`, `result.department["canonical"]`, `result.department["category"]`
- Properties (preferred): `name_standardized`, `title_canonical`, `department_canonical`, `email_standardized`, `phone_standardized`, `address_canonical`, `organization_canonical`
- Full dicts: `result.title`, `result.department`, `result.email`, etc.

## Recommended Properties

**Names**
- `name_standardized`, `name_first`, `name_last`, `name_middle`, `name_suffix`, `name_suffix_type`, `name_gender`, `name_nickname`

**Emails**
- `email_standardized`, `email_domain`, `email_is_valid`, `email_is_generic_inbox`, `email_is_free_provider`

**Phones**
- `phone_standardized`, `phone_e164`, `phone_pretty`, `phone_extension`, `phone_is_valid`, `phone_type`

**Departments**
- `department_canonical`, `department_category`, `department_normalized`, `department_override`

**Titles**
- `title_canonical`, `title_raw`, `title_normalized`, `title_is_valid`, `title_confidence`, `title_seniority`

**Addresses**
- `address_canonical`, `address_raw`, `address_street`, `address_unit`, `address_city`, `address_state`, `address_zip`, `address_country`

**Organizations**
- `organization_raw`, `organization_normalized`, `organization_canonical`, `organization_confidence`

Use `result.get("email.is_valid")` or other dot paths to fetch nested dict values.

## Comparing Records
```python
from humanmint import compare
score = compare(r1, r2)  # 0–100
# >85 likely duplicate, >70 similar, <50 different
```

## Batch & Export
```python
from humanmint import bulk, export_json, export_csv, export_parquet, export_sql

results = bulk(records, workers=4, progress=True)
export_json(results, "out.json")
export_csv(results, "out.csv", flatten=True)
```

## CLI
```bash
humanmint clean input.csv output.csv --name-col name --email-col email --phone-col phone --dept-col department --title-col title
```

## Performance (benchmark)
| Dataset | Time | Per Record | Throughput |
|---------|------|-----------|------------|
| 1,000   | 561 ms | 0.56 ms | 1,783 rec/sec |
| 10,000  | 3.1 s  | 0.31 ms | 3,178 rec/sec |
| 50,000  | 14.0 s | 0.28 ms | 3,576 rec/sec |

## Notes
- US-focused address parsing; `usaddress` is used when available, otherwise heuristics.
- Optional deps (pandas, pyarrow, sqlalchemy, rich, tqdm) enhance exports and progress bars.
- Department and title datasets are curated and updated regularly for best accuracy.
