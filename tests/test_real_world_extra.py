import sys
import json

sys.path.insert(0, "src")

from humanmint import mint


def test_real_world_extra():
    scenarios = [
        {
            "id": "R11_CITY_PLANNING",
            "note": "City planning dept with internal extension encoding",
            "data": {
                "name": "Anne-Marie D'Angelo",
                "email": "adangelo@springfieldplanning.gov",
                "phone": "413-787-6020 ext. 14",
                "department": "Department of Planning & Development",
                "title": "Senior Planner",
            },
        },
        {
            "id": "R12_FIRE_DEPARTMENT",
            "note": "Fire rank prefix, inconsistent spacing, common in small-town PDFs",
            "data": {
                "name": "  Capt   John   R. Myles ",
                "email": "jmyles@riverfire.org",
                "phone": "(860)5554550",
                "department": "Fire Dept.",
                "title": "Shift Captain",
            },
        },
        {
            "id": "R13_PARKS_AND_REC",
            "note": "Recreation department with slashes and abbreviations",
            "data": {
                "name": "Melissa K. Turner",
                "email": "mturner@parks.wy.gov",
                "phone": "307.555.9211 x33",
                "department": "Parks/Rec – Maintenance",
                "title": "Program Supervisor",
            },
        },
        {
            "id": "R14_IT_DEPARTMENT",
            "note": "IT staff often have unconventional titles",
            "data": {
                "name": "Kyle Svenson",
                "email": "ksvenson@ci.dover.ma.us",
                "phone": "508-555-1199",
                "department": "IT & Digital Services",
                "title": "Systems Admin II",
            },
        },
        {
            "id": "R15_TOWN_TREASURER",
            "note": "Financial role with messy punctuation and abbreviations",
            "data": {
                "name": "Mrs. Linda J. Campbell",
                "email": "lcampbell@townofeden.net",
                "phone": "716 555 0080",
                "department": "Treasurer's Offc.",
                "title": "Asst. Town Treasurer",
            },
        },
        {
            "id": "R16_SHERIFFS_OFFICE",
            "note": "Sheriff dept with rank and badge number inside name",
            "data": {
                "name": "Sgt. Daniel Brooks #172",
                "email": "dbrooks@co.jacksonsd.net",
                "phone": "+1 (517) 555-1212",
                "department": "Sheriff’s Office",
                "title": "Patrol Sergeant",
            },
        },
        {
            "id": "R17_PUBLIC_TRANSPORT",
            "note": "Transit authority with domain mismatch",
            "data": {
                "name": "Carlos E. Rivera",
                "email": "crivera@metrotransitmn.us",
                "phone": "612-555-4400",
                "department": "Transit Operations Division",
                "title": "Operations Coordinator",
            },
        },
        {
            "id": "R18_ECONOMIC_DEVELOPMENT",
            "note": "ED departments have long job titles and multiple org layers",
            "data": {
                "name": "Dr. Helena S. Orlov",
                "email": "helena.orlov@eastcountydev.org",
                "phone": "(301) 555-3344",
                "department": "Office of Economic and Workforce Development",
                "title": "Deputy Director for Small Business Initiatives",
            },
        },
        {
            "id": "R19_HUMAN_RESOURCES",
            "note": "HR titles frequently carry certifications",
            "data": {
                "name": "Brian J. Lopez, SHRM-CP",
                "email": "blopez@citymillertown.com",
                "phone": "928.555.4482",
                "department": "Human Resources Dept.",
                "title": "HR Generalist II",
            },
        },
        {
            "id": "R20_COMMUNITY_DEVELOPMENT",
            "note": "CD role with no title punctuation and camelcased domain",
            "data": {
                "name": "Jade Morrell",
                "email": "jmorrell@CommunityDev.ca.gov",
                "phone": "916-555-9911",
                "department": "Community Development",
                "title": "Housing Program Manager",
            },
        },
    ]

    results = []
    print(f"Running {len(scenarios)} extra real-world scenarios...\n")

    for case in scenarios:
        cleaned = mint(**case["data"])
        results.append(
            {
                "scenario_id": case["id"],
                "input": case["data"],
                "output": cleaned.model_dump(),
            }
        )

    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    test_real_world_extra()
