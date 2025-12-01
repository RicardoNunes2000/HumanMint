import json
import sys

sys.path.insert(0, "src")

import pandas as pd

# Ensure we can import the library
sys.path.insert(0, "src")
from humanmint import mint


def test_real_world_scenarios():
    # A mock "Nightmare CSV" containing inconsistent, messy data
    data = [
        {
            "id": 1,
            "desc": "Government Official (Messy)",
            "full_name": "OFC. JAMES 'JIMMY' O'CONNOR III",  # Rank, nickname, suffix
            "email": "JIM.OCONNOR@POLICE.CI.BOSTON.MA.US",  # Uppercase, complex domain
            "phone": "617.555.1234 ext 404",  # Dot format with extension
            "dept": "001-POLICE DEPT (NORTH PRECINCT)",  # Code, abbreviation, extra info
            "title": "SGT / PATROL SUPERVISOR",  # Abbreviation, slash
        },
        {
            "id": 2,
            "desc": "Medical Professional (Typos)",
            "full_name": "Dr. Sarah Jenkins, PhD",  # Prefix/Suffix
            "email": "sjenkins@health.org",
            "phone": "+1 (415) 555-0000",
            "dept": "Public Hlth & Safety",  # Typo "Hlth"
            "title": "Dir. of Public Health",  # Needs canonicalization
        },
        {
            "id": 3,
            "desc": "Garbage / System Row",
            "full_name": "### TEMP USER ###",  # Garbage
            "email": "admin+test@localhost",  # Invalid/Generic
            "phone_num": "000-000-0000",  # Impossible number
            "dept": "N/A",
            "title": "UNKNOWN",
        },
        {
            "id": 4,
            "desc": "Corporate / Generic Inbox",
            "full_name": "  mary   louise   parker  ",  # Bad spacing
            "email": "info@parker-consulting.com",  # Generic inbox
            "phone": "555-1234",  # Invalid (missing area code)
            "dept": "Human   Resourcs",  # Typo, double space
            "title": "HR Generalist II",  # Acronym preservation
        },
        {
            "id": 5,
            "desc": "Public Works (Abbr)",
            "full_name": 'Robert "Bob" Smith',
            "email": "bob.smith@city.gov",
            "phone": "(503) 555-9999",
            "dept": "PW / Streets",  # Common abbreviation
            "title": "Maint. Worker",
        },
    ]

    print("=" * 80)
    print("HUMANMINT REAL-WORLD DATA REVIEW")
    print("=" * 80)

    processed_rows = []

    for row in data:
        # Run HumanMint on the row
        res = mint(
            name=row.get("full_name"),
            email=row.get("email"),
            phone=row.get("phone") or row.get("phone_num"),
            department=row.get("dept"),
            title=row.get("title"),
            aggressive_clean=True,  # Enable for garbage rows
        )

        # Compile results for display
        processed_rows.append(
            {
                "Scenario": row["desc"],
                "ORIGINAL Name": row.get("full_name"),
                "MINTED Name": res.name_standardized,
                "Gender": res.name_gender,
                "ORIGINAL Dept": row.get("dept"),
                "MINTED Dept": res.department_canonical,  # Canonical
                "Category": res.department_category,
                "MINTED Title": res.title_raw,
                "Is Generic Email?": res.email_is_generic_inbox,
                "Phone Valid?": res.phone_is_valid,
            }
        )

    # Create a Pandas DataFrame for clean visualization
    df = pd.DataFrame(processed_rows)

    # Adjust pandas settings to ensure we see the full output
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 25)

    # Print the comparison table
    print(df.to_string(index=False))

    print("\n" + "=" * 80)
    print("DETAILED INSPECTION OF ROW 1 (Government Official)")
    print("=" * 80)
    # Show the full detailed dictionary for the first complex row
    # This proves all the metadata (first/last split, phone e164) is there
    complex_res = mint(
        name=data[0]["full_name"],
        email=data[0]["email"],
        phone=data[0]["phone"],
        department=data[0]["dept"],
        title=data[0]["title"],
    )
    print(json.dumps(complex_res.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    test_real_world_scenarios()
