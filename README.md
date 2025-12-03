# HumanMint v2

HumanMint cleans and normalizes messy contact data with one call. It standardizes names, emails, phones, addresses, departments, titles, and organizations. It's built for both public-sector data and B2B (CEOs, VPs, directors, managers) and ships with curated public-sector mappings.

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
```

Multi-person splitting:
```python
mint(name="John and Jane Smith", split_multi=True)
# -> [MintResult(John Smith), MintResult(Jane Smith)]
```

## Why HumanMint
- General-purpose: works for government and B2B without swapping libraries.
- Real-world chaos: handles titles inside names, departments with codes/phones, smashed addresses, anti-scraper emails, casing quirks.
- Unique data: 23K+ department variants -> 64 categories; 73K+ titles with curated canonicals + BLS; context-aware title mapping.
- Safe defaults: length guards, optional aggressive cleaning, semantic conflict checks, bulk dedupe, multi-person name splitting.
- Fast: lazy imports for quick startup, process-based bulk for CPU-bound speed, built-in dedupe to avoid redundant work.

## AI extraction (optional)
Install the ML extra (`pip install humanmint[ml]`) and pass `text=` with `use_gliner=True` to extract from unstructured text, then normalize. Structured fields you pass always win. GLiNER extraction is experimental; prefer structured inputs when available.

```python
from humanmint.gliner import GlinerConfig
result = mint(text=signature_block, use_gliner=True, gliner_cfg=GlinerConfig(threshold=0.85))
```

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

score, why = compare(r1, r2, explain=True)

records = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob",   "email": "bob@example.com"},
]
results = bulk(records, workers=4)
```

## Access Patterns
- Dicts: `result.title["canonical"]`, `result.department["canonical"]`, `result.department["category"]`
- Properties: `name_standardized`, `title_canonical`, `department_canonical`, `email_standardized`, `phone_standardized`, `address_canonical`, `organization_canonical`
- Full dicts: `result.title`, `result.department`, `result.email`, etc.

## Recommended Properties
- Names: `name_standardized`, `name_first`, `name_last`, `name_middle`, `name_suffix`, `name_gender`, `name_nickname`
- Name extras: `name_salutation` (Mr./Ms./Mx.)
- Emails: `email_standardized`, `email_domain`, `email_is_valid`, `email_is_generic_inbox`, `email_is_free_provider`
- Phones: `phone_standardized`, `phone_e164`, `phone_pretty`, `phone_extension`, `phone_is_valid`, `phone_type`, `phone_location`, `phone_time_zones`
- Departments: `department_canonical`, `department_category`, `department_normalized`, `department_override`
- Titles: `title_canonical`, `title_raw`, `title_normalized`, `title_is_valid`, `title_confidence`, `title_seniority`
- Addresses: `address_canonical`, `address_raw`, `address_street`, `address_unit`, `address_city`, `address_state`, `address_zip`, `address_country`
- Organizations: `organization_raw`, `organization_normalized`, `organization_canonical`, `organization_confidence`

Use `result.get("email.is_valid")` to fetch nested dict values via dot paths.

## Comparing Records
```python
from humanmint import compare
score, reasons = compare(r1, r2, explain=True)  # 0->100
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

## Performance (current)
- Cold import: ~0.5 s (with pandas installed).
- First call warm-up: ~0.5 s (loads caches).
- Bulk: process-based parallelism; throughput scales with cores and workload size.

## Notes
- US-focused address parsing; `usaddress` used when available, otherwise heuristics.
- Optional deps (pandas, pyarrow, sqlalchemy, rich, tqdm) enhance exports and progress bars.
- Department and title datasets are curated and updated regularly for best accuracy.

