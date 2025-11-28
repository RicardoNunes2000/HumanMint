import sys

sys.path.insert(0, "src")

from humanmint import mint


def test_office_of_strategic_initiatives_and_innovation_maps():
    """Ensure long OSI variants prefer the mapping over generic fuzzy matches."""
    result = mint(
        name="JOHN Q PUBLIC",
        email="JOHN.Q.PUBLIC@GOVERNMENT.ORG",
        phone="703-555-5555",
        department="OFFICE OF STRATEGIC INITIATIVES AND INNOVATION DEPARTMENT",
        title="ASSISTANT DEPUTY DIRECTOR, POLICY AND PROGRAM MANAGEMENT",
    )

    assert result.department
    assert result.department["canonical"] == "Strategic Initiatives"
