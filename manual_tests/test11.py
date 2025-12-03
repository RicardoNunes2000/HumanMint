import sys

sys.path.insert(0, "src")


from humanmint import mint
import time

# ==========================================
# LEVEL 1: THE "CULTURAL" GAUNTLET
# US-centric parsers usually die here.
# ==========================================
level_1_culture = [
    # Spanish Compound Surnames (Should not split "De La" as middle name)
    {"name": "Maria de la Luz Garcia"},
    # Irish/Scottish (Apostrophes often break capitalization logic -> O'neil)
    {"name": "Seamus O'Reilly-Smythe"},
    # Asian Name Ordering (Is it First: Li, Last: Wei? Or vice versa?)
    {"name": "Wei Li"},
    # The "Suffix Nightmare" (Multiple generations)
    {"name": "Thurston Howell III, Esq."},
    # Mononyms (Cher, Zendaya - common in arts departments)
    {"name": "Prince"},
]

# ==========================================
# LEVEL 2: THE "PASSIVE AGGRESSIVE CLERK"
# Humans putting notes where names should be.
# ==========================================
level_2_human_error = [
    # The "Helpful" Note
    {"name": "John Smith (Do Not Contact)"},
    # The "Role" in the Name field
    {"name": "Sheriff David Clarke"},
    # The "Interim" status in the Name field
    {"name": "Interim Director Sarah Connor"},
    # The "Dead" Record
    {"name": "Robert Paulson (Deceased)"},
    # The "Spouse" entry
    {"name": "Mrs. John Doe"},  # Should ideally extract "John Doe" or handle gracefully
]

# ==========================================
# LEVEL 3: THE "DATA POISONING"
# OCR errors, encoding issues, and formatting garbage.
# ==========================================
level_3_dirty_data = [
    # Bad Encoding (Mojibake)
    {"name": "RenÃ© Descartes"},
    # All Punctuation
    {"name": "---"},
    # The "Spreadsheet Slip" (Email in name field)
    {"name": "bob@city.gov"},
    # The "PDF Scrape Artifact"
    {"name": "1.  Alice Johnson"},
    # Invisible characters & Non-breaking spaces
    {"name": "Kyle\u00a0Reese"},
]

# ==========================================
# LEVEL 4: THE "LOGIC TRAP"
# Titles that sound like Departments, and Depts that sound like Titles.
# ==========================================
level_4_logic = [
    # Is "Clerk of the Works" a person or a department?
    {"title": "Clerk of the Works", "department": "Construction"},
    # "General" is a rank, "General Counsel" is a lawyer.
    {"name": "General George Patton", "title": "General"},
    {"name": "David Souter", "title": "General Counsel"},
    # "Sergeant at Arms" vs "Sergeant"
    {"title": "Sgt-at-Arms"},
    # The "Assistant to the Regional Manager" (Recursive titles)
    {"title": "Exec. Asst. to the Deputy Dir. of Ops."},
]

# ==========================================
# LEVEL 5: THE "ABSURD" (EDGE OF SANITY)
# Security risks, buffer overflows, and nonsense.
# ==========================================
long_string = "John " + "Smith " * 500  # 3000+ characters

level_5_absurd = [
    # SQL Injection Attempt (Did he sanitize inputs?)
    {"name": "Robert'); DROP TABLE students;--"},
    # Script Injection (XSS)
    {"name": "<script>alert('xss')</script>"},
    # The "Buffer Overflow" Test
    {"name": long_string},
    # The "Zero Width" Attack
    {"name": "J\u200bo\u200bh\u200bn"},
    # The "Recursive Department"
    {"department": "Dept of the Dept of Public Works Dept"},
]

all_levels = [
    ("Level 1: Cultural", level_1_culture),
    ("Level 2: Human Error", level_2_human_error),
    ("Level 3: Dirty Data", level_3_dirty_data),
    ("Level 4: Logic Traps", level_4_logic),
    ("Level 5: The Absurd", level_5_absurd),
]

print("Running 5-Stage Torture Test...\n")

for level_name, cases in all_levels:
    print(f"\n{'=' * 10} {level_name} {'=' * 10}")
    for raw in cases:
        try:
            start = time.time()
            # Run the library
            r = mint(**raw)
            end = time.time()

            # Prepare display string
            input_str = f"{raw.get('name') or raw.get('title')}"
            output_name = f"Name: '{r.name_standardized}'" if raw.get("name") else ""
            output_title = f"Title: '{r.title_canonical}'" if raw.get("title") else ""

            print(f"IN:  {input_str[:50]}...")
            print(
                f"OUT: {output_name} {output_title} (Took {(end - start) * 1000:.2f}ms)"
            )

        except Exception as e:
            print(f"❌ CRASHED on: {raw} \n   Error: {e}")
