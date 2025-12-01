# Use Case: Government Contact Management

Managing government employee contacts requires handling messy data with names, ranks, and varying formats.

## Problem

Government databases often contain:
- Rank prefixes: `"Chief John Smith"`, `"Lt. Sarah O'Connor"`
- Department codes: `"001 - Police Department"`
- Multiple phone formats: `"(202) 555-0123 ext 456"`
- Inconsistent capitalization: `"JOHN.SMITH@CITY.GOV"`

## Solution

```python
from humanmint import mint, bulk, compare

# Single record
result = mint(
    name="Chief Robert Patterson",
    email="robert.patterson@police.gov",
    phone="(202) 555-0178",
    department="000171 - Police",
    title="Chief of Police"
)

print(result.name_standardized)          # "Robert Patterson" (rank stripped)
print(result.department_canonical)    # "Police" (code removed)
print(result.title_canonical)         # "police chief"
print(result.phone_standardized)         # "+1 202-555-0178"
```

## Batch Processing with Deduplication

```python
from humanmint import bulk, compare

# Import from CSV
records = [
    {
        "name": "Chief John Smith",
        "email": "JOHN.SMITH@POLICE.GOV",
        "phone": "(202) 555-0101",
        "department": "000171 - Police",
        "title": "Chief of Police"
    },
    {
        "name": "John Smith Jr.",
        "email": "john.smith.jr@police.gov",
        "phone": "202-555-0102",
        "department": "Police",
        "title": "Captain"
    },
]

# Clean all records in parallel
results = bulk(records, workers=4, progress=True)

# Find duplicates
for i, r1 in enumerate(results):
    for r2 in results[i+1:]:
        score = compare(r1, r2)
        if score > 80:  # >80 = high similarity, likely duplicate
            print(f"Potential duplicate: {r1.name_standardized} vs {r2.name_standardized} (score: {score:.0f})")
```

## Export to Database

```python
from humanmint import bulk, export_sql
from sqlalchemy import create_engine

# Clean records
results = bulk(records, workers=4)

# Export to database
engine = create_engine("postgresql://user:pass@localhost/government_db")
export_sql(results, engine, "employees", flatten=True)

# Creates columns:
# name_first, name_last, email_normalized, phone_e164,
# department_canonical, title_canonical, etc.
```

## Accessing Detailed Fields

```python
result = mint(
    title="Chief of Police",
    department="001 - Police Department"
)

# Raw and normalized stages
print(result.title["raw"])        # "Chief of Police"
print(result.title["normalized"]) # "Chief Of Police"
print(result.title["canonical"])  # "police chief"

# Check validity and confidence
if result.title["is_valid"]:
    print(f"Valid title with {result.title['confidence']:.0%} confidence")
```

## Custom Department Mapping

Map your agency names to preferred canonicals:

```python
result = mint(
    department="Public Works Division",
    dept_overrides={"public works": "Infrastructure Services"}
)

print(result.department_canonical)  # "Infrastructure Services"
```
