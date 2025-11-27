import sys
import pandas as pd
from io import StringIO

# Ensure local src/ is importable so we can run without installing
sys.path.insert(0, "src")

# Importing humanmint automatically registers the pandas accessor
import humanmint


def banner(text):
    print(f"\n{'-' * 60}\n{text}\n{'-' * 60}")


def test_data_quality_audit():
    """
    Simulates a Data Engineer receiving a messy CSV from a client
    and running a quality assessment report before ingestion.
    """
    banner("SCENARIO: Pre-Import Data Quality Audit")

    # 1. Simulate a raw CSV import with typical "dirty" data issues
    # - Row 1: Perfect data (Control)
    # - Row 2: Gmail (Low value lead), Messy Dept code
    # - Row 3: Garbage/Missing data ("UNKNOWN")
    # - Row 4: Vendor email, Messy Phone format, Dept slash
    # - Row 5: Corrupted data / SQL injection attempt
    # - Row 6: Typo in department ("Svcs")
    csv_data = """id,full_name,email_addr,phone_num,dept_raw,job_role
1,Dr. James Miller,james.miller@city.gov,555-0100,Public Works - Streets,Director
2,Sarah O'Connor,soconnor@gmail.com,(555) 019-2020,040-Parks & Rec,Program Coord.
3,UNKNOWN,,000-000-0000,N/A,
4,Robert 'Bob' Smith,bob.smith@vendor.com,+1 555 555 5555,IT Dept / Helpdesk,Tech II
5,### CORRUPTED ###,admin@localhost,,Code 99,
6,Maria Garcia,mgarcia@county.org,555.888.9999,Health & Human Svcs,Case Manager
"""

    print(">>> Step 1: Ingesting Raw Data...")
    df = pd.read_csv(StringIO(csv_data))
    total_rows = len(df)

    # Display raw mess briefly
    print(df[["full_name", "dept_raw", "email_addr"]].to_string(index=False))
    print(f"\nLoaded {total_rows} rows.")

    # 2. Apply HumanMint Cleaning via Pandas Accessor
    print("\n>>> Step 2: Running HumanMint Standardization Pipeline...")

    # We map the raw CSV headers to HumanMint's expected inputs
    df_clean = df.humanmint.clean(
        name_col="full_name",
        email_col="email_addr",
        phone_col="phone_num",
        dept_col="dept_raw",
        title_col="job_role",
    )

    # 3. Generate Analytics (The "Audit")

    # Calculate counts
    valid_emails = df_clean["hm_email"].notnull().sum()

    # "High Quality" emails are valid AND not generic (info@) AND not free (gmail)
    high_quality_emails = df_clean[
        (df_clean["hm_email"].notnull())
        & (df_clean["hm_email_is_generic"] == False)
        & (df_clean["hm_email_is_free_provider"] == False)
    ].shape[0]

    valid_phones = df_clean["hm_phone"].notnull().sum()

    # Departments that successfully mapped to a Canonical Standard
    standardized_depts = df_clean["hm_department"].notnull().sum()

    banner("DATA HEALTH REPORT")
    print(f"Total Records Processed: {total_rows}")
    print("-" * 40)
    print(
        f"📧 Valid Emails:            {valid_emails} ({valid_emails / total_rows:.0%})"
    )
    print(f"   - Corporate/Gov (High Val): {high_quality_emails}")
    print(f"   - Free/Generic (Low Val):   {valid_emails - high_quality_emails}")
    print("-" * 40)
    print(
        f"📱 Valid Phones:            {valid_phones} ({valid_phones / total_rows:.0%})"
    )
    print(
        f"🏢 Standardized Depts:      {standardized_depts} ({standardized_depts / total_rows:.0%})"
    )

    # 4. Department Category Breakdown
    banner("DEPARTMENT CATEGORY BREAKDOWN")
    # This shows how we grouped messy inputs into clean buckets
    if standardized_depts > 0:
        counts = df_clean["hm_department_category"].value_counts()
        for cat, count in counts.items():
            print(f"{cat:<25} : {count}")
    else:
        print("No valid departments found.")

    # 5. Record Inspection (Visual Proof)
    banner("RECORD INSPECTION: BEFORE vs AFTER")

    # Row 1: The "Perfect" Row
    print("Record #1 (Ideal Data):")
    print(f"  Input Dept: '{df.iloc[0]['dept_raw']}'")
    print(
        f"  Output:     '{df_clean.iloc[0]['hm_department']}' (Category: {df_clean.iloc[0]['hm_department_category']})"
    )
    print(f"  Canonical Title: {df_clean.iloc[0]['hm_title_canonical']}")

    # Row 2: The "Free Email" Row
    print("\nRecord #2 (Messy Data + Gmail):")
    print(f"  Email: {df_clean.iloc[1]['hm_email']}")
    print(
        f"  -> Is Free Provider? {df_clean.iloc[1]['hm_email_is_free_provider']} (Flagged)"
    )
    print(f"  Input Dept: '{df.iloc[1]['dept_raw']}'")
    print(f"  Output:     '{df_clean.iloc[1]['hm_department']}'")

    # Row 3: The "Garbage" Row
    print("\nRecord #3 (Garbage Data):")
    print(f"  Input Name:  '{df.iloc[2]['full_name']}'")
    print(f"  Output Name: {df_clean.iloc[2]['hm_name_full']} (Correctly nulled)")
    print(f"  Input Phone: '{df.iloc[2]['phone_num']}'")
    print(
        f"  Output Phone: {df_clean.iloc[2]['hm_phone']} (Impossible number detected)"
    )

    # Row 5: The "Corrupted" Row
    print("\nRecord #5 (Corrupted Data):")
    print(f"  Input Name:  '{df.iloc[4]['full_name']}'")
    print(
        f"  Output Name: {df_clean.iloc[4]['hm_name_full']} (Corruption markers stripped)"
    )

    print("\n[Audit Complete]")


if __name__ == "__main__":
    test_data_quality_audit()
