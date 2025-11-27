import time
import random
from faker import Faker
import sys

# Ensure local src/ is importable so we can run without installing
sys.path.insert(0, "src")

# Importing humanmint automatically registers the pandas accessor
import humanmint

fake = Faker("en_US")

# ---------------------------
# Real-world seeds (normal)
# ---------------------------
REAL_NORMAL = [
    {
        "name": "Michael J. Barrett",
        "email": "mbarrett@springfieldma.gov",
        "phone": "(413) 787-6100",
        "department": "Department of Public Works",
        "title": "Deputy Director",
    },
    {
        "name": "Sarah Ramirez",
        "email": "sramirez@cityofsalinas.org",
        "phone": "831-758-7201",
        "department": "Community Development Department",
        "title": "Senior Planner",
    },
    {
        "name": "Karen Walker",
        "email": "kwalker@sandiego.gov",
        "phone": "619-236-5555",
        "department": "City Treasurer",
        "title": "Accounting Supervisor",
    },
]

# ---------------------------
# Real messy gov-style seeds
# ---------------------------
REAL_MESSY = [
    {
        "name": "### TEMP ### MR JOHN Q PUBLIC ; DROP TABLES",
        "email": " JOHN.PUBLIC@CITYOFSPRINGFIELD.GOV  ",
        "phone": "(413) 787-6020 ext. 14",
        "department": "0020 - Publíc Wørks Div. 413-555-1212",
        "title": "Sr. Managér - PW",
    },
    {
        "name": "Capt. Maria L. De Souza",
        "email": "M.L.DE.SOUZA@PD.HOUSTONTX.GOV ",
        "phone": "+1 (713) 555-9812 x99",
        "department": "Hou Public Wrks",
        "title": "Captain",
    },
    {
        "name": "Lt. Вікто́р Novak",
        "email": "VNOVAK@SHERIFF.ORG",
        "phone": "512.555.1002 ext 5",
        "department": "Sheriff’s Off.",
        "title": "Lieutenant",
    },
]

# ---------------------------
# Department & title pools
# ---------------------------
DEPARTMENTS = [
    "Public Works",
    "Police Department",
    "Fire Department",
    "Planning & Zoning",
    "Water & Sewer",
    "Parks & Recreation",
    "Information Technology",
    "Finance Department",
    "City Clerk",
    "Elections",
    "Human Resources",
    "Houston Public Works",
    "Inspectional Services",
    "Office of Sustainability & Environment",
]

TITLES = [
    "Chief of Police",
    "Police Officer",
    "Fire Chief",
    "Captain",
    "Lieutenant",
    "Planner",
    "Senior Planner",
    "HR Manager",
    "Finance Analyst",
    "Budget Analyst",
    "Network Engineer",
    "Deputy Director",
    "Administrative Coordinator",
    "City Clerk",
    "Epidemiologist",
    "Water Engineer",
    "Housing Specialist",
]


# ---------------------------
# Generate synthetic realistic data
# ---------------------------
def generate_faker_record():
    full_name = fake.name()
    first, last = full_name.split(" ")[0], full_name.split(" ")[-1]

    domain = random.choice(
        [
            f"{fake.city().replace(' ', '').lower()}.gov",
            f"{fake.city().replace(' ', '').lower()}.us",
            f"{fake.city().replace(' ', '').lower()}-{fake.word()}.gov",
        ]
    )

    email = f"{first.lower()}.{last.lower()}@{domain}"
    phone = fake.phone_number()

    return {
        "name": full_name,
        "email": email,
        "phone": phone,
        "department": random.choice(DEPARTMENTS),
        "title": random.choice(TITLES),
    }


# ---------------------------
# Mild corruption injector
# ---------------------------
def corrupt(record):
    r = record.copy()

    # Random casing
    if random.random() < 0.4:
        r["name"] = r["name"].upper()
    if random.random() < 0.4:
        r["email"] = r["email"].lower()

    # Random extra spaces
    if random.random() < 0.3:
        r["name"] = "   " + r["name"] + "   "
    if random.random() < 0.3:
        r["department"] = r["department"] + "  "

    # Random punctuation noise
    if random.random() < 0.2:
        r["department"] = r["department"] + "  (Ref#1001)"

    return r


# ---------------------------
# Build final dataset
# ---------------------------
def build_dataset(n=10000):
    dataset = []

    # Include real normal
    dataset.extend(REAL_NORMAL)

    # Include real messy
    dataset.extend(REAL_MESSY)

    # Faker + corruption
    for _ in range(n - len(dataset)):
        base = generate_faker_record()
        if random.random() < 0.4:
            base = corrupt(base)
        dataset.append(base)

    random.shuffle(dataset)
    return dataset


# ---------------------------
# Benchmark runner
# ---------------------------
def main():
    N = 10000  # change to 20000+ if you want torture mode
    print(f"Generating {N} mixed records...")

    records = build_dataset(N)

    print("Running HumanMint mint() on all records...")
    start = time.perf_counter()
    results = [humanmint.mint(**r) for r in records]
    end = time.perf_counter()

    total_ms = (end - start) * 1000
    avg_ms = total_ms / N

    print("\n=== SAMPLE OUTPUTS (150) ===")
    for i in range(100):
        print(f"\n--- Record #{i + 1} ---")
        print(results[i].model_dump())

    print("\n=== PERFORMANCE ===")
    print(f"Total time: {total_ms:.2f} ms")
    print(f"Avg per record: {avg_ms:.4f} ms")
    print(f"Throughput: ~{int(1000 / avg_ms)} records/sec")

    print("\nDone.")


if __name__ == "__main__":
    main()
