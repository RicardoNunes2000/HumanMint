import csv
import json
import time
import random
import string
import os
from datetime import datetime
from collections import Counter


import sys

sys.path.insert(0, "src")

# Import your library
try:
    from humanmint import mint, bulk
except ImportError:
    print(
        "ERROR: Could not import 'humanmint'. Please ensure the library code is in the python path."
    )
    exit(1)

# Configuration
NUM_RECORDS = 50_000  # Adjust this number for load testing (e.g., 100,000 or 1,000,000)
WORKERS = os.cpu_count() or 4
OUTPUT_FILE = "humanmint_results.csv"
REPORT_FILE = "humanmint_report.json"

# --- 1. Data Generators (Creating the Mess) ---


def random_string(length=10):
    return "".join(random.choices(string.ascii_letters, k=length))


def generate_messy_name():
    """Generates names with formatting issues, suffixes, and SQL injection."""
    firsts = [
        "john",
        "JANE",
        "AleX",
        "mArIa",
        "Robert",
        "D'Angelo",
        "O'Connor",
        "Renée",
    ]
    lasts = ["SMITH", "doe", "O'neill", "van der waals", "McDonald", "JOHNSON"]
    suffixes = ["jr", "III", "PhD", "M.D.", ""]
    noise = ["", " ", "  ", "\t"]
    injection = ["", "'; DROP TABLE users;--", "<script>alert(1)</script>"]

    f = random.choice(firsts)
    l = random.choice(lasts)
    s = random.choice(suffixes)

    # Randomly apply casing mess
    if random.random() < 0.3:
        f = f.upper()
    if random.random() < 0.3:
        l = l.lower()

    full = f"{f} {l} {s}".strip() + random.choice(injection)
    return random.choice(noise) + full + random.choice(noise)


def generate_messy_email(name_part):
    """Generates valid, invalid, and generic emails."""
    domains = ["gmail.com", "yahoo.com", "city.gov", "company.co.uk", "bad-domain"]

    choice = random.random()
    if choice < 0.8:
        # Valid-ish
        clean_name = name_part.split()[0].lower().replace("'", "")
        return f"{clean_name}.{random.randint(1, 99)}@{random.choice(domains)}"
    elif choice < 0.9:
        # Invalid format
        return f"{name_part}@{random.choice(domains)} (Do not contact)"
    else:
        # Generic/Garbage
        return random.choice(["info@company.com", "admin@", "N/A", ""])


def generate_messy_phone():
    """Generates various phone formats."""
    formats = [
        # Basic 7-digit (rare but still seen)
        "555-0123",
        "777-8899",
        "123-4567",
        # Classic US formats with different real area codes
        "(212) 555-0199",
        "(415) 392-1234",
        "(305) 774-0900",
        "(907) 555-7777",  # Alaska
        "(808) 321-9876",  # Hawaii
        "(617) 823-4401",  # Boston
        "(404) 992-1144",  # Atlanta
        "(915) 240-6678",  # Texas El Paso
        # Dot separators
        "212.555.0199",
        "415.392.1234",
        "907.555.7777",
        # No separators
        "2125550199",
        "4153921234",
        "8083219876",
        # With +1, mixed spacing
        "+1 212 555 0199",
        "+1 (415) 392 1234",
        "+1-808-321-9876",
        "+1 305.774.0900",
        # Country code without +
        "1-212-555-0199",
        "1 (415) 392-1234",
        # Extensions
        "212-555-0199 ext 44",
        "415.392.1234 x120",
        "(305) 774-0900 ext. 887",
        "+1 404 992 1144 x55",
        "808-321-9876 extension 9001",
        # Prefixed labels
        "Phone: (212) 555-0199",
        "Tel: 415-392-1234",
        "Work: +1 305 774 0900",
        "Mobile: 404.992.1144",
        "Contact: 8083219876",
        # Odd messy ones
        "(212 555-0199",  # missing parenthesis
        "415).392.1234",  # broken closing
        "305-774  -0900",  # double separator
        "+1   404   992   1144",  # too many spaces
        "808-321-98  76",  # spaced mid block
        # Vanity numbers
        "1-800-FLOWERS",
        "1-888-BEST-BUY",
        "1-877-CALL-NOW",
        # Invalid but seen
        "000-000-0000",
        "(123) 456-7890",  # placeholder area code
        "9999999999",
        # With extra text noise
        "Customer service: (212) 555-0199",
        "Call us today at 415.392.1234!",
        "Office line --> +1 305 774 0900",
        "Hotline: 404-992-1144 ext 12 (24/7)",
        "808 321 9876 (Hawaii office)",
    ]
    if random.random() < 0.1:
        return "No Phone"  # Invalid
    return random.choice(formats)


def generate_messy_dept():
    """Generates departments that need canonicalization."""
    depts = [
        "Public Works",
        "PW Dept",
        "Dept. of Public Works",
        "005-PW",
        "Human Resources",
        "HR",
        "People Ops",
        "IT",
        "Information Technology",
        "Comp Sci",
        "Finance",
        "Rev & Tax",
        "Unknown",
    ]
    return random.choice(depts)


def generate_messy_title():
    """Generates job titles."""
    titles = [
        "Director",
        "Dir.",
        "Assistant Director",
        "Asst. Dir",
        "Manager",
        "Mgr",
        "Senior Engineer",
        "Sr. Eng.",
        "VP of Sales",
        "Vice President",
        "Chief of Police",
    ]
    return random.choice(titles)


