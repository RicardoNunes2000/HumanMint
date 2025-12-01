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
            "name_str": "Thomas A Green",
            "email_str": "tgreen@cityofraleigh.nc.gov",
            "department_str": "Public Works",
            "title_str": "maintenance technician",
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
            "name_str": "Jennifer G Watkins",
            "department_str": "Emergency Management",
            "title_str": "deputy director",
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
            "name_str": "Angela S Pierce",
            "department_str": "Administration",
            "title_str": "curriculum coordinator",
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
            "name_str": "Joe Bobby McCarthy",
            "department_str": "Police",
            "title_str": "police officer",
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
            "department_str": "Parks & Recreation",
            "title_str": "recreation supervisor",
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
            "name_str": r.name_str,
            "email_str": r.email_str,
            "phone_str": r.phone_str,
            "department_str": r.department_str,
            "title_str": r.title_str,
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
