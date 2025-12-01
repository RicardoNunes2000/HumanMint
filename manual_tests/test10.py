import sys

sys.path.insert(0, "src")


from humanmint import mint

REAL_US_CASES = [
    {
        "desc": "Common city employee, mild mess",
        "input": {
            "name": "  Mr. Thomas   A.    Green  ",
            "email": "tgreen@cityofraleigh.nc.gov",
            "phone": "(919) 555-0144 ext. 55",
            "department": "Public Works Dept.",
            "title": "Sr Maint Tech",
        },
        "expected": {
            "name_standardized": "Thomas A Green",
            "email_standardized": "tgreen@cityofraleigh.nc.gov",
            "department_canonical": "Public Works",
            "title_canonical": "maintenance technician",
        },
    },
    {
        "desc": "County office, typical abbreviations",
        "input": {
            "name": "Jennifer G. Watkins",
            "email": "jwatkins@co.lake.il.us",
            "phone": "847-555-9988",
            "department": "Emer Mgmt",
            "title": "Deputy Dir",
        },
        "expected": {
            "name_standardized": "Jennifer G Watkins",
            "department_canonical": "Emergency Management",
            "title_canonical": "deputy director",
        },
    },
    {
        "desc": "School district, normal US formatting",
        "input": {
            "name": "Dr. Angela S Pierce",
            "email": "angela.pierce@schoolsd.org",
            "phone": "555-222-1111",
            "department": "District Admin",
            "title": "Curriculum Coordinator",
        },
        "expected": {
            "name_standardized": "Angela S Pierce",
            "department_canonical": "Administration",
            "title_canonical": "curriculum coordinator",
        },
    },
    {
        "desc": "Police dept, simple nicknames",
        "input": {
            "name": "Lt Joe 'Bobby' McCarthy",
            "email": "jmccarthy@town.gov",
            "phone": "406-555-9090",
            "department": "Police Dept",
            "title": "Police Officer II",
        },
        "expected": {
            "name_standardized": "Joe Bobby McCarthy",
            "department_canonical": "Police",
            "title_canonical": "police officer",
        },
    },
    {
        "desc": "Parks & Rec worker",
        "input": {
            "name": "Tyler M Jones",
            "email": "tjones@parks.city.gov",
            "phone": "503-555-8899",
            "department": "P&R",
            "title": "Rec Supervisor",
        },
        "expected": {
            "department_canonical": "Parks & Recreation",
            "title_canonical": "recreation supervisor",
        },
    },
]


def test_real_us():
    print("=" * 80)
    print("HUMANMINT — REAL-WORLD US TEST")
    print("=" * 80)

    failures = 0

    for case in REAL_US_CASES:
        print(f"\nTest: {case['desc']}")
        print("-" * 80)

        r = mint(**case["input"])
        out = {
            "name_standardized": r.name_standardized,
            "email_standardized": r.email_standardized,
            "phone_standardized": r.phone_standardized,
            "department_canonical": r.department_canonical,
            "title_canonical": r.title_canonical,
        }

        for field, expected in case["expected"].items():
            actual = out.get(field)

            if actual != expected:
                print(f"  FAIL: {field}")
                print(f"    expected: {expected}")
                print(f"    actual:   {actual}")
                failures += 1
            else:
                print(f"  OK: {field}: {actual}")

    print("\n" + "=" * 80)

    if failures == 0:
        print("RESULT: PASS — HumanMint handles normal US data correctly.")
    else:
        print(f"RESULT: FAIL — {failures} mismatches on normal US data.")

    print("=" * 80)


if __name__ == "__main__":
    test_real_us()
