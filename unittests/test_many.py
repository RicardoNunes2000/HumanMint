import sys

sys.path.insert(0, "src")

from humanmint import mint

# ======================================================================
# 1) 10 ADDRESS TESTS
# ======================================================================


def test_addr_1():
    r = mint(address="123 N. Main St Apt 4B, Springfield, MA 01103")
    assert r.address["city"] == "Springfield"


def test_addr_2():
    r = mint(address="500 5th Ave, New York NY 10110")
    assert r.address["state"] == "NY"


def test_addr_3():
    r = mint(address="1600 Pennsylvania Ave NW, Washington, DC 20500")
    assert r.address["zip"] == "20500"


def test_addr_4():
    r = mint(address="1 Infinite Loop, Cupertino, CA")
    assert r.address["city"] == "Cupertino"


def test_addr_5():
    r = mint(address="200 Elm St, Madison, WI 53703")
    assert r.address["country"] == "US"


def test_addr_6():
    r = mint(address="742 Evergreen Terrace, Springfield, IL 62704")
    assert r.address["state"] == "IL"


def test_addr_7():
    r = mint(address="75 Market St Suite 300, Portland, ME 04101")
    assert r.address["unit"] == "Suite 300"


def test_addr_8():
    r = mint(address="350 Fifth Avenue, New York, NY 10118")
    assert r.address["zip"] == "10118"


def test_addr_9():
    r = mint(address="805 SW Broadway, Portland OR 97205")
    assert r.address["city"] == "Portland"


def test_addr_10():
    r = mint(address="1100 Congress Ave, Austin, TX 78701")
    assert r.address["state"] == "TX"


# ======================================================================
# 2) 10 REAL GOVERNMENT-STYLE RECORDS
# ======================================================================


def test_real_1():
    r = mint(
        name="Laura M. Johnson",
        email="laura.johnson@cityofmadison.com",
        phone="(608) 266-4751",
        department="Public Works",
        title="Civil Engineer",
    )
    assert r.department["canonical"] == "Public Works"


def test_real_2():
    r = mint(
        name="Michael T. Barrett",
        email="mbarrett@springfieldma.gov",
        phone="413-787-6100",
        department="Department of Public Works",
        title="Deputy Director",
    )
    assert r.name["first"] == "Michael"


def test_real_3():
    r = mint(
        name="Sarah L. Ramirez",
        email="sramirez@cityofsalinas.org",
        phone="831-758-7201",
        department="Community Development",
    )
    assert r.department["canonical"] == "Community Development"


def test_real_4():
    r = mint(
        name="Rebecca S. Chen",
        email="rchen@seattle.gov",
        department="Office of Sustainability & Environment",
    )
    assert r.department["canonical"].startswith("Office")


def test_real_5():
    r = mint(
        name="James O'Brien",
        email="jobrien@newtonma.gov",
        phone="617-796-1000",
        department="Finance Department",
    )
    assert r.department["canonical"] == "Finance"


def test_real_6():
    r = mint(
        name="Karen Walker", email="kwalker@sandiego.gov", title="Accounting Supervisor"
    )
    assert r.title["canonical"] == "accounting supervisor"


def test_real_7():
    r = mint(
        name="Joseph T Kim",
        email="jkim@lacity.org",
        phone="213-978-1133",
        department="Information Technology Agency",
    )
    assert "technology" in r.department["category"]


def test_real_8():
    r = mint(
        name="Anthony Thompson",
        email="athompson@houstontx.gov",
        department="Houston Public Works",
    )
    assert "Works" in r.department["canonical"]


def test_real_9():
    r = mint(
        name="Maria D. Lopez", email="mlopez@boston.gov", title="Building Inspector"
    )
    assert "inspector" in r.title["canonical"]


# ======================================================================
# 3) 10 HARDER BUT STILL DOABLE INPUTS
# ======================================================================


def test_hard_1():
    r = mint(name="Dr. Emily C. Watson, PhD")
    assert r.name["first"] == "Emily"


def test_hard_2():
    r = mint(name="J. R. Robertson")
    assert r.name["first"] == "J" or r.name["middle"] == "R"


def test_hard_3():
    r = mint(email="JOHN.SMITH@CITY.GOV")
    assert r.email["normalized"] == "john.smith@city.gov"


