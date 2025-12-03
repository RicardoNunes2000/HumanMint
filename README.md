# HumanMint v2

HumanMint cleans and normalizes messy contact data with one line of code. It standardizes names, emails, phones, addresses, departments, titles, and organizations. It is a general-purpose cleaner for B2B and public-sector data, and ships with curated public-sector mappings you won’t find anywhere else.

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
- General-purpose: works for government data and B2B (execs, VPs, directors, managers) without switching libraries.
- Real-world chaos: titles inside names, departments with numbers/phone extensions, strange-casing emails, smashed-together addresses.
- Unique data: 23K+ department variants → 64 categories; 73K+ titles with curated canonicals + BLS; context-aware (dept-informed) title mapping not available off-the-shelf.
- Safe defaults: length guards, optional aggressive cleaning, semantic conflict checks, bulk dedupe, and optional multi-person name splitting.

### Department & Title mapping you can’t get elsewhere
Curated public-sector mappings that solve the “impossible to Google” parts of contact normalization. Works for governments and B2B roles (CEOs, VPs, Directors, Managers) alike.
```
"City Administration"    -> "Administration"       [administration]
"Finance Department"     -> "Finance"              [finance]
"Public Works"           -> "Public Works"         [infrastructure]
"Police Department"      -> "Police"               [public safety]
```
Titles get similar treatment across 73K standardized forms with optional department context to boost accuracy.

### All fields in one library
Names, emails, phones, addresses, departments, titles, organizations—one pipeline. Most libraries clean only one field (just names or just phones); HumanMint normalizes the entire record with canonicalization, categorization, and confidence.

### Fast
Typical workloads run sub-millisecond per record with multithreading and built-in dedupe.

### AI extraction (optional)
Install the ML extra (`pip install humanmint[ml]`) and pass `text=` with `use_gliner=True` to extract from unstructured text, then normalize. Structured fields you pass always win. You can also pass a `GlinerConfig` (`gliner_cfg`) to control schema, threshold, and GPU usage.
GLiNER extraction is experimental and may be inaccurate; prefer structured inputs when available.

Example (signature block → canonicalized):
```
text = """
John A. Miller
Deputy Director of Public Works
City of Springfield, Missouri
305 E McDaniel St, Springfield, MO 65806
Phone: (417) 864-1234
Email: jmiller@springfieldmo.gov
"""

result = mint(text=text, use_gliner=True)

# Result:
# MintResult(
#   name: John A Miller
#   email: jmiller@springfieldmo.gov
#   phone: +1 417-864-1234
#   department: Public Works
#   title:
#     raw: Deputy Director
#     normalized: Deputy Director
#     canonical: deputy director
#   address: None
#   organization: Springfield Missouri
# )
```
You can also batch texts: `mint(texts=[...], use_gliner=True)` returns a list of `MintResult` objects.

Advanced GLiNER configuration:
```python
from humanmint.gliner import GlinerConfig

cfg = GlinerConfig(
    threshold=0.85,    # optional confidence threshold
    use_gpu=True,      # move model to GPU if available
    schema=None,       # custom schema dict if desired
    extractor=None,    # reuse a preloaded GLiNER2 instance
)

result = mint(text=text, use_gliner=True, gliner_cfg=cfg)
```

## What’s new in v2 (vs v1)
- Clear, canonical property names: `name_standardized`, `email_standardized`, `phone_standardized`, `title_canonical`, `department_canonical` (legacy aliases removed).
- Explainable comparisons: `compare(..., explain=True)` shows component scores/penalties.
- Multi-person name splitting: `split_multi=True` handles “John and Jane Smith”.
- Name enrichment: detects nicknames and generational suffixes without polluting the main name fields.
- Optional GLiNER extraction for unstructured text via `use_gliner=True` and `GlinerConfig`; multi-person GLiNER input raises a clear error.
- Structured-field pipeline remains deterministic and fast; GLiNER is opt-in and experimental.

## Installation
```bash
pip install humanmint
# Optional extras:
#   pip install humanmint[address]  # usaddress parsing
#   pip install humanmint[pandas]   # DataFrame helpers
#   pip install humanmint[ml]       # GLiNER2 extraction
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
Quick reference (full field guide in `docs/FIELDS.md`):
- Dict access: `result.title["canonical"]`, `result.department["canonical"]`, `result.department["category"]`
- Properties (preferred): `name_standardized`, `title_canonical`, `department_canonical`, `email_standardized`, `phone_standardized`, `address_canonical`, `organization_canonical`
- Full dicts: `result.title`, `result.department`, `result.email`, etc.

## Recommended Properties (quick reference)

**Names** — `name_standardized`, `name_first`, `name_last`, `name_middle`, `name_suffix`, `name_suffix_type`, `name_gender`, `name_nickname`

**Emails** — `email_standardized`, `email_domain`, `email_is_valid`, `email_is_generic_inbox`, `email_is_free_provider`

**Phones** — `phone_standardized`, `phone_e164`, `phone_pretty`, `phone_extension`, `phone_is_valid`, `phone_type`

**Departments** — `department_canonical`, `department_category`, `department_normalized`, `department_override`

**Titles** — `title_canonical`, `title_raw`, `title_normalized`, `title_is_valid`, `title_confidence`, `title_seniority`

**Addresses** — `address_canonical`, `address_raw`, `address_street`, `address_unit`, `address_city`, `address_state`, `address_zip`, `address_country`

**Organizations** — `organization_raw`, `organization_normalized`, `organization_canonical`, `organization_confidence`

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
