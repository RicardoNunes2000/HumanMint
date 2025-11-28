import time
import random
from faker import Faker
import sys
from pathlib import Path

# Ensure we can import the library
sys.path.insert(0, "src")

from humanmint import mint, export_json, export_csv

fake = Faker("en_US")

# Realistic US departments
DEPARTMENTS = [
    "Police Department",
    "Fire Department",
    "Department of Public Works",
    "Planning & Zoning",
    "Water & Sewer",
    "Parks & Recreation",
    "City Clerk",
    "Elections",
    "Finance Department",
    "Human Resources",
    "Health Department",
    "Transportation Services",
    "Information Technology",
    "Community Development",
]

# Realistic US titles
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
    "IT Systems Administrator",
    "Deputy Director",
    "Administrative Coordinator",
    "City Clerk",
    "Epidemiologist",
    "Water Engineer",
    "Housing Specialist",
]


def generate_record():
    full_name = fake.name()
    first, last = full_name.split(" ")[0], full_name.split(" ")[-1]

    # Random gov domain
    domain = random.choice(
        [
            f"{fake.city().replace(' ', '').lower()}.gov",
            f"{fake.city().replace(' ', '').lower()}-{fake.word()}.gov",
            f"{fake.city().replace(' ', '').lower()}.us",
        ]
    )

    email = f"{first.lower()}.{last.lower()}@{domain}"

    phone = fake.phone_number()

    department = random.choice(DEPARTMENTS)
    title = random.choice(TITLES)

    return {
        "name": full_name,
        "email": email,
        "phone": phone,
        "department": department,
        "title": title,
    }


def main():
    N = 5000
    print(f"Generating and processing {N} records...")

    records = [generate_record() for _ in range(N)]

    start = time.perf_counter()
    results = [mint(**r) for r in records]
    end = time.perf_counter()

    total_ms = (end - start) * 1000
    avg_ms = total_ms / N

    print(f"\n=== SAMPLE OUTPUTS ===")
    for i in range(5):
        print(f"\n--- Record #{i + 1} ---")
        print(results[i].model_dump())

    print("\n=== PERFORMANCE ===")
    print(f"Total time: {total_ms:.2f} ms")
    print(f"Avg per record: {avg_ms:.4f} ms")

    # Export results to root folder
    root_dir = Path(__file__).parent.parent
    json_file = root_dir / "department_edge_cases_results.json"
    csv_file = root_dir / "department_edge_cases_results.csv"

    print("\n=== EXPORTING RESULTS ===")
    export_json(results, str(json_file))
    print(f"Exported JSON: {json_file}")

    export_csv(results, str(csv_file), flatten=True)
    print(f"Exported CSV: {csv_file}")

    print("\nDone.")


if __name__ == "__main__":
    main()