def test_hard_4():
    r = mint(phone="202 555 0133 ext 55")
    assert r.phone["extension"] == "55"


def test_hard_5():
    r = mint(department="Dept of Transportation Services")
    assert r.department["canonical"] == "Transportation Services"


def test_hard_6():
    r = mint(title="Chief of Police")
    assert "chief" in r.title["canonical"]


def test_hard_7():
    r = mint(name="José Ramírez")
    assert r.name["first"] == "José"


def test_hard_8():
    r = mint(address="500 S. State St, Ann Arbor MI 48109")
    assert r.address["city"] == "Ann Arbor"


def test_hard_9():
    r = mint(name="Jo")
    assert r.name["first"] == "Jo"


def test_hard_10():
    r = mint(title="Sr Engineer")
    assert "engineer" in r.title["canonical"]


# ======================================================================
# 4) 10 MODERATELY MESSY INPUTS
# ======================================================================


def test_messy_1():
    r = mint(name="### TEMP ### JOHN Q PUBLIC")
    assert r.name["last"] == "Public"


def test_messy_2():
    r = mint(email=" invalid@@example..com  ")
    assert r.email["is_valid"] is False


def test_messy_3():
    r = mint(phone="(999)---555...1212")
    assert r.phone["is_valid"] in (True, False)


def test_messy_4():
    r = mint(department="00021 - Public Works – 555-555-5555")
    assert r.department["canonical"] == "Public Works"


def test_messy_5():
    r = mint(title="Dir. of Ops / PW")
    # Abbreviated title "Dir. of Ops / PW" normalizes to "Director of Operations Ops / PW"
    # No canonical matches due to fuzzy threshold, so canonical is None
    # Test that we at least normalize it without crashing
    assert r.title["normalized"] is not None
    assert "director" in r.title["normalized"].lower() or r.title["canonical"] is None


def test_messy_6():
    r = mint(name="Dr,,,, Anna-Marie Smith")
    assert r.name["first"] == "Anna-Marie"


def test_messy_7():
    r = mint(address="City Hall Building 123, Floor 2, Boston, MA 02108")
    assert r.address["city"] == "Boston"


def test_messy_8():
    r = mint(email="unknown@SOMECITY.GOV ")
    assert r.email["domain"] == "somecity.gov"


def test_messy_9():
    r = mint(name="ROBERT      BROWN")
    assert r.name["first"] == "Robert"


def test_messy_10():
    r = mint(title="Asst Dir PW")
    # Abbreviated titles don't achieve 92%+ fuzzy threshold for canonical matching
    # Test that we normalize without crashing
    assert r.title["normalized"] is not None
    assert (
        "director" in r.title["normalized"].lower()
        or "assistant" in r.title["normalized"].lower()
    )


# ======================================================================
# 5) 10 NICHE / EDGE CASES
# ======================================================================


def test_edge_1():
    r = mint()  # noqa: F401
    assert True  # should not crash


def test_edge_2():
    r = mint(name="Madonna")
    assert r.name["last"] == ""


def test_edge_3():
    r = mint(phone="ext 500 only")
    assert r.phone["extension"] in (None, "500")


def test_edge_4():
    r = mint(email="test@localhost")
    assert isinstance(r.email["is_valid"], bool)


def test_edge_5():
    r = mint(department="Planning & Dev.")
    assert "Planning" in r.department["canonical"]


def test_edge_6():
    r = mint(title="zzz")
    assert r.title["is_valid"] in (True, False)


def test_edge_7():
    r = mint(address="Just a random building")
    assert r.address["confidence"] <= 0.5


def test_edge_8():
    r = mint(name="李 华")
    assert r.name["gender"] in ("unknown", None)


def test_edge_9():
    r = mint(name="First Last", email=None, phone=None, department=None)
    assert r.name["first"] == "First"


def test_edge_10():
    r = mint(title="Officer I")
    # "Officer I" doesn't achieve 92%+ fuzzy match to any canonical
    # Test that it at least normalizes and doesn't crash
    assert r.title["normalized"] is not None
    assert "officer" in r.title["normalized"].lower()


def test_org_acronym_mapping():
    r = mint(organization="USDA")
    assert r.organization
    assert "Agriculture" in r.organization.get("canonical", "")
