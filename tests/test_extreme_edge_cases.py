"""Test extreme edge cases that challenge HumanMint's robustness."""

import sys

sys.path.insert(0, "src")

import json

from humanmint import mint

# 10 extreme edge-case scenarios
test_scenarios = [
    {
        "id": "1_UNICODE_WILDCARD",
        "description": "Unicode punctuation, accents, CRM noise in name",
        "input": {
            "name": "Dr. Andrea   Lopez–Martinez (TEMP USER)",
            "email": "ANDREA.LOPEZ@CITY.GOV",
            "phone": "+1 (415) 555-0101 ext 44",
            "department": "Public Safety–HQ 00231",
            "title": "Interim Police Chief"
        }
    },
    {
        "id": "2_EMAIL_INSIDE_NAME",
        "description": "Name contains email address; email malformed; phone valid",
        "input": {
            "name": "Michael (mike_the_god@aol) Thompson",
            "email": "mike_the_god@@aol.com",
            "phone": "(650)555-0193",
            "department": "Finance / Budget Office",
            "title": "Sr. Budget Analyst"
        }
    },
    {
        "id": "3_DEPARTMENT_IS_A_BUILDING",
        "description": "Department field is actually a physical building name",
        "input": {
            "name": "Jane     Wu",
            "email": "jwu@harbor.city.gov",
            "phone": "1.202.555.7777",
            "department": "Harbor Building 04B - Room 220",
            "title": "Harbor Master"
        }
    },
    {
        "id": "4_TITLE_INSIDE_NAME",
        "description": "Title embedded inside name, generic inbox email, invalid phone",
        "input": {
            "name": "Deputy Director Christopher    Hall",
            "email": "support@agency.gov",
            "phone": "111-111-1111",
            "department": "Human Resources",
            "title": "Deputy Director"
        }
    },
    {
        "id": "5_MISSING_NAME_DATA",
        "description": "Name missing, only email/phone/department available",
        "input": {
            "name": None,
            "email": "clerk.office@county.gov",
            "phone": "+1-503-555-0000",
            "department": "Clerk's Office (Payments)",
            "title": "Office Manager"
        }
    },
    {
        "id": "6_PHONE_EXTENSIONS_EXTREME",
        "description": "Multiple phone formats with complex extensions",
        "input": {
            "name": "Sarah Johnson",
            "email": "sjohnson@dept.gov",
            "phone": "Ext: 9999 from (650)555.0193",
            "department": "Parks & Recreation",
            "title": "Parks Manager"
        }
    },
    {
        "id": "7_EMPTY_AND_WHITESPACE",
        "description": "Fields with only whitespace and empty strings",
        "input": {
            "name": "   ",
            "email": "",
            "phone": "      ",
            "department": None,
            "title": ""
        }
    },
    {
        "id": "8_WEIRD_DEPARTMENT_NAMES",
        "description": "Department names with slashes, parentheses, multiple codes",
        "input": {
            "name": "Robert Chen",
            "email": "rchen@agency.org",
            "phone": "(555) 123-4567",
            "department": "005 / 006 - Bureau (Actual) of [Something]",
            "title": "Coordinator"
        }
    },
    {
        "id": "9_ALL_CAPS_AND_SPECIAL_CHARS",
        "description": "Name in ALL CAPS with special characters and numbers",
        "input": {
            "name": "DR. JOHN O'CONNOR III, JR.",
            "email": "JOHN.O'CONNOR@GOV.ORG",
            "phone": "+1-555.123.4567 extension 001-002",
            "department": "PUBLIC-SAFETY_OFFICE",
            "title": "Chief Investigator I/II"
        }
    },
    {
        "id": "10_NONE_AND_UNEXPECTED_TYPES",
        "description": "Mix of None values, empty values, and edge cases",
        "input": {
            "name": None,
            "email": None,
            "phone": None,
            "department": None,
            "title": None
        }
    }
]

print("=" * 100)
print("EXTREME EDGE CASE TEST SUITE - 10 Scenarios")
print("=" * 100)

results = []
for scenario in test_scenarios:
    scenario_id = scenario["id"]
    description = scenario["description"]
    input_data = scenario["input"]

    print(f"\n[{scenario_id}] {description}")
    print("-" * 100)
    print("Input:")
    print(json.dumps(input_data, indent=2, default=str))

    try:
        result = mint(
            name=input_data.get("name"),
            email=input_data.get("email"),
            phone=input_data.get("phone"),
            department=input_data.get("department"),
            title=input_data.get("title"),
        )

        output = result.model_dump()
        print("\nOutput (cleaned):")
        print(json.dumps(output, indent=2, default=str))

        results.append({
            "id": scenario_id,
            "status": "PASS",
            "error": None
        })
        print("\n[SUCCESS] Processed without errors")

    except Exception as e:
        results.append({
            "id": scenario_id,
            "status": "FAIL",
            "error": str(e)
        })
        print(f"\n[ERROR] {type(e).__name__}: {e}")

print("\n" + "=" * 100)
print("TEST SUMMARY")
print("=" * 100)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print(f"\nResults: {passed} passed, {failed} failed out of {len(results)} scenarios")
print()

for result in results:
    status_str = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
    print(f"{status_str} {result['id']}")
    if result["error"]:
        print(f"       Error: {result['error']}")

if failed == 0:
    print("\n[SUCCESS] All edge cases handled gracefully!")
else:
    print(f"\n[WARNING] {failed} scenario(s) failed - review errors above")
