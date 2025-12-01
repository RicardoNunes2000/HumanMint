import sys

# Ensure we can import the library
sys.path.insert(0, "src")

from humanmint import mint


def show(label, value):
    print(f"\n=== {label} ===")
    print(value)


def main():
    # 1. Fully messy real-world record
    r1 = mint(
        name="### TEMP ### MR JOHN Q PUBLIC ; DROP TABLES",
        email=" JOHN.PUBLIC@CITYOFSPRINGFIELD.GOV  ",
        phone="(413) 787-6020 ext. 14",
        department="0020 - Publíc Wørks Div. 413-555-1212",
        title="Sr. Managér - PW",
    )
    show("Messy government record", r1.model_dump())

    # 2. Missing fields + single name + rare first name
    r2 = mint(
        name="Al",
        email=None,
        phone="555.123.9999 x200",
        department="Water & Wastewater (District 7)",
        title=None,
    )
    show("Minimal data + short name", r2.model_dump())

    # 3. Non-ASCII + mixed scripts + hyphens
    r3 = mint(
        name="Мария-Thompson",
        email="MARIA.T@example.COM",
        phone="+1 202 555 8888",
        department="Códé Enfôrcemént",
        title="Deputy Chief Code Officer",
    )
    show("Unicode names + mixed dept accents", r3.model_dump())

    # 4. Corporate-style messy data
    r4 = mint(
        name="John-Michael O’Reilly Jr.",
        email="jm.oreilly@Example.ORG",
        phone="202 555 0000",
        department="Human Capital Mgmt / HR / Talent",
        title="Asst. Director, HR Strategy",
    )
    show("Corporate record", r4.model_dump())

    # 5. Edge-case: no name, no title, only email
    r5 = mint(
        name=None,
        email="unknown.user@SOMECITY.gov",
        phone=None,
        department=None,
        title=None,
    )
    show("Email-only record", r5.model_dump())


if __name__ == "__main__":
    main()
