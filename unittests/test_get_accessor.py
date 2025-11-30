"""
Tests for MintResult.get() accessor method.

Tests the new .get() convenience method for safely accessing nested fields
with dot notation and default value support.
"""

import sys
sys.path.insert(0, "src")

import pytest
from humanmint import mint


class TestGetAccessor:
    """Test the MintResult.get() method for accessing nested fields."""

    def test_get_name_first(self):
        """Test accessing name.first via get()."""
        result = mint(name="John Smith")
        assert result.get("name.first") == "John"

    def test_get_name_last(self):
        """Test accessing name.last via get()."""
        result = mint(name="John Smith")
        assert result.get("name.last") == "Smith"

    def test_get_name_middle(self):
        """Test accessing name.middle via get()."""
        result = mint(name="John Alexander Smith")
        assert result.get("name.middle") == "Alexander"

    def test_get_email_domain(self):
        """Test accessing email.domain via get()."""
        result = mint(email="john@example.com")
        assert result.get("email.domain") == "example.com"

    def test_get_email_normalized(self):
        """Test accessing email.normalized via get()."""
        result = mint(email="JOHN@EXAMPLE.COM")
        assert result.get("email.normalized") == "john@example.com"

    def test_get_phone_e164(self):
        """Test accessing phone.e164 via get()."""
        result = mint(phone="(202) 555-0123")
        assert result.get("phone.e164") == "+12025550123"

    def test_get_phone_pretty(self):
        """Test accessing phone.pretty via get()."""
        result = mint(phone="2025550123")
        assert result.get("phone.pretty") is not None
        assert "202" in result.get("phone.pretty")

    def test_get_department_canonical(self):
        """Test accessing department.canonical via get()."""
        result = mint(department="Public Works Dept")
        assert result.get("department.canonical") == "Public Works"

    def test_get_title_canonical(self):
        """Test accessing title.canonical via get()."""
        result = mint(title="Chief of Police")
        assert result.get("title.canonical") == "police chief"

    def test_get_root_object(self):
        """Test accessing root objects (without nested field)."""
        result = mint(name="John Smith")
        name_dict = result.get("name")
        assert isinstance(name_dict, dict)
        assert name_dict.get("first") == "John"
        assert name_dict.get("last") == "Smith"

    def test_get_missing_nested_field(self):
        """Test accessing missing nested field returns None."""
        result = mint(name="John Smith")
        assert result.get("name.nonexistent") is None

    def test_get_missing_nested_field_with_default(self):
        """Test accessing missing nested field with default value."""
        result = mint(name="John Smith")
        assert result.get("name.nonexistent", "DEFAULT") == "DEFAULT"

    def test_get_missing_root_field(self):
        """Test accessing missing root field returns None."""
        result = mint(name="John Smith")
        assert result.get("nonexistent") is None

    def test_get_missing_root_field_with_default(self):
        """Test accessing missing root field with default value."""
        result = mint(name="John Smith")
        assert result.get("nonexistent", "DEFAULT_VALUE") == "DEFAULT_VALUE"

    def test_get_phone_when_no_phone_provided(self):
        """Test accessing phone when not provided."""
        result = mint(name="Jane Doe")
        assert result.get("phone") is None
        assert result.get("phone.e164") is None
        assert result.get("phone.e164", "+1 000-000-0000") == "+1 000-000-0000"

    def test_get_department_when_no_dept_provided(self):
        """Test accessing department when not provided."""
        result = mint(name="Jane Doe")
        assert result.get("department") is None
        assert result.get("department.canonical") is None

    def test_get_all_fields_comprehensive(self):
        """Test accessing all major fields via get()."""
        result = mint(
            name="Dr. Jane Smith",
            email="jane.smith@city.gov",
            phone="(202) 555-0172",
            address="123 Main St, Springfield, IL 62701",
            department="Planning Department",
            title="Chief Planner",
            organization="City of Springfield"
        )

        # Names
        assert result.get("name.first") == "Jane"
        assert result.get("name.last") == "Smith"
        assert result.get("name.full") == "Jane Smith"

        # Email
        assert result.get("email.domain") == "city.gov"
        assert result.get("email.normalized") == "jane.smith@city.gov"

        # Phone
        assert result.get("phone.e164") == "+12025550172"

        # Address
        assert result.get("address.city") == "Springfield"
        assert result.get("address.state") == "IL"
        assert result.get("address.zip") == "62701"

        # Department
        assert result.get("department.canonical") == "Planning"
        assert result.get("department.category") == "planning & development"

        # Title
        # Canonicalization maps to canonical form (may be reordered due to fuzzy matching)
        title_canonical = result.get("title.canonical").lower()
        assert "planner" in title_canonical and "chief" in title_canonical

        # Organization
        assert result.get("organization.canonical") == "Springfield"

    def test_get_with_empty_default(self):
        """Test that empty string default works correctly."""
        result = mint(name="John Smith")
        assert result.get("phone.e164", "") == ""

    def test_get_with_zero_default(self):
        """Test that numeric default works correctly."""
        result = mint(name="John Smith")
        assert result.get("phone.e164", 0) == 0

    def test_get_with_none_explicit_default(self):
        """Test that None can be explicitly passed as default."""
        result = mint(name="John Smith")
        assert result.get("phone.e164", None) is None

    def test_get_title_is_valid(self):
        """Test accessing boolean field title.is_valid."""
        result = mint(title="Chief of Police")
        assert result.get("title.is_valid") is True

    def test_get_email_is_valid(self):
        """Test accessing boolean field email.is_valid."""
        result = mint(email="john@example.com")
        assert result.get("email.is_valid") is True

    def test_get_email_is_free_provider(self):
        """Test accessing boolean field email.is_free_provider."""
        result = mint(email="john@gmail.com")
        assert result.get("email.is_free_provider") is True

        result2 = mint(email="john@company.com")
        assert result2.get("email.is_free_provider") is False

    def test_get_phone_type(self):
        """Test accessing phone.type field."""
        result = mint(phone="(202) 555-0123")
        phone_type = result.get("phone.type")
        assert phone_type is not None
        assert phone_type in ["FIXED_LINE", "MOBILE", "UNKNOWN", "fixed_line_or_mobile"]
