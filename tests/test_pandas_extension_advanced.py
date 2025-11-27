import sys
import json

# Ensure local src/ is importable
sys.path.insert(0, "src")

from humanmint import mint, compare


def print_record(label, record):
    """Helper to print a condensed version of a MintResult"""
    name = record.name["full"] if record.name else "N/A"
    dept = record.department["canonical"] if record.department else "N/A"
    email = record.email["normalized"] if record.email else "N/A"
    phone = record.phone["pretty"] if record.phone else "N/A"
    title = record.title["canonical"] if record.title else "N/A"
    print(f"  {label:<10} | {name:<20} | {dept:<15} | {email:<25} | {title}")


def run_comparison(title, data_a, data_b):
    print(f"\n>> SCENARIO: {title}")
    print("-" * 90)
    print(
        f"  {'TYPE':<10} | {'NAME':<20} | {'DEPT (Canon)':<15} | {'EMAIL':<25} | {'TITLE (Canon)'}"
    )
    print("-" * 90)

    # 1. Mint the records (Clean them first)
    a = mint(**data_a)
    b = mint(**data_b)

    # 2. Print what HumanMint 'sees' after cleaning
    print_record("Record A", a)
    print_record("Record B", b)

    # 3. Run the comparison logic
    score = compare(a, b)

    # 4. Verdict
    print("-" * 90)
    print(f"  MATCH CONFIDENCE SCORE: {score}/100")

    if score >= 80:
        print("  VERDICT: ✅ SAME PERSON (High Confidence)")
    elif score >= 50:
        print("  VERDICT: ⚠️ POTENTIAL MATCH (Manual Review)")
    else:
        print("  VERDICT: ❌ DIFFERENT PEOPLE")
    print("=" * 90)


def main():
    print("=" * 90)
    print("HUMANMINT ENTITY RESOLUTION TESTER")
    print("=" * 90)

    # 1. The "Bob vs Robert" Problem (High Difficulty)
    # Different name variants, Dept Abbreviation vs Full, formatted vs unformatted phone
    run_comparison(
        "Nickname & Abbreviation Matching",
        {
            "name": "Robert J. Smith",
            "department": "Public Works Department",
            "phone": "(555) 123-4567",
        },
        {
            "name": "Bob Smith",
            "department": "PW - Streets Div",
            "phone": "555.123.4567",
        },
    )

    # 2. The Typos & Noise Problem
    # Garbage in name, misspelled dept, same email (strong linker)
    run_comparison(
        "Typos & Corruption Handling",
        {
            "name": "### TEMP ### Jonathan Doe",
            "email": "jdoe@city.gov",
            "department": "Polcie Dept",  # Typo
        },
        {
            "name": "Jon Doe",
            "email": "JDOE@CITY.GOV",  # Case difference
            "department": "Police",
        },
    )

    # 3. The "Imposter" Problem (Negative Test)
    # Same Name, Same Dept, BUT different email user -> Should be LOW score
    run_comparison(
        "Same Name / Different Person check",
        {"name": "Michael Chen", "email": "mchen@agency.gov", "department": "IT"},
        {
            "name": "Michael Chen",
            "email": "michael.chen.2@agency.gov",
            "department": "IT",
        },
    )

    # 4. The "Missing Data" Problem
    # One record has email, one doesn't. Can we match on Name + Title?
    run_comparison(
        "Partial Data Matching",
        {
            "name": "Sarah Connor",
            "title": "Dir. of Operations",
            "department": "Facilities",
        },
        {
            "name": "S. Connor",
            "title": "Operations Director",
            "phone": "555-0000",  # Extra info in B not in A
        },
    )

    # 5. International / Unicode
    run_comparison(
        "Unicode Normalization Match",
        {"name": "Andréa Müller", "email": "amuller@global.org"},
        {"name": "Andrea Muller", "email": "amuller@global.org"},
    )


if __name__ == "__main__":
    main()
