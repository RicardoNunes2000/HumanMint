"""Test humanmint comprehensively across all fields."""

import sys

sys.path.insert(0, "src")

from humanmint import bulk

# Sample of realistic messy records covering all field types
test_records = [
    {
        "name": "Dr. John Q. Smith, PhD",
        "email": "JOHN.SMITH@CITY.GOV",
        "phone": "(202) 555-0173 ext 456",
        "title": "Chief of Police",
        "department": "001 - Police Dept",
        "address": "123 Main St, Springfield, IL 62701",
    },
    {
        "name": "Jane M. Wilson",
        "email": "jane.wilson@gmail.com",
        "phone": "202-555-0174",
        "title": "Sr. Water Engineer",
        "department": "Public Works Department",
        "address": "456 Oak Ave, Springfield IL 62702",
    },
    {
        "name": "robert brown jr.",
        "email": "rbrown@CITY.GOV",
        "phone": "+1 (202) 555-0175",
        "title": "Dir., Planning",
        "department": "Planning & Development",
        "address": "789 Elm Street Springfield, Illinois 62703",
    },
    {
        "name": "Maria Garcia-Lopez",
        "email": "MARIA.GARCIA@CITY.GOV",
        "phone": "2025550176",
        "title": "Manager IT",
        "department": "IT - Information Technology",
        "address": "321 Pine Ln Springfield IL",
    },
    {
        "name": "David Chen",
        "email": "david.chen@city.gov",
        "phone": "202.555.0177 x200",
        "title": "Deputy Chief Financial Officer",
        "department": "Finance & Budget",
        "address": "654 Maple Dr, Springfield, Illinois",
    },
    {
        "name": "Patricia O'Brien",
        "email": "p.obrien@city.gov",
        "phone": "(202) 555-0178",
        "title": "Principal Planner",
        "department": "Planning Dept",
        "address": "987 Cedar Ave, Springfield, IL 62704",
    },
    {
        "name": "Michael Johnson",
        "email": "mjohnson@fire.city.gov",
        "phone": "555-0179",
        "title": "Fire Chief",
        "department": "Fire & Rescue",
        "address": "147 Birch St Springfield IL",
    },
    {
        "name": "SANDRA LEE",
        "email": "sandra.lee@city.gov",
        "phone": "2025550180",
        "title": "Asst. City Manager",
        "department": "City Manager Office",
        "address": "258 Walnut Way, Springfield, Illinois 62705",
    },
    {
        "name": "Thomas Martinez",
        "email": "t.martinez@city.gov",
        "phone": "+1-202-555-0181",
        "title": "Director of Parks",
        "department": "Parks & Recreation",
        "address": "369 Oak Ridge Rd Springfield IL 62706",
    },
    {
        "name": "angela.davis",
        "email": "a.davis@city.gov",
        "phone": "(202)555-0182",
        "title": "HR Manager",
        "department": "Human Resources",
        "address": "741 Spruce Lane, Springfield, IL",
    },
    {
        "name": "Christopher R. Taylor, IV",
        "email": "c.taylor@city.gov",
        "phone": "202 555 0183",
        "title": "Civil Engineer",
        "department": "Public Works",
        "address": "852 Hickory Hts Springfield IL 62707",
    },
    {
        "name": "Lisa Anderson",
        "email": "l.anderson@city.gov",
        "phone": "2025550184 extension 101",
        "title": "Budget Analyst",
        "department": "Finance",
        "address": "963 Ash Ave, Springfield, Illinois",
    },
    {
        "name": "James Wilson",
        "email": "j.wilson@police.city.gov",
        "phone": "(202) 555-0185",
        "title": "Police Officer III",
        "department": "Police",
        "address": "147 Sycamore St Springfield IL 62708",
    },
    {
        "name": "Rebecca Thompson",
        "email": "r.thompson@city.gov",
        "phone": "202.555.0186 ext 50",
        "title": "Administrative Assistant",
        "department": "City Hall Admin",
        "address": "258 Dogwood Dr, Springfield, IL",
    },
    {
        "name": "kevin harris",
        "email": "k.harris@city.gov",
        "phone": "202-555-0187",
        "title": "Community Services Manager",
        "department": "Community Services",
        "address": "369 Magnolia Ln Springfield Illinois 62709",
    },
]

print("=" * 120)
print(f"TESTING HUMANMINT COMPREHENSIVE - ALL FIELDS ({len(test_records)} records)")
print("=" * 120)

results = bulk(test_records, workers=4, progress=False)

# Analysis containers
analyses = {
    "name": {"valid": 0, "invalid": 0, "examples": []},
    "email": {"valid": 0, "invalid": 0, "generic": 0, "free": 0, "examples": []},
    "phone": {"valid": 0, "invalid": 0, "has_extension": 0, "examples": []},
    "address": {"valid": 0, "invalid": 0, "has_state": 0, "has_zip": 0, "examples": []},
}

