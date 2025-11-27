import sys
import json
from pathlib import Path

# Add ./src to path
sys.path.insert(0, "src")

from humanmint import mint


def test_extreme_cases():
    scenarios = [
        {
            "id": "X1_MIXED_SCRIPT",
            "note": "Unicode mixing, Cyrillic letters inside a name, malformed title",
            "data": {
                "name": "Аlеx Johnson",  # Two letters are Cyrillic lookalikes
                "email": "alex.j@example.com ",
                "phone": "+1 (415) 555-0199 ext 12",
                "department": "0020 - Publíc Wørks Div.",
                "title": "Sr. Managér - PW",
            },
        },
        {
            "id": "X2_PDF_COPY_PASTE_HORROR",
            "note": "Random whitespace, hidden chars, phone embedded w/ department",
            "data": {
                "name": "  Dr.\u200b Sarah   L.   Kane   ",
                "email": "SARAH..KANE@CITY.GOV",
                "phone": "(202)5550101 x 78",
                "department": "Public Works (Main) - 202 555 0101",
                "title": "Dir of Operations (PW)",
            },
        },
        {
            "id": "X3_MUNICIPAL_DUMP",
            "note": "Full municipal style: long subdomain, legal codes, role account email",
            "data": {
                "name": "Lt. Mark O’Donnell",
                "email": "dispatch@police.city.town.ma.gov",
                "phone": "508-555-0000",
                "department": "Chapter 4.12.010 - Police Div.",
                "title": "Shift Commander",
            },
        },
        {
            "id": "X4_THE_MINIMALIST",
            "note": "Barely any real data, but still should not crash",
            "data": {
                "name": "Li",
                "email": "   ",
                "phone": "555",
                "department": "",
                "title": None,
            },
        },
        {
            "id": "X5_SPECIAL_EDU_CONTACT",
            "note": "Education-specific, noisy title, nickname in name",
            "data": {
                "name": "Beth ‘Liz’ Thompson",
                "email": "liz.thompson@district.k12.ca.us",
                "phone": "+1 650-253-0000",
                "department": "Special Ed   ",
                "title": "Asst. Director – Special Education",
            },
        },
        {
            "id": "X6_FIRE_AND_POLICE_MIX",
            "note": "Both departments mentioned. Should pick the dominant one.",
            "data": {
                "name": "James Carter",
                "email": "jcarter@city-fire-police.gov",
                "phone": "1-800-555-0100",
                "department": "Police / Fire / Emergency Mgt",
                "title": "Responder Lieutenant",
            },
        },
        {
            "id": "X7_INTERNATIONAL_CONTACT",
            "note": "International name, phone, accents, weird title punctuation",
            "data": {
                "name": "François Delacroix",
                "email": "   francois.delacroix@ville.fr",
                "phone": "+33 1 44 55 66 77",
                "department": "Urbanisme et Développement",
                "title": "Ingénieur Principal",
            },
        },
        {
            "id": "X8_CORRUPT_DATA_STRUCTURES",
            "note": "Bad department, nonsense phone, broken email but should not crash",
            "data": {
                "name": "N/A",
                "email": "??invalid@@@",
                "phone": "12345abc678",
                "department": "___---???",
                "title": "Employee",
            },
        },
        {
            "id": "X9_HARDCORE_COPS",
            "note": "Police dataset style codes & rank prefixes",
            "data": {
                "name": "Det. John R. McLane",
                "email": "jmclane@nyc.gov",
                "phone": "(917) 555-0123",
                "department": "NYPD / Precinct 12 Div.",
                "title": "Detective II",
            },
        },
        {
            "id": "X10_HEALTHCARE_COMPLEX",
            "note": "Healthcare contact with credentials and unclear job title",
            "data": {
                "name": "Dr. Melissa Varga, MD MPH",
                "email": "mvarga@countyhealth.us",
                "phone": "+1-303-555-0115",
                "department": "County Health & Human Svcs.",
                "title": "Dir. Clinical Ops.",
            },
        },
    ]

    results = []

    print(f"Running {len(scenarios)} extreme scenarios...\n")

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
    test_extreme_cases()
