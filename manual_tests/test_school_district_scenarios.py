import json
import sys
from typing import Dict, List

# Ensure we can import the library
sys.path.insert(0, "src")

from humanmint import mint


def test_school_district_scenarios():
    """
    Simulates a messy export from a School District or Municipal HR system.
    Tests specific logic for:
    - Educational titles (Para, Supt, Coach)
    - Educational departments (Bus Barn, Cafeteria, Board)
    - Multi-role formatting
    """

    print("=" * 80)
    print("TEST SCENARIO: School District & Municipal Roster Export")
    print("=" * 80)

    roster_data = [
        {
            "id": "ADMIN_01",
            "desc": "Superintendent with heavy credentials and legacy department code",
            "input": {
                "name": "Dr. Eleanor G. Vance, Ed.D.",
                "email": "EVANCE@DISTRICT.K12.US",
                "phone": "555-0100 ext 1",
                "department": "001-00 - Board of Education/Admin",
                "title": "Supt. of Schools",
            },
        },
        {
            "id": "TRANS_02",
            "desc": "Bus Driver with radio handle in name and garage department",
            "input": {
                "name": "Mike 'Mac' McCarthy (Radio #44)",
                "email": "transportation@district.org",
                "phone": "(555) 999-8888",
                "department": "Bus Barn / Garage",
                "title": "Bus Driver / Mechanic",
            },
        },
        {
            "id": "FOOD_03",
            "desc": "Cafeteria worker with location-specific department noise",
            "input": {
                "name": "MRS. PATRICIA O'MALLEY",
                "email": "pomalley@schools.net",
                "phone": "555.123.4567",
                "department": "Food Service - High School Cafeteria",
                "title": "Head Cook",
            },
        },
        {
            "id": "ATHLETICS_04",
            "desc": "Coach with seasonal tag in title and generic rec department",
            "input": {
                "name": "Coach Ted Lasso",
                "email": "soccer_coach@city.gov",
                "phone": "+1 555 000 0000",
                "department": "Parks & Rec / Fields",
                "title": "Varsity Soccer Coach (Boys)",
            },
        },
        {
            "id": "SUB_05",
            "desc": "Substitute teacher with generic email",
            "input": {
                "name": "TBD / Substitute",
                "email": "subs@district.k12.us",
                "department": "HR - Substitute Services",
                "title": "Sub Teacher",
            },
        },
        {
            "id": "IT_06",
            "desc": "IT Director with acronym department",
            "input": {
                "name": "Kenji Sato",
                "email": "ksato@tech.district.org",
                "department": "I.S. / Technology Dept",
                "title": "Dir. of Info Tech",
            },
        },
    ]

    for case in roster_data:
        print(f"\n🔹 Processing: {case['id']} ({case['desc']})")

        # Run Mint
        result = mint(**case["input"])

        # Extract data for display
        res_data = result.model_dump()

        # Display Input vs Output
        print(f"   {'INPUT':<30} | {'OUTPUT':<30}")
        print("   " + "-" * 65)

        # Compare Name
        in_name = case["input"].get("name", "")
        out_name = res_data["name"]["full"] if res_data["name"] else "None"
        print(f"   Name: {in_name:<24} -> {out_name}")

        # Compare Dept
        in_dept = case["input"].get("department", "")
        out_dept = (
            res_data["department"]["canonical"] if res_data["department"] else "None"
        )
        print(f"   Dept: {in_dept:<24} -> {out_dept}")

        # Compare Title
        in_title = case["input"].get("title", "")
        out_title = res_data["title"]["canonical"] if res_data["title"] else "None"
        print(f"   Role: {in_title:<24} -> {out_title}")

        # Specific assertions to ensure your logic holds up
        if case["id"] == "ADMIN_01":
            assert res_data["name"]["suffix"] is None  # Ed.D should be stripped
            assert (
                res_data["department"]["canonical"] == "Board of Education"
            )  # From your CSV map

        if case["id"] == "TRANS_02":
            # Should strip (Radio #44)
            assert "44" not in res_data["name"]["full"]
            # Should map Bus Barn to Transportation
            assert (
                "Transportation" in res_data["department"]["canonical"]
                or "Fleet" in res_data["department"]["canonical"]
            )

        if case["id"] == "FOOD_03":
            # Should handle O'Malley correctly
            assert res_data["name"]["last"] == "O'Malley"
            assert res_data["department"]["category"] == "education"

    print("\n✅ All school district scenarios processed successfully.")


if __name__ == "__main__":
    test_school_district_scenarios()
