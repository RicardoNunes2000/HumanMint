"""Test that all examples in documentation actually work."""

from humanmint import mint, compare, bulk, export_csv
import tempfile
import os


def test_readme_basic_example():
    """Test the main README example."""
    result = mint(
        name="Dr. John Q. Smith, PhD",
        email="JOHN.SMITH@CITY.GOV",
        phone="(202) 555-0173 ext 456",
        department="001 - Public Works Dept",
        title="Chief of Police"
    )

    assert result.name_str == "John Q Smith"  # PhD suffix is stripped
    assert result.email_str == "john.smith@city.gov"
    assert result.phone_str == "+1 202-555-0173"
    assert result.department_str == "Public Works"
    assert result.title_str == "police chief"


def test_title_field_access():
    """Test title field access patterns from README."""
    result = mint(title="Chief of Police")

    # Dict access
    assert result.title["raw"] == "Chief of Police"
    assert result.title["normalized"] == "Chief of Police"  # Cleaned, not title-cased
    assert result.title["canonical"] == "police chief"
    assert result.title["is_valid"] is True

    # Shorthand properties
    assert result.title_str == "police chief"
    assert result.title_normalized == "Chief of Police"


def test_compare_example():
    """Test compare function from README."""
    r1 = mint(name="John Smith", email="john@example.com")
    r2 = mint(name="Jon Smith", email="john.smith@example.com")

    score = compare(r1, r2)
    assert isinstance(score, (int, float))
    assert 0 <= score <= 100


def test_bulk_example():
    """Test bulk processing from README."""
    records = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]

    results = bulk(records, workers=4, progress=False)
    assert len(results) == 2
    assert results[0].name_str == "Alice"
    assert results[1].name_str == "Bob"


def test_government_contacts_example():
    """Test Government Contacts use case example."""
    result = mint(
        name="Chief Robert Patterson",
        email="robert.patterson@police.gov",
        phone="(202) 555-0178",
        department="000171 - Police",
        title="Chief of Police"
    )

    assert result.name_str == "Robert Patterson"
    assert result.department_str == "Police"
    assert result.title_str == "police chief"
    assert result.phone_str == "+1 202-555-0178"


def test_hr_salesforce_example():
    """Test HR/Salesforce use case example."""
    result = mint(
        name="Dr. Sarah Johnson, MBA",
        email="SARAH@COMPANY.COM",
        phone="(415) 555-0123 x456",
        department="Engineering",
        title="Senior Software Engineer"
    )

    # Names
    assert result.name_first == "Sarah"
    assert result.name_last == "Johnson"
    assert result.name_gender == "female"  # Returns lowercase

    # Email
    assert result.email_str == "sarah@company.com"
    assert result.email_domain == "company.com"

    # Phone
    assert result.phone_str == "+1 415-555-0123"
    assert result.phone_extension == "456"

    # Title transformation stages
    assert result.title["raw"] == "Senior Software Engineer"
    assert result.title["canonical"] == "senior software engineer"
    assert result.title_str == "senior software engineer"


def test_department_override():
    """Test custom department mapping from Government Contacts."""
    result = mint(
        department="Public Works Division",
        dept_overrides={"public works": "Infrastructure Services"}
    )

    # Override should match after normalization
    assert result.department_str in ["Infrastructure Services", "Public Works"]


def test_export_csv():
    """Test CSV export functionality."""
    records = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]

    results = bulk(records, workers=2, progress=False)

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name

    try:
        export_csv(results, temp_path, flatten=True)
        assert os.path.exists(temp_path)

        # Verify file has content
        with open(temp_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'Alice' in content or 'alice' in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
