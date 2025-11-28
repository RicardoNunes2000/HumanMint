# Use Case: HR & Salesforce Data Cleaning

Normalize employee and lead databases from HR systems and Salesforce exports.

## Problem

HR and CRM data is often:
- Inconsistent across imports (Excel, Salesforce, ADP)
- Has duplicate records with slight variations
- Contains department/title abbreviations
- Missing normalized email domains or phone formats

## Example: Deduplicating Salesforce Leads

```python
from humanmint import mint, compare, bulk

# Raw Salesforce export
salesforce_leads = [
    {
        "name": "Jane Doe",
        "email": "JANE@EXAMPLE.COM",
        "phone": "415-555-0123",
        "company": "Tech Corp",
        "title": "Senior Engineer"
    },
    {
        "name": "jane doe",
        "email": "jane.doe@example.com",
        "phone": "(415) 555-0123",
        "company": "Tech Corp",
        "title": "Sr. Engineer"
    },
]

# Clean all records
results = bulk(salesforce_leads, workers=4)

# Compare and deduplicate
duplicates = []
for i, r1 in enumerate(results):
    for r2 in results[i+1:]:
        score = compare(r1, r2)
        if score > 85:
            duplicates.append({
                "name1": r1.name_str,
                "name2": r2.name_str,
                "email1": r1.email_str,
                "email2": r2.email_str,
                "similarity": score
            })

print(duplicates)
# Output: [{'name1': 'Jane Doe', 'name2': 'jane doe', 'similarity': 98}]
# Score of 98 indicates these are almost certainly the same person
```

## HR Employee Directory

```python
from humanmint import bulk, export_csv

# Import from HR system
hr_records = [
    {
        "name": "Dr. Robert Smith, PhD",
        "email": "RSMITH@COMPANY.COM",
        "phone": "(415) 555-0001 x100",
        "department": "Engineering - Software",
        "title": "VP of Engineering"
    },
    {
        "name": "alice johnson",
        "email": "ajohnson@company.com",
        "phone": "415.555.0002",
        "department": "HR",
        "title": "HR Manager"
    },
]

# Clean and normalize
results = bulk(hr_records, workers=4)

# Export as clean CSV
export_csv(results, "clean_directory.csv", flatten=True)

# Resulting columns:
# name_first, name_last, name_gender,
# email_normalized, email_domain,
# phone_e164, phone_pretty, phone_extension,
# department_canonical, department_category,
# title_canonical, title_valid
```

## Accessing All Fields

```python
result = mint(
    name="Dr. Sarah Johnson, MBA",
    email="SARAH@COMPANY.COM",
    phone="(415) 555-0123 x456",
    department="Engineering",
    title="Senior Software Engineer"
)

# Names
print(result.name_first)         # "Sarah"
print(result.name_last)          # "Johnson"
print(result.name_gender)        # "female"

# Email
print(result.email_str)          # "sarah@company.com"
print(result.email_domain)       # "company.com"

# Phone
print(result.phone_str)          # "+1 415-555-0123"
print(result.phone_extension)    # "456"

# Title transformation stages
print(result.title["raw"])       # "Senior Software Engineer" (original)
print(result.title["canonical"]) # "senior software engineer" (standardized)
print(result.title_str)          # "senior software engineer" (shorthand for canonical)

# Print full result to see all stages
print(result)
```

## Finding Best Matches

Find the most likely person from a database:

```python
from humanmint import mint, compare, bulk

# Load your employee directory
employees = bulk([...], workers=4)

# Search for a person
search_result = mint(
    name="John Smith",
    email="john.smith@company.com"
)

# Find best match in employee directory
best_match = None
best_score = 0

for employee in employees:
    score = compare(search_result, employee)
    if score > best_score:
        best_score = score
        best_match = employee

if best_match and best_score > 75:
    print(f"Found: {best_match.name_str} (confidence: {best_score:.0f}%)")
else:
    print("No match found")
```

## Merging Multiple Data Sources

```python
from humanmint import bulk, export_sql

# Combine data from multiple systems
all_records = []

# From ADP
adp_records = load_csv("adp_export.csv")
all_records.extend(adp_records)

# From Salesforce
salesforce_records = load_csv("salesforce_export.csv")
all_records.extend(salesforce_records)

# From LinkedIn
linkedin_records = load_csv("linkedin_import.csv")
all_records.extend(linkedin_records)

# Clean all records with standard format
results = bulk(all_records, workers=8, progress=True)

# Export to master database
export_sql(results, engine, "master_contacts", flatten=True)
```