# --- 2. Main routine (wrapped to be Windows-safe for multiprocessing) ---


def main() -> None:
    """Run HumanMint stress test with 50,000 synthetic records.

    Generates synthetic data with intentional messiness, processes it through bulk(),
    validates output quality, and reports performance metrics. Tests deduplication,
    multiprocessing, and caching behavior under realistic load.

    Test Configuration:
        - NUM_RECORDS: Number of synthetic records to generate (configurable)
        - WORKERS: Number of parallel worker processes (configurable)
        - Deduplication: Enabled to test caching performance on duplicates
        - Data: Includes messy names, emails, phones, departments, titles

    Output:
        - Prints generation time, processing time, and throughput
        - Reports data quality metrics (valid names, emails, phones)
        - Verifies that results are properly expanded after deduplication
    """
    print(f"--- HumanMint Stress Test Configuration ---")
    print(f"Records to generate: {NUM_RECORDS:,}")
    print(f"Worker processes:    {WORKERS}")
    print(f"-----------------------------------------\n")

    print("Step 1: Generating synthetic data...")
    start_gen = time.perf_counter()

    records = []
    for _ in range(NUM_RECORDS):
        # Create duplicates intentionally (10% chance)
        if records and random.random() < 0.1:
            records.append(records[-1].copy())
        else:
            nm = generate_messy_name()
            records.append(
                {
                    "name": nm,
                    "email": generate_messy_email(nm),
                    "phone": generate_messy_phone(),
                    "department": generate_messy_dept(),
                    "title": generate_messy_title(),
                    # Add overrides to test that feature
                    "dept_overrides": {"Rev & Tax": "Finance"},
                    "aggressive_clean": True if "DROP TABLE" in nm else False,
                }
            )

    gen_time = time.perf_counter() - start_gen
    print(f"Generated {len(records)} records in {gen_time:.2f} seconds.")

    # --- 3. Processing Phase (The Test) ---

    print("\nStep 2: Running HumanMint.bulk()...")
    start_proc = time.perf_counter()

    # We enable deduplication to test that logic as well
    results = bulk(records, workers=WORKERS, progress=False, deduplicate=True)

    proc_time = time.perf_counter() - start_proc
    rate = len(records) / proc_time

    print(f"\nProcessing complete!")
    print(f"Total Time:  {proc_time:.2f} seconds")
    print(f"Throughput:  {rate:.0f} records/second")

    # --- 4. Analysis & Validation ---

    print("\nStep 3: Analyzing results...")

    stats = {
        "total_records": len(results),
        "valid_emails": 0,
        "valid_phones": 0,
        "names_changed": 0,
        "departments_canonicalized": 0,
        "titles_standardized": 0,
        "sql_injections_neutralized": 0,
    }

    # CSV Writer setup
    csv_headers = [
        "original_name",
        "clean_name",
        "name_quality",
        "name_salutation",
        "original_email",
        "clean_email",
        "email_valid",
        "clean_phone",
        "phone_type",
        "phone_location",
        "phone_time_zones",
        "dept_raw",
        "dept_canonical",
        "title_raw",
        "title_canonical",
        "title_seniority",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for i, res in enumerate(results):
            orig = records[i]

            # Stats Counting
            if res.email_is_valid:
                stats["valid_emails"] += 1

            if res.phone_is_valid:
                stats["valid_phones"] += 1

            if res.name_standardized != orig["name"]:
                stats["names_changed"] += 1

            # Check if canonicalization happened (Result different from Normalized input)
            if (
                res.department_canonical
                and res.department_canonical != res.department_normalized
            ):
                stats["departments_canonicalized"] += 1

            if res.title_canonical:
                stats["titles_standardized"] += 1

            # Security check
            if "DROP TABLE" in orig["name"] and "DROP TABLE" not in (
                res.name_standardized or ""
            ):
                stats["sql_injections_neutralized"] += 1

            # Write sample to CSV
            writer.writerow(
                [
                    orig["name"],
                    res.name_standardized,
                    "Good"
                    if res.name_standardized and len(res.name_standardized.split()) >= 2
                    else "Partial",
                    res.name_salutation,
                    orig["email"],
                    res.email_standardized,
                    res.email_is_valid,
                    res.phone_pretty,
                    res.phone_type,
                    res.phone_location,
                    ";".join(res.phone_time_zones) if res.phone_time_zones else None,
                    res.department_raw,
                    res.department_canonical,
                    res.title_raw,
                    res.title_canonical,
                    res.title_seniority,
                ]
            )

    # --- 5. Reporting ---

    report = {
        "performance": {
            "records_processed": NUM_RECORDS,
            "duration_seconds": round(proc_time, 2),
            "records_per_second": round(rate, 2),
            "workers": WORKERS,
        },
        "quality_metrics": {
            "email_validity_rate": f"{(stats['valid_emails'] / NUM_RECORDS) * 100:.1f}%",
            "phone_validity_rate": f"{(stats['valid_phones'] / NUM_RECORDS) * 100:.1f}%",
            "data_cleaning_impact": f"{(stats['names_changed'] / NUM_RECORDS) * 100:.1f}% records modified",
        },
        "normalization": {
            "departments_mapped": stats["departments_canonicalized"],
            "titles_mapped": stats["titles_standardized"],
        },
        "security": {"sql_injections_caught": stats["sql_injections_neutralized"]},
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("\n--- Final Report ---")
    print(json.dumps(report, indent=2))
    print(f"\nDetailed CSV written to: {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()
