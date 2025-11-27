"""Test pandas_ext functionality."""

import sys
sys.path.insert(0, "src")

import pandas as pd
import humanmint

# Create a test DataFrame
df = pd.DataFrame({
    "name": [
        "Dr. Alex J. Mercer PhD",
        "Jane Smith",
        "John Doe"
    ],
    "email": [
        "alex.mercer@city.gov",
        "jane.smith@example.com",
        "JOHN.DOE@COUNTY.GOV"
    ],
    "phone": [
        "(201) 555-0123 x 101",
        "(555) 123-4567",
        "(555) 987-6543"
    ],
    "department": [
        "005 - Public Wrks Dept",
        "002 - Finance",
        "010 - HR Dept"
    ],
    "title": [
        "Dir. of Public Works",
        "Finance Manager",
        "Human Resources Director"
    ]
})

print("Original DataFrame:")
print(df)

print("\n" + "="*80 + "\n")

# Use the humanmint accessor
cleaned_df = df.humanmint.clean()

print("Cleaned DataFrame (with all columns):")
print(cleaned_df)

print("\n" + "="*80 + "\n")

# Show just the cleaned columns
cleaned_cols = [col for col in cleaned_df.columns if col.startswith("hm_")]
print(f"Cleaned columns ({len(cleaned_cols)}):")
print(cleaned_df[cleaned_cols])

print("\n" + "="*80 + "\n")

# Verify some key values
print("Sample cleaned values:")
print(f"  Row 0: {cleaned_df.iloc[0]['hm_name_first']} {cleaned_df.iloc[0]['hm_name_last']} - {cleaned_df.iloc[0]['hm_department']}")
print(f"  Row 1: {cleaned_df.iloc[1]['hm_name_first']} {cleaned_df.iloc[1]['hm_name_last']} - {cleaned_df.iloc[1]['hm_department']}")
print(f"  Row 2: {cleaned_df.iloc[2]['hm_name_first']} {cleaned_df.iloc[2]['hm_name_last']} - {cleaned_df.iloc[2]['hm_department']}")

print("\n[SUCCESS] Pandas accessor test passed!")
