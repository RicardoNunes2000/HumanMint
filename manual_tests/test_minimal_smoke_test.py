import sys
from pprint import pprint

# Ensure local src/ is importable when run directly
sys.path.insert(0, "src")

from humanmint import mint


def main() -> None:
    record = mint(
        name="Laura M. Johnson",
        email="laura.johnson@cityofmadison.com",
        phone="(608) 266-4751 x204",
        department="Department of Public Works",
        title="Senior Civil Engineer",
        address="123 N. Main St Apt 4B, Madison, WI 53703",
    )

    print(record)
    pprint(record.model_dump())


if __name__ == "__main__":
    main()
