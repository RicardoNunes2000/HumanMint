import sys

sys.path.insert(0, "src")

from humanmint import mint

SCENARIOS = [
    # -------------------------
    # 1–10 REAL-WORLD NORMAL
    # -------------------------
    {
        "name": "Dr. John A. Smith, PhD",
        "email": "JOHN.SMITH@CITY.GOV",
        "phone": "(202) 555-0173",
        "address": "123 Main St, Springfield, IL 62701",
        "department": "Public Works",
        "title": "Chief of Police",
    },
    {
        "name": "Anne Marie Johnson",
        "email": "am.johnson@co.springfield.org",
        "phone": "413-787-6541 ext. 12",
        "address": "44 Park Ave, Springfield MA",
        "department": "Planning & Development",
        "title": "Senior Planner",
    },
    {
        "name": "Robert 'Bobby' Lee",
        "email": "BLEE@TOWNOFGREENVILLE.COM",
        "phone": "864.467.4490",
        "address": "100 North St, Greenville SC",
        "department": "Fire Department",
        "title": "Fire Chief",
    },
    {
        "name": "Tiffany O’Malley",
        "email": "tmalley@boston.gov",
        "phone": "617-635-4500",
        "address": "1 City Hall Square, Boston MA",
        "department": "Parks and Recreation",
        "title": "Recreation Coordinator",
    },
    {
        "name": "Miguel de la Cruz",
        "email": "m.delacruz@miamidade.gov",
        "phone": "(305) 555-0034",
        "address": "200 NW 2nd Ave, Miami FL",
        "department": "Transportation and Public Works",
        "title": "Transit Supervisor",
    },
    # -------------------------
    # 11–20 HARDER BUT CLEAN
    # -------------------------
    {
        "name": "Lt. Sarah-Kate O'Connor",
        "email": "SKOCONNOR@CITYOFSALem.org",
        "phone": "503-588-6123",
        "address": "555 Liberty St SE, Salem OR",
        "department": "Police Dept",
        "title": "Lieutenant",
    },
    {
        "name": "Jonathan (Jon) M. Perry",
        "email": "jon.perry@lakecountyil.gov",
        "phone": "847-377-2600",
        "address": "18 N County St, Waukegan IL",
        "department": "Health Department",
        "title": "Epidemiologist",
    },
    {
        "name": "Mary-Lou Ruiz",
        "email": "mruiz@sf.gov",
        "phone": "415-554-4000",
        "address": "1 Dr Carlton B Goodlett Pl, San Francisco CA",
        "department": "City Attorney Office",
        "title": "Deputy City Attorney",
    },
    {
        "name": "Capt. John 'Jack' Reynolds",
        "email": "JREYNOLDS@BPD.GOV",
        "phone": "617-343-4500",
        "address": "One Schroeder Plaza, Boston MA",
        "department": "Police",
        "title": "Captain",
    },
    {
        "name": "Alicia D. Torres",
        "email": "alicia.torres@houstontx.gov",
        "phone": "832-395-3000",
        "address": "901 Bagby St, Houston TX",
        "department": "Solid Waste Management",
        "title": "Division Manager",
    },
    # -------------------------
    # 21–30 MESSY DATA
    # -------------------------
    {
        "name": "### TEMP ### MR JOHN Q PUBLIC",
        "email": "PUBLIC123@CITY.GOV",
        "phone": "2025550188???",
        "address": "?? 123 Main St, ??? Springfield, IL",
        "department": "PUBLIC WORKS 850-123-1234 ext 200",
        "title": "Interim Director",
    },
    {
        "name": "MRS. LINDA   MC   DONALD",
        "email": "linda.mcdonald@town.org",
        "phone": "207 - 555 - 9981",
        "address": "4 Oak Road,,,, Portland ME",
        "department": "Town Clerk Office",
        "title": "CLERK",
    },
    {
        "name": "john doe",
        "email": "   JOHN.DOE@EXAMPLE.COM   ",
        "phone": "555-5555",
        "address": "123 nowhere",
        "department": "hr",
        "title": "boss",
    },
    {
        "name": "Mr.   Karl-Heinz von Wittgenstein",
        "email": "kvw@munich.gov",
        "phone": "+49 (89) 233-00",
        "address": "Marienplatz 1, Munich",
        "department": "Department of Cultural Affairs",
        "title": "Deputy Director of Arts",
    },
    {
        "name": "Dr..Dr.. Sarah  Müller",
        "email": "s.mueller@@berlin.de",
        "phone": "(030) 000-000",
        "address": "Berlin",
        "department": "Umwelt & Klima",
        "title": "Wissenschaftliche Mitarbeiterin",
    },
    {
        "name": "Mr Robert   Jr. Brown Jr",
        "email": "rbrown@atlantaga.gov",
        "phone": "404.330.6200",
        "address": "55 Trinity Ave, Atlanta GA",
        "department": "Water & Sewer 203-222-2222",
        "title": "FIELD TECH??",
    },
    # -------------------------
    # 31–40 NICHE CASES
    # -------------------------
    {
        "name": "Jean-Pierre Le Roux",
        "email": "jpleroux@paris.fr",
        "phone": "+33 1 40 00 00 00",
        "address": "Hôtel de Ville, Paris",
        "department": "Voirie",
        "title": "Chef de service",
    },
    {
        "name": "李小龍",
        "email": "bruce.lee@hongkong.gov.hk",
        "phone": "+852 2802 0022",
        "address": "Hong Kong",
        "department": "Transport Dept",
        "title": "Officer",
    },
    {
        "name": "Иван Петров",
        "email": "ivan.petrov@gov.ru",
        "phone": "+7 495 123 4567",
        "address": "Москва",
        "department": "Министерство культуры",
        "title": "Специалист",
    },
    {
        "name": "عبدالله صالح",
        "email": "abdullah.saleh@riyadh.gov.sa",
        "phone": "+966 11 456 7890",
        "address": "Riyadh",
        "department": "Municipality",
        "title": "Coordinator",
    },
    {
        "name": "João Miguel",
        "email": "joao.miguel@lisboa.pt",
        "phone": "+351 21 322 0000",
        "address": "Lisboa",
        "department": "Urbanismo",
        "title": "Técnico Superior",
    },
    # -------------------------
    # 41–50 EXTREME EDGE CASES
    # -------------------------
    {
        "name": "",
        "email": "noemail",
        "phone": "123",
        "address": "none",
        "department": "",
        "title": "",
    },
    {
        "name": "123 123 123",
        "email": "123@123.com",
        "phone": "123123123",
        "address": "123 123",
        "department": "123 123",
        "title": "123",
    },
    {
        "name": "Mayor Francis Baker; DOT",
        "email": "",
        "phone": "",
        "address": "",
        "department": "",
        "title": "",
    },
    {
        "name": "Chief.?? John *** Smith",
        "email": "smith@city",
        "phone": "phone",
        "address": "address",
        "department": "dept dept dept",
        "title": "title??",
    },
    {
        "name": "Normal Name",
        "email": "invalid@@email",
        "phone": "++--++",
        "address": "Unknown",
        "department": "HR 555-111-2222",
        "title": "???",
    },
]


def rate(result):
    """Very simple heuristic: you can upgrade later."""
    ok = True

    # name
    if not result.name or not result.name.get("full"):
        ok = False

    # email
    if result.email is None:
        ok = False

    # phone
    if result.phone is None:
        ok = False

    return "OK" if ok else "Needs improvement"


def test_scenarios():
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n--- Scenario {i} ---")
        print("Input:", scenario)
        result = mint(**scenario)
        print("Output:", result.title_canonical)
        print("Rating:", rate(result))


if __name__ == "__main__":
    test_scenarios()
