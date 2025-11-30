import json
import sys
from pathlib import Path

# Add ./src to path
sys.path.insert(0, "src")

from humanmint import mint


def test_government_nightmare_cases():
    scenarios = [
        {
            "id": "CASE_A_BAD_CRM_EXPORT",
            "note": "Name contains HTML, phone in name, email inside department",
            "data": {
                "name": "<b>Mrs. Linda  Parker</b> (Cell: 555-0202)",
                "email": "lparker@town.gov",
                "phone": "(502) 555-0202",
                "department": "Clerk Office - reach me at linda.parker@town.gov",
                "title": "Deputy Clerk",
            },
        },
        {
            "id": "CASE_B_INTERNAL_CODES",
            "note": "Department full of internal finance codes",
            "data": {
                "name": "Aaron Smith",
                "email": "asmith@city.gov",
                "phone": "720.555.0100",
                "department": "##001300##FIN-SVCS##AP##",
                "title": "Accounts Payable Specialist",
            },
        },
        {
            "id": "CASE_C_MIDDLE_INITIAL_MESS",
            "note": "Weird spacing, suffix inside email-like string",
            "data": {
                "name": "ROBERT   T  JONES  JR.",
                "email": "robert.t.jones.jr@publicworks.gov",
                "phone": "+1-303-555-3322 ext 901",
                "department": "Public Works (Streets Div)",
                "title": "Street Maintenance Supv.",
            },
        },
        {
            "id": "CASE_D_WEIRD_PHONE",
            "note": "Extension spelled as EXTENSION, phone embedded in title",
            "data": {
                "name": "Maria Lopes",
                "email": "mlopes@county.gov",
                "phone": "555-1234 EXTENSION 77",
                "department": "Health Services",
                "title": "Lead Nurse (303-555-4411)",
            },
        },
        {
            "id": "CASE_E_CITY_HALL_SPECIAL",
            "note": "Name is position, random Unicode, impossible phone",
            "data": {
                "name": "CITY MANAGER ✨",
                "email": "citymanager@hall.gov",
                "phone": "0000000000",
                "department": "City Manager Office",
                "title": "City Manager",
            },
        },
        {
            "id": "CASE_F_EMAIL_TAGS_AND_PLUS",
            "note": "Email with +tag and department typo",
            "data": {
                "name": "Emily Rose",
                "email": "emily.rose+alerts@citygov.gov",
                "phone": "(612) 555-9933",
                "department": "Parks & Recration",
                "title": "Program Coordinator",
            },
        },
        {
            "id": "CASE_G_TITLE_IN_EMAIL",
            "note": "Email local part includes job title, weird hyphenation",
            "data": {
                "name": "Thomas Reed",
                "email": "treed-supervisor@city.gov",
                "phone": "+1 818 555 2717",
                "department": "Solid Waste Mgmt.",
                "title": "Operations Supervisor",
            },
        },
        {
            "id": "CASE_H_JUST_GARBAGE",
            "note": "Everything is garbage but still somewhat parseable",
            "data": {
                "name": "##TEMP##X Æ A-12--??",
                "email": "x12@@gov..us",
                "phone": "xyz 123",
                "department": "000 --- UNKNOWN",
                "title": "???",
            },
        },
        {
            "id": "CASE_I_BUILDING_NAME_DEPT",
            "note": "Department is actually building location",
            "data": {
                "name": "Janice Moore",
                "email": "jmoore@fire.city.gov",
                "phone": "+1 602 555 7711",
                "department": "Station #14 - Ladder Unit",
                "title": "Firefighter",
            },
        },
        {
            "id": "CASE_J_FREE_PROVIDER_OFFICIAL",
            "note": "Official email from Gmail, rank prefix, noise in title",
            "data": {
                "name": "Lt. Daniel Perez",
                "email": "danperez.city@gmail.com",
                "phone": "+1 785 555 1988",
                "department": "Police",
                "title": "Lt. / Ops",
            },
        },
    ]

    results = []

    print(f"Running {len(scenarios)} nightmare scenarios...\n")

    for case in scenarios:
        cleaned = mint(**case["data"])
        results.append(
            {
                "scenario_id": case["id"],
                "note": case["note"],
                "input": case["data"],
                "output": cleaned.model_dump(),
            }
        )

    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    test_government_nightmare_cases()
