"""
Manual address normalization smoke test.

Run directly:
    python tests/test22.py
"""

import sys
from pprint import pprint

# Ensure local src/ is importable when run directly
sys.path.insert(0, "src")

from humanmint import mint


def main() -> None:
    sample_addresses = [
        "123 N. Main St Apt #4B, Springfield, MA 01103",
        "500 5th Ave, New York NY 10110",
        "42 Wallaby Way, Sydney NSW",
        "1600 Pennsylvania Ave NW, Washington, DC 20500",
        "1 Infinite Loop, Cupertino, CA",
    ]

    for raw in sample_addresses:
        result = mint(address=raw)
        print(f"Raw: {raw}")
        pprint(result.address)
        print("-" * 60)


if __name__ == "__main__":
    main()
