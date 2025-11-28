# Fields Reference

Complete guide to accessing all fields returned by `mint()` using properties.

## Names

```python
result = mint(name="Dr. John Q. Smith, PhD")

result.name_str         # "John Q Smith"
result.name_first       # "John"
result.name_last        # "Smith"
result.name_middle      # "Q"
result.name_suffix      # "phd"
result.name_gender      # "male"
```

## Emails

```python
result = mint(email="JOHN.SMITH@CITY.GOV")

result.email_str        # "john.smith@city.gov"
result.email_domain     # "city.gov"
result.email_valid      # True
result.email_generic    # False (not gmail, hotmail, etc.)
result.email_free       # False (not from free provider)
```

## Phones

```python
result = mint(phone="(202) 555-0173 x456")

result.phone_str        # "+1 202-555-0173" (preferred format)
result.phone_e164       # "+12025550173" (E.164 international)
result.phone_pretty     # "+1 202-555-0173" (human-readable)
result.phone_extension  # "456"
result.phone_valid      # True
result.phone_type       # "fixed_line" or "mobile"
```

## Departments

```python
result = mint(department="001 - Public Works Dept")

result.department_str       # "Public Works"
result.department_normalized # "Public Works" (before canonical match)
result.department_category   # "infrastructure"
result.department_override   # False (not from custom overrides)
```

## Titles

```python
result = mint(title="0001 - Chief of Police (Downtown)")

result.title_raw         # "0001 - Chief of Police (Downtown)" (original input)
result.title_normalized  # "Chief Of Police" (cleaned, human-readable)
result.title_canonical   # "police chief" (standardized, machine-friendly)
result.title_valid       # True (matched a known title)
result.title_confidence  # 0.95 (confidence score)
```

**Three stages of transformation:**
- **raw**: Exactly what you provided (with codes, noise, etc.)
- **normalized**: After cleaning (title case, noise removed, human-readable)
- **canonical**: Standardized from database (lowercase, machine-friendly for comparisons)

## Addresses

```python
result = mint(address="123 Main St Apt 4B, Springfield, IL 62701")

result.address_raw       # "123 Main St Apt 4B, Springfield, IL 62701"
result.address_street    # "123 Main St"
result.address_unit      # "Apt 4B"
result.address_city      # "Springfield"
result.address_state     # "IL"
result.address_zip       # "62701"
result.address_country   # "US"
result.address_canonical # "123 Main St Apt 4B Springfield IL 62701 US"
```

## Organizations

```python
result = mint(organization="City of Springfield Police")

result.organization_raw         # "City of Springfield Police"
result.organization_normalized  # "Springfield Police"
result.organization_canonical   # "Springfield Police"
result.organization_confidence  # 0.85 (confidence score)
```

## Cheat Sheet

| What You Want | Property |
|---|---|
| Full name | `result.name_str` |
| Email (normalized) | `result.email_str` |
| Phone (pretty) | `result.phone_str` |
| Phone (E.164) | `result.phone_e164` |
| Department | `result.department_str` |
| Title (canonical) | `result.title_canonical` |
| Title (original) | `result.title_raw` |
| Address | `result.address_canonical` |
| Organization | `result.organization_canonical` |

## Safe Access with get()

For optional fields, use the `.get()` accessor:

```python
# Safe access with default value
result.get("email.domain", "unknown")     # Returns domain or "unknown"
result.get("title.canonical", None)       # Returns canonical or None
result.get("phone.extension", "")         # Returns extension or ""
```

## Exporting to dict

```python
# Full dict with all fields
data = result.model_dump()

# Or access the raw dicts directly
title_dict = result.title  # {'raw': '...', 'normalized': '...', 'canonical': '...'}
```
