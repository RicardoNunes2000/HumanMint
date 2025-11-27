import sys
import time
import random
import pandas as pd
import statistics
from typing import List, Dict

# Ensure we can import the library
sys.path.insert(0, "src")

# We import inside the timing function to measure "Cold Start"
import humanmint


def generate_dataset(n: int) -> List[Dict]:
    """Generates N rows of messy data to stress-test the library."""

    first_names = [
        "John",
        "Jane",
        "Robert",
        "Michael",
        "William",
        "David",
        "Richard",
        "Joseph",
        "Thomas",
        "Charles",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Miller",
        "Davis",
        "Garcia",
        "Rodriguez",
        "Wilson",
    ]

    titles = [
        "Chief of Police",
        "Dir. Public Works",
        "Admin Asst",
        "Sr. Manager",
        "Ofc. Manager",
        "Unknown",
        "VP of Sales",
        "Clerk II",
        "Sheriff Deputy",
    ]

    departments = [
        "001-Police Dept",
        "Public Works - Streets",
        "Finance & Admin",
        "Human   Resources",
        "Water/Sewer/Trash",
        "Parks and Rec",
        "Office of the Mayor",
        "IT Dept",
        "Health & Safety",
        "Zoning Bd",
    ]

    phones = [
        "(555) 123-4567",
        "555.987.6543",
        "+1 555 000 1111",
        "555-123-4567 x101",
        "1234567890",
    ]

    data = []
    for _ in range(n):
        # Randomly dirty the data
        name = f"{random.choice(['Dr.', 'Mr.', '', ''])} {random.choice(first_names)} {random.choice(last_names)} {random.choice(['PhD', 'Jr.', ''])}"

        # Occasional garbage/SQL injection simulation
        if random.random() < 0.05:
            name = f"{name}; DROP TABLE users"

        row = {
            "full_name": name.strip(),
            "email": f"{random.choice(first_names)}.{random.choice(last_names)}@city.gov".upper(),
            "phone": random.choice(phones),
            "department": random.choice(departments),
            "job_title": random.choice(titles),
        }
        data.append(row)
    return data


def benchmark_cold_start():
    print("\n--- 1. Cold Start / Import Overhead ---")
    start_time = time.perf_counter()

    # Force a reload of internal data structures
    # This simulates the first time a user runs the script
    humanmint.departments.data_loader._mappings_cache = None
    humanmint.emails.normalize._GENERIC_INBOXES_CACHE = None
    humanmint.emails.classifier._FREE_PROVIDERS_CACHE = None
    humanmint.names.enrichment._gender_cache = None

    # Run one mint to trigger lazy loading
    humanmint.mint(name="Test")

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Time to load caches and process first item: {duration:.4f} seconds")

    if duration < 1.0:
        print("✅ Rating: EXCELLENT (<1s)")
    elif duration < 3.0:
        print("⚠️ Rating: ACCEPTABLE (<3s)")
    else:
        print("❌ Rating: SLOW (>3s) - Check your GZIP loading efficiency")


def benchmark_pure_python_loop(n=1000):
    print(f"\n--- 2. Pure Python Loop ({n} records) ---")
    data = generate_dataset(n)

    start_time = time.perf_counter()

    for row in data:
        humanmint.mint(
            name=row["full_name"],
            email=row["email"],
            phone=row["phone"],
            department=row["department"],
            title=row["job_title"],
        )

    end_time = time.perf_counter()
    duration = end_time - start_time
    per_second = n / duration

    print(f"Total time: {duration:.4f} seconds")
    print(f"Speed: {per_second:.0f} records/second")


def benchmark_pandas(n=50000):
    print(f"\n--- 3. Pandas Batch Processing ({n} records) ---")
    print(f"Generating {n} rows of synthetic data...")
    data = generate_dataset(n)
    df = pd.DataFrame(data)

    print("Starting processing...")
    start_time = time.perf_counter()

    # Use your accessor
    _ = df.humanmint.clean(
        name_col="full_name",
        email_col="email",
        phone_col="phone",
        dept_col="department",
        title_col="job_title",
    )

    end_time = time.perf_counter()
    duration = end_time - start_time
    per_second = n / duration

    print(f"Total time: {duration:.4f} seconds")
    print(f"Speed: {per_second:.0f} records/second")

    # Verdict logic
    if per_second > 2000:
        print("🚀 Rating: BLAZING FAST (>2k/sec)")
    elif per_second > 500:
        print("✅ Rating: PRODUCTION READY (>500/sec)")
    else:
        print("⚠️ Rating: NEEDS OPTIMIZATION (<500/sec)")


def benchmark_caching_impact(n=5000):
    print(f"\n--- 4. Caching Effectiveness (LRU Cache) ---")
    # Use a small set of repeated data to test lru_cache
    repeats = 5
    data = generate_dataset(n // repeats) * repeats

    start_time = time.perf_counter()
    for row in data:
        humanmint.mint(department=row["department"])
    end_time = time.perf_counter()

    print(f"Processed {len(data)} items (high duplication)")
    print(f"Time: {end_time - start_time:.4f} seconds")
    print(
        "Note: If this is significantly faster than the random loop, your @lru_cache is working."
    )


if __name__ == "__main__":
    print("=" * 60)
    print("HUMANMINT PERFORMANCE BENCHMARK")
    print(f"Python Version: {sys.version.split()[0]}")
    print("=" * 60)

    benchmark_cold_start()
    benchmark_pure_python_loop(2000)
    benchmark_caching_impact(10000)

    # The big test
    try:
        benchmark_pandas(50000)
    except ImportError:
        print("\nPandas not installed, skipping Pandas benchmark.")
    except Exception as e:
        print(f"\nPandas benchmark failed: {e}")
