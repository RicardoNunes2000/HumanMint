import sys

sys.path.insert(0, "src")

from humanmint import mint


TEST_RECORDS = [
    {
        "name": "Michael J. Barrett",
        "email": "mbarrett@springfieldma.gov",
        "phone": "(413) 787-6100",
        "department": "Department of Public Works",
        "title": "Deputy Director",
    },
    {
        "name": "Sarah L. Ramirez",
        "email": "sramirez@cityofsalinas.org",
        "phone": "831-758-7201",
        "department": "Community Development Department",
        "title": "Senior Planner",
    },
    {
        "name": "James O'Brien",
        "email": "jobrien@newtonma.gov",
        "phone": "617-796-1000",
        "department": "Finance Department",
        "title": "Chief Financial Officer",
    },
    {
        "name": "Rebecca S. Chen",
        "email": "rchen@seattle.gov",
        "phone": "(206) 684-8600",
        "department": "Office of Sustainability & Environment",
        "title": "Environmental Analyst",
    },
    {
        "name": "David A. Thompson",
        "email": "dthompson@cityofmadison.com",
        "phone": "608-266-4751",
        "department": "Parks & Recreation",
        "title": "Recreation Supervisor",
    },
    {
        "name": "Melissa K. Andrews",
        "email": "mandrews@charlottenc.gov",
        "phone": "704-336-7600",
        "department": "Charlotte Water",
        "title": "Engineering Manager",
    },
    {
        "name": "Jonathan P. Lopez",
        "email": "jlopez@houstontx.gov",
        "phone": "(713) 837-0311",
        "department": "Houston Public Works",
        "title": "Water Engineer",
    },
    {
        "name": "Karen D. Walker",
        "email": "kwalker@sandiego.gov",
        "phone": "619-236-5555",
        "department": "City Treasurer",
        "title": "Accounting Supervisor",
    },
    {
        "name": "Joseph T. Kim",
        "email": "jkim@lacity.org",
        "phone": "213-978-1133",
        "department": "Information Technology Agency",
        "title": "IT Systems Administrator",
    },
    {
        "name": "Laura M. Pearson",
        "email": "lpearson@boston.gov",
        "phone": "617-635-4500",
        "department": "Inspectional Services",
        "title": "Building Inspector",
    },
]


def main():
    print("=== REAL-WORLD NORMAL TESTS ===")

    for idx, rec in enumerate(TEST_RECORDS, start=1):
        print(f"\n--- RECORD {idx} ---")
        result = mint(**rec)
        print(result.model_dump())


if __name__ == "__main__":
    main()
