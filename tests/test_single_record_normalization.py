"""
Manual bulk smoke runner with optional rich progress (enabled inside bulk()).

Usage:
    python tests/test20.py
"""

import sys
import time
from faker import Faker

# Ensure local src/ is importable when run directly
sys.path.insert(0, "src")

from humanmint import bulk


def run_bulk_20k(workers: int = 8):
    faker = Faker()
    faker.seed_instance(2025)
    total = 20_000

    records = [
        {
            "name": faker.name(),
            "email": faker.email(),
            "phone": faker.phone_number(),
            "department": faker.job(),
            "title": faker.job(),
        }
        for _ in range(total)
    ]

    start = time.time()
    results = bulk(records, workers=workers, progress="rich")
    elapsed = time.time() - start
    print(f"Processed {len(results)} records in {elapsed:.2f}s")
    print(f"Sample normalized record: {results[0] if results else None}")


if __name__ == "__main__":
    run_bulk_20k()