for i, record in enumerate(test_records):
    result = results[i]

    # NAME ANALYSIS
    name_valid = result.name.get("is_valid", False)
    if name_valid:
        analyses["name"]["valid"] += 1
    else:
        analyses["name"]["invalid"] += 1
    analyses["name"]["examples"].append(
        {
            "raw": record.get("name", ""),
            "first": result.name_first,
            "last": result.name_last,
            "full": result.name_str,
        }
    )

    # EMAIL ANALYSIS
    email_valid = result.email.get("is_valid", False)
    if email_valid:
        analyses["email"]["valid"] += 1
        if result.email.get("is_generic"):
            analyses["email"]["generic"] += 1
        if result.email.get("is_free"):
            analyses["email"]["free"] += 1
    else:
        analyses["email"]["invalid"] += 1
    analyses["email"]["examples"].append(
        {
            "raw": record.get("email", ""),
            "normalized": result.email_str,
            "valid": email_valid,
            "free": result.email.get("is_free", False),
        }
    )

    # PHONE ANALYSIS
    phone_valid = result.phone.get("is_valid", False)
    if phone_valid:
        analyses["phone"]["valid"] += 1
        if result.phone_extension:
            analyses["phone"]["has_extension"] += 1
    else:
        analyses["phone"]["invalid"] += 1
    analyses["phone"]["examples"].append(
        {
            "raw": record.get("phone", ""),
            "formatted": result.phone_str,
            "e164": result.phone_e164,
            "extension": result.phone_extension,
            "valid": phone_valid,
        }
    )

    # ADDRESS ANALYSIS
    address_canonical = result.address.get("canonical") if result.address else None
    if address_canonical:
        analyses["address"]["valid"] += 1
        if result.address.get("state"):
            analyses["address"]["has_state"] += 1
        if result.address.get("zip"):
            analyses["address"]["has_zip"] += 1
    else:
        analyses["address"]["invalid"] += 1
    analyses["address"]["examples"].append(
        {
            "raw": record.get("address", ""),
            "formatted": address_canonical,
            "city": result.address.get("city") if result.address else None,
            "state": result.address.get("state") if result.address else None,
            "zip": result.address.get("zip") if result.address else None,
        }
    )

print("\n" + "=" * 120)
print("NAMES")
print("=" * 120)
print(f"Valid:   {analyses['name']['valid']}/{len(test_records)}")
print(f"Invalid: {analyses['name']['invalid']}/{len(test_records)}")
print("\nExamples:")
for ex in analyses["name"]["examples"][:5]:
    print(f"  Input:  {ex['raw']}")
    print(f"  Output: {ex['full']} (First: {ex['first']}, Last: {ex['last']})")
    print()

print("\n" + "=" * 120)
print("EMAILS")
print("=" * 120)
print(f"Valid:        {analyses['email']['valid']}/{len(test_records)}")
print(f"Invalid:      {analyses['email']['invalid']}/{len(test_records)}")
print(f"Generic:      {analyses['email']['generic']} (info@, admin@, etc.)")
print(f"Free Provider:{analyses['email']['free']} (Gmail, Yahoo, etc.)")
print("\nExamples:")
for ex in analyses["email"]["examples"][:5]:
    status = "VALID" if ex["valid"] else "INVALID"
    print(f"  Input:  {ex['raw']:30} -> {ex['normalized']:30} [{status}]")
    if ex["free"]:
        print("(FREE PROVIDER)")

print("\n" + "=" * 120)
print("PHONES")
print("=" * 120)
print(f"Valid:        {analyses['phone']['valid']}/{len(test_records)}")
print(f"Invalid:      {analyses['phone']['invalid']}/{len(test_records)}")
print(f"Has Extension:{analyses['phone']['has_extension']}")
print("\nExamples:")
for ex in analyses["phone"]["examples"][:8]:
    status = "VALID" if ex["valid"] else "INVALID"
    ext_str = f" (ext: {ex['extension']})" if ex["extension"] else ""
    e164 = ex["e164"] or "INVALID"
    pretty = ex["formatted"] or "INVALID"
    print(f"  Input:  {ex['raw']:30}")
    print(f"  E.164:  {e164:20} Pretty: {pretty:20} [{status}]{ext_str}")
    print()

print("\n" + "=" * 120)
print("ADDRESSES")
print("=" * 120)
print(f"Parsed:       {analyses['address']['valid']}/{len(test_records)}")
print(f"Has State:    {analyses['address']['has_state']}")
print(f"Has ZIP:      {analyses['address']['has_zip']}")
print("\nExamples:")
for ex in analyses["address"]["examples"][:8]:
    city = ex["city"] or "?"
    state = ex["state"] or "?"
    zip_code = ex["zip"] or "?"
    print(f"  Input:  {ex['raw']}")
    print(f"  City:   {city:20} State: {state:3} ZIP: {zip_code}")
    print()

print("\n" + "=" * 120)
print("OVERALL FIELD QUALITY ASSESSMENT")
print("=" * 120)
name_rate = (analyses["name"]["valid"] / len(test_records)) * 100
email_rate = (analyses["email"]["valid"] / len(test_records)) * 100
phone_rate = (analyses["phone"]["valid"] / len(test_records)) * 100
address_rate = (analyses["address"]["valid"] / len(test_records)) * 100

print(f"\nNames:    {name_rate:5.1f}% valid")
print(f"Emails:   {email_rate:5.1f}% valid")
print(f"Phones:   {phone_rate:5.1f}% valid")
print(f"Addresses:{address_rate:5.1f}% parsed")
