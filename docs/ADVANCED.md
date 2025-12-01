# Advanced Usage

This guide covers advanced features and customization options in HumanMint.

## Table of Contents

- [Custom Comparison Weights](#custom-comparison-weights)
- [Department & Title Overrides](#department--title-overrides)
- [Batch Processing & Export](#batch-processing--export)
- [Pandas Integration](#pandas-integration)
- [Performance Optimization](#performance-optimization)

## Custom Comparison Weights

The `compare()` function uses weighted scoring to determine similarity between two records. You can customize these weights to prioritize certain fields over others.

### Default Weights

```python
from humanmint import compare

# Default weights:
# - name: 40%
# - email: 30%
# - phone: 20%
# - department: 5%
# - title: 5%

score = compare(result1, result2)
```

### Custom Weights

```python
from humanmint import compare

# Emphasize email matching over name
custom_weights = {
    "name": 0.25,      # 25%
    "email": 0.50,     # 50%
    "phone": 0.15,     # 15%
    "department": 0.05,
    "title": 0.05,
}

score = compare(result1, result2, weights=custom_weights)
```

### Weight Scenarios

**Email-focused (data deduplication):**
```python
weights = {
    "name": 0.20,
    "email": 0.60,  # Email is most reliable
    "phone": 0.15,
    "department": 0.025,
    "title": 0.025,
}
```

**Name-focused (fuzzy matching):**
```python
weights = {
    "name": 0.70,   # Prioritize name similarity
    "email": 0.15,
    "phone": 0.10,
    "department": 0.025,
    "title": 0.025,
}
```

**Disable specific fields:**
```python
# Ignore department and title entirely
weights = {
    "name": 0.50,
    "email": 0.35,
    "phone": 0.15,
    "department": 0.0,  # Disabled
    "title": 0.0,       # Disabled
}
```

## Department & Title Overrides

Override the canonical mappings for departments and titles to match your organization's terminology.

### Department Overrides

```python
from humanmint import mint

dept_overrides = {
    "IT Department": "Information Technology",
    "Public Works": "DPW",
    "HR": "Human Resources",
}

result = mint(
    department="IT Department",
    dept_overrides=dept_overrides
)

print(result.department_canonical)  # "Information Technology"
```

### Title Overrides

```python
from humanmint import mint

title_overrides = {
    "City Manager": "chief executive officer",
    "Assistant Director": "assistant manager",
}

result = mint(
    title="City Manager",
    title_overrides=title_overrides
)

print(result.title_canonical)  # "chief executive officer"
```

### Batch Overrides

Apply overrides to all records in a batch:

```python
from humanmint import bulk

records = [
    {"name": "John Doe", "department": "IT Dept", "title": "City Manager"},
    {"name": "Jane Smith", "department": "Public Works", "title": "Assistant Director"},
]

dept_overrides = {"IT Dept": "Information Technology"}
title_overrides = {"City Manager": "chief executive officer"}

results = bulk(
    records,
    dept_overrides=dept_overrides,
    title_overrides=title_overrides
)
```

## Batch Processing & Export

Process large datasets efficiently and export to various formats.

### Bulk Processing

```python
from humanmint import bulk

# Basic bulk processing
records = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    # ... thousands more
]

results = bulk(records, workers=4)
```

### Progress Tracking

```python
# Simple progress bar
results = bulk(records, workers=4, progress=True)

# Rich progress bar (requires 'rich' package)
results = bulk(records, workers=4, progress="rich")

# Custom progress callback
def my_progress():
    print(".", end="", flush=True)

results = bulk(records, workers=4, progress=my_progress)
```

### Export to JSON

```python
from humanmint import bulk, export_json

results = bulk(records)

# Nested format (default)
export_json(results, "output.json")

# Flattened format (for databases)
export_json(results, "output.json", flatten=True)
```

### Export to CSV

```python
from humanmint import bulk, export_csv

results = bulk(records)

# Flattened format
export_csv(results, "output.csv", flatten=True)

# Nested format
export_csv(results, "output.csv", flatten=False)
```

### Export to Parquet

```python
from humanmint import bulk, export_parquet

results = bulk(records)

# Requires pandas and pyarrow
# pip install humanmint[pandas] pyarrow
export_parquet(results, "output.parquet", flatten=True)
```

### Export to SQL

```python
from humanmint import bulk, export_sql

results = bulk(records)

# SQLite
export_sql(
    results,
    "contacts.db",
    table="cleaned_contacts",
    flatten=True,
    mode="replace"  # or "append"
)

# PostgreSQL (requires psycopg2)
export_sql(
    results,
    "postgresql://user:pass@localhost/db",
    table="contacts",
    flatten=True
)
```

## Pandas Integration

HumanMint provides a pandas accessor for DataFrame operations.

### Basic Usage

```python
import pandas as pd
import humanmint

df = pd.DataFrame({
    "name": ["Dr. John Smith", "Jane Doe, PhD"],
    "email": ["JOHN@EXAMPLE.COM", "jane@example.com"],
    "phone": ["(202) 555-0123", "202-555-0124"],
    "department": ["001 - IT", "HR Department"],
    "title": ["Chief of IT", "HR Manager"],
})

# Clean entire DataFrame
cleaned = df.humanmint.clean()

# Access cleaned columns
print(cleaned[["hm_name_first", "hm_name_last", "hm_email"]])
```

### Explicit Column Mapping

```python
# Specify exact column names
cleaned = df.humanmint.clean(
    name_col="full_name",
    email_col="contact_email",
    phone_col="phone_number",
    dept_col="dept",
    title_col="job_title"
)
```

### Bulk Mode

```python
# Use parallel processing for large DataFrames
cleaned = df.humanmint.clean(
    use_bulk=True,
    workers=8,
    progress=True
)
```

### Available Columns

After cleaning, these columns are added (prefixed with `hm_`):

**Names:**
- `hm_name_full`
- `hm_name_first`
- `hm_name_last`
- `hm_name_gender`

**Emails:**
- `hm_email`
- `hm_email_domain`
- `hm_email_is_generic`
- `hm_email_is_free_provider`

**Phones:**
- `hm_phone`

**Addresses:**
- `hm_address_canonical`
- `hm_address_city`
- `hm_address_state`
- `hm_address_zip`

**Departments:**
- `hm_department`
- `hm_department_category`

**Titles:**
- `hm_title_canonical`
- `hm_title_is_valid`

**Organizations:**
- `hm_organization`

## Performance Optimization

### Choosing Worker Count

```python
import os
from humanmint import bulk

# Use CPU count
workers = os.cpu_count()

# Conservative (good for I/O-bound tasks)
workers = os.cpu_count() // 2

# Aggressive (good for CPU-bound tasks)
workers = os.cpu_count() * 2

results = bulk(records, workers=workers)
```

### Memory Management

For very large datasets, process in chunks:

```python
def process_in_chunks(records, chunk_size=10000):
    all_results = []
    
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        results = bulk(chunk, workers=4)
        all_results.extend(results)
    
    return all_results

results = process_in_chunks(large_dataset)
```

### Pandas Chunking

```python
import pandas as pd

chunk_size = 10000
results = []

for chunk in pd.read_csv("large_file.csv", chunksize=chunk_size):
    cleaned = chunk.humanmint.clean(use_bulk=True, workers=4)
    results.append(cleaned)

final_df = pd.concat(results, ignore_index=True)
```

### Aggressive Text Cleaning

Enable aggressive cleaning for extremely messy data:

```python
from humanmint import mint

result = mint(
    name="<script>alert('John')</script> Doe!!!",
    aggressive_clean=True
)
```

## Tips & Best Practices

### 1. Use Bulk for Large Datasets

```python
# ❌ Slow for large datasets
results = [mint(**record) for record in records]

# ✅ Fast parallel processing
results = bulk(records, workers=4)
```

### 2. Flatten for Database Export

```python
# ✅ Easy to import into SQL
export_csv(results, "output.csv", flatten=True)
export_sql(results, "db.sqlite", table="contacts", flatten=True)
```

### 3. Cache Override Dictionaries

```python
# Define once, reuse many times
DEPT_OVERRIDES = {
    "IT": "Information Technology",
    "HR": "Human Resources",
}

# Use across multiple operations
for batch in large_dataset_batches:
    results = bulk(batch, dept_overrides=DEPT_OVERRIDES)
```

### 4. Validate Results

```python
# Check confidence scores
low_confidence = [
    r for r in results 
    if r.title and r.title.get("confidence", 0) < 0.7
]

# Review invalid titles
invalid_titles = [
    r for r in results
    if r.title and not r.title.get("is_valid", True)
]
```

### 5. Combine with Data Validation

```python
from humanmint import mint

def validate_and_clean(record):
    result = mint(**record)
    
    # Add custom validation
    if result.email_valid and result.phone_valid:
        return result
    else:
        return None  # Skip invalid records

valid_results = [
    r for r in [validate_and_clean(rec) for rec in records]
    if r is not None
]
```

## See Also

- [API Reference](https://github.com/RicardoNunes2000/HumanMint#api-reference)
- [Fields Guide](FIELDS.md)
- [Use Cases](use_cases/)
