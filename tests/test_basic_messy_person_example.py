import sys

sys.path.insert(0, "src")

from humanmint import mint
import json

# 1. Create a "messy" random person record
# (Simulating bad data from a CSV or legacy database)
raw_person = {
    "name": "Dr. Alex J. Mercer, PhD",  # Contains prefix, suffix, middle initial
    "email": "ALEX.MERCER@CITY.GOV",  # Screaming caps
    "phone": "(201) 555-0123 x 101",  # Formatted phone with extension
    "department": "005 - Public Wrks Dept",  # Codes, abbreviation, typos
    "title": "Dir. of Public Works",  # Abbreviated title
}

print("--- 1. Input (Messy Data) ---")
print(json.dumps(raw_person, indent=2))

# 2. Run it through HumanMint
result = mint(
    name=raw_person["name"],
    email=raw_person["email"],
    phone=raw_person["phone"],
    department=raw_person["department"],
    title=raw_person["title"],
)

# 3. View the cleaned result
print("\n--- 2. Output (Cleaned Data) ---")
print(json.dumps(result.model_dump(), indent=2))

# 4. Verify specific fields (Simple Assertions)
# Name should be parsed and capitalized
assert result.name["first"] == "Alex"
assert result.name["last"] == "Mercer"
# Professional suffixes (PhD/MD/etc.) are stripped from the name
assert result.name["suffix"] in (None, "phd")

# Email should be lowercase (normalized)
assert result.email["normalized"] == "alex.mercer@city.gov"
assert result.email["is_valid"]

# Phone should be E.164 pretty format (US)
assert "+1 201-555-0123" in result.phone["pretty"]

# Department should be mapped to canonical "Public Works"
assert result.department["canonical"] == "Public Works"
assert result.department["category"] == "infrastructure"

# Title should be canonicalized
assert result.title["canonical"] in (None, "public works director")

print("\n[SUCCESS] Test passed! The random person was successfully minted.")
