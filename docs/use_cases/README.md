# Use Cases

Real-world examples of cleaning and normalizing contact data.

## Government Contacts

Managing employee records with ranks, department codes, and varying formats.

- Cleaning rank prefixes: `"Chief John Smith"` → `"John Smith"`
- Removing department codes
- Batch processing with deduplication
- Export to database

[Read: Government Contact Management](GOVERNMENT_CONTACTS.md)

## HR & Salesforce Data

Normalizing employee directories and CRM exports.

- Deduplicating Salesforce leads
- Building clean HR directory
- Finding matching records
- Merging multiple data sources

[Read: HR & Salesforce Data Cleaning](HR_SALESFORCE.md)

## Common Patterns

### Single Record

```python
from humanmint import mint

result = mint(
    name="Dr. John Smith, PhD",
    email="JOHN.SMITH@CITY.GOV",
    phone="(202) 555-0123",
    department="001 - Public Works",
    title="Chief of Police"
)

print(result.name_standardized)          # "John Smith"
print(result.title_canonical)         # "police chief"
print(result.phone_standardized)         # "+1 202-555-0123"
```

### Batch Processing

```python
from humanmint import bulk

records = load_csv("export.csv")
results = bulk(records, workers=4, progress=True)
```

### Finding Duplicates

```python
from humanmint import compare

score = compare(result_a, result_b)  # Returns 0-100
if score > 85:
    print(f"Likely duplicate (score: {score:.0f})")
elif score > 70:
    print(f"Similar records (score: {score:.0f})")
```

### Exporting Results

```python
from humanmint import export_csv, export_sql

# CSV (recommended for analysis)
export_csv(results, "cleaned.csv", flatten=True)

# Database
export_sql(results, engine, "contacts", flatten=True)
```
