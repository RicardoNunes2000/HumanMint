import sys

sys.path.insert(0, "src")

from humanmint import mint

# The "Dirty 5" - Real-world messy data scenarios
scenarios = [
    {
        "id": 1,
        "type": "Civic/Gov Data (Your Niche)",
        "data": {
            "name": "OFC. ROBERT 'BOB' JONES",
            "email": "BOB.JONES@POLICE.CI.OMAHA.NE.US",
            "department": "050 - Pub. Safety / Police Dept",
            "title": "SGT.",
        },
    },
    {
        "id": 2,
        "type": "Messy Typos & Formatting",
        "data": {
            "name": "mr. john smith, esq.",
            "phone": "555.123.4567 x 101",
            "department": "Water & Swr",
            "title": "Director of operations",
        },
    },
    {
        "id": 3,
        "type": "Incomplete/Ambiguous Data",
        "data": {
            "name": "J. Doe",
            "email": "info@gmail.com",
            "department": "Rec Center",
            "title": "Head Coach",
        },
    },
    {
        "id": 4,
        "type": "Garbage/System Data",
        "data": {
            "name": "### TEMP USER ###",
            "email": "admin+test@company.com",
            "department": "Cost Center 4401",
            "title": "N/A",
        },
    },
    {
        "id": 5,
        "type": "International Format",
        "data": {
            "name": "Andréa Müller",
            "phone": "+44 20 7946 0958",
            "email": "andrea@company.co.uk",
            "department": "IT Ops",
        },
    },
]

print(
    f"{'ID':<3} | {'HUMANMINT OUTPUT (NORMALIZED)':<45} | {'PAID API (TYPICAL OUTPUT)'}"
)
print("-" * 100)

for s in scenarios:
    res = mint(**s["data"], aggressive_clean=True)

    print(res)

    print(f"SCENARIO {s['id']}: {s['type']}")
    print(f"INPUT: {s['data']}")
    print("-" * 40)
    print("-" * 40)
    print("\n")
