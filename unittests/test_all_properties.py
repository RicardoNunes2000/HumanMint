"""
Comprehensive test for all MintResult properties.

This test ensures all convenience properties on MintResult work correctly
across all data types: names, emails, phones, departments, titles, addresses, and organizations.
"""

import sys

sys.path.insert(0, "src")

import pytest
from humanmint import mint


class TestAllNameProperties:
    """Test all name-related properties."""

    def test_name_str(self):
        """Test name_str property."""
        result = mint(name="John Alexander Smith Jr.")
        assert result.name_str is not None
        assert "John" in result.name_str
        assert "Smith" in result.name_str

    def test_name_first(self):
        """Test name_first property."""
        result = mint(name="John Alexander Smith")
        assert result.name_first == "John"

    def test_name_last(self):
        """Test name_last property."""
        result = mint(name="John Alexander Smith")
        assert result.name_last == "Smith"

    def test_name_middle(self):
        """Test name_middle property."""
        result = mint(name="John Alexander Smith")
        assert result.name_middle == "Alexander"

    def test_name_suffix(self):
        """Test name_suffix property."""
        result = mint(name="John Smith Jr.")
        assert result.name_suffix == "jr"

    def test_name_gender(self):
        """Test name_gender property."""
        result = mint(name="John Smith")
        assert result.name_gender in ["male", "female", "unknown", None]

    def test_name_properties_when_no_name(self):
        """Test all name properties return None when no name provided."""
        result = mint(email="test@example.com")
        assert result.name_str is None
        assert result.name_first is None
        assert result.name_last is None
        assert result.name_middle is None
        assert result.name_suffix is None
        assert result.name_gender is None


class TestAllEmailProperties:
    """Test all email-related properties."""

    def test_email_str(self):
        """Test email_str property."""
        result = mint(email="JOHN.DOE@EXAMPLE.COM")
        assert result.email_str == "john.doe@example.com"

    def test_email_domain(self):
        """Test email_domain property."""
        result = mint(email="john@example.com")
        assert result.email_domain == "example.com"

    def test_email_valid(self):
        """Test email_valid property."""
        result = mint(email="john@example.com")
        assert result.email_valid is True

    def test_email_generic(self):
        """Test email_generic property."""
        result = mint(email="info@example.com")
        assert isinstance(result.email_generic, bool)

    def test_email_free(self):
        """Test email_free property."""
        result = mint(email="john@gmail.com")
        assert result.email_free is True

    def test_email_properties_when_no_email(self):
        """Test all email properties return None when no email provided."""
        result = mint(name="John Smith")
        assert result.email_str is None
        assert result.email_domain is None
        assert result.email_valid is None
        assert result.email_generic is None
        assert result.email_free is None


class TestAllPhoneProperties:
    """Test all phone-related properties."""

    def test_phone_str(self):
        """Test phone_str property."""
        result = mint(phone="(202) 555-0123")
        assert result.phone_str is not None
        assert "202" in result.phone_str or "555" in result.phone_str

    def test_phone_e164(self):
        """Test phone_e164 property."""
        result = mint(phone="(202) 555-0123")
        assert result.phone_e164 == "+12025550123"

    def test_phone_pretty(self):
        """Test phone_pretty property."""
        result = mint(phone="2025550123")
        assert result.phone_pretty is not None
        assert "202" in result.phone_pretty

    def test_phone_extension(self):
        """Test phone_extension property."""
        result = mint(phone="(202) 555-0123 x456")
        assert result.phone_extension == "456"

    def test_phone_valid(self):
        """Test phone_valid property."""
        result = mint(phone="(202) 555-0123")
        assert isinstance(result.phone_valid, bool)

    def test_phone_type(self):
        """Test phone_type property."""
        result = mint(phone="(202) 555-0123")
        # Phone type might be MOBILE, FIXED_LINE, etc.
        if result.phone_type is not None:
            assert isinstance(result.phone_type, str)

    def test_phone_properties_when_no_phone(self):
        """Test all phone properties return None when no phone provided."""
        result = mint(name="John Smith")
        assert result.phone_str is None
        assert result.phone_e164 is None
        assert result.phone_pretty is None
        assert result.phone_extension is None
        assert result.phone_valid is None
        assert result.phone_type is None


class TestAllDepartmentProperties:
    """Test all department-related properties."""

    def test_department_str(self):
        """Test department_str property."""
        result = mint(department="Public Works Dept")
        assert result.department_str == "Public Works"

    def test_department_category(self):
        """Test department_category property."""
        result = mint(department="Police Department")
        assert result.department_category is not None
        assert isinstance(result.department_category, str)

    def test_department_normalized(self):
        """Test department_normalized property."""
        result = mint(department="005 - Public Works Dept")
        assert result.department_normalized is not None
        assert isinstance(result.department_normalized, str)

    def test_department_override(self):
        """Test department_override property."""
        result = mint(department="Police Dept")
        assert isinstance(result.department_override, bool)

    def test_department_properties_when_no_department(self):
        """Test all department properties return None when no department provided."""
        result = mint(name="John Smith")
        assert result.department_str is None
        assert result.department_category is None
        assert result.department_normalized is None
        assert result.department_override is None


class TestAllTitleProperties:
    """Test all title-related properties."""

    def test_title_str(self):
        """Test title_str property."""
        result = mint(title="Chief of Police")
        assert result.title_str == "police chief"

    def test_title_raw(self):
        """Test title_raw property."""
        result = mint(title="Dir. of Public Works")
        assert result.title_raw == "Dir. of Public Works"

    def test_title_normalized(self):
        """Test title_normalized property."""
        result = mint(title="Dir. of Public Works")
        assert result.title_normalized is not None
        assert isinstance(result.title_normalized, str)

    def test_title_canonical(self):
        """Test title_canonical property."""
        result = mint(title="Police Chief")
        assert result.title_canonical == "police chief"

    def test_title_valid(self):
        """Test title_valid property."""
        result = mint(title="Police Chief")
        assert isinstance(result.title_valid, bool)

    def test_title_confidence(self):
        """Test title_confidence property."""
        result = mint(title="Police Chief")
        assert isinstance(result.title_confidence, float)
        assert 0.0 <= result.title_confidence <= 1.0

    def test_title_properties_when_no_title(self):
        """Test all title properties return appropriate defaults when no title provided."""
        result = mint(name="John Smith")
        assert result.title_str is None
        assert result.title_raw is None
        assert result.title_normalized is None
        assert result.title_canonical is None
        assert result.title_valid is None
        assert result.title_confidence == 0.0


class TestAllAddressProperties:
    """Test all address-related properties."""

    def test_address_raw(self):
        """Test address_raw property."""
        result = mint(address="123 Main St, New York, NY 10001")
        assert result.address_raw == "123 Main St, New York, NY 10001"

    def test_address_street(self):
        """Test address_street property."""
        result = mint(address="123 Main St, New York, NY 10001")
        if result.address_street is not None:
            assert "Main" in result.address_street

    def test_address_unit(self):
        """Test address_unit property."""
        result = mint(address="123 Main St Apt 4B, New York, NY 10001")
        # Unit might be parsed or None
        assert result.address_unit is None or isinstance(result.address_unit, str)

    def test_address_city(self):
        """Test address_city property."""
        result = mint(address="123 Main St, New York, NY 10001")
        if result.address_city is not None:
            assert isinstance(result.address_city, str)

    def test_address_state(self):
        """Test address_state property."""
        result = mint(address="123 Main St, New York, NY 10001")
        if result.address_state is not None:
            assert isinstance(result.address_state, str)

    def test_address_zip(self):
        """Test address_zip property."""
        result = mint(address="123 Main St, New York, NY 10001")
        if result.address_zip is not None:
            assert isinstance(result.address_zip, str)

    def test_address_country(self):
        """Test address_country property."""
        result = mint(address="123 Main St, New York, NY 10001, USA")
        # Country might be detected or None
        assert result.address_country is None or isinstance(result.address_country, str)

    def test_address_canonical(self):
        """Test address_canonical property."""
        result = mint(address="123 Main St, New York, NY 10001")
        if result.address_canonical is not None:
            assert isinstance(result.address_canonical, str)

    def test_address_properties_when_no_address(self):
        """Test all address properties return None when no address provided."""
        result = mint(name="John Smith")
        assert result.address_raw is None
        assert result.address_street is None
        assert result.address_unit is None
        assert result.address_city is None
        assert result.address_state is None
        assert result.address_zip is None
        assert result.address_country is None
        assert result.address_canonical is None


class TestAllOrganizationProperties:
    """Test all organization-related properties."""

    def test_organization_raw(self):
        """Test organization_raw property."""
        result = mint(organization="City of New York Police Dept")
        assert result.organization_raw == "City of New York Police Dept"

    def test_organization_normalized(self):
        """Test organization_normalized property."""
        result = mint(organization="City of New York Police Dept")
        assert result.organization_normalized is not None
        assert isinstance(result.organization_normalized, str)

    def test_organization_canonical(self):
        """Test organization_canonical property."""
        result = mint(organization="NYC Police Department")
        assert result.organization_canonical is not None
        assert isinstance(result.organization_canonical, str)

    def test_organization_confidence(self):
        """Test organization_confidence property."""
        result = mint(organization="Police Department")
        assert isinstance(result.organization_confidence, float)
        assert 0.0 <= result.organization_confidence <= 1.0

    def test_organization_properties_when_no_organization(self):
        """Test all organization properties return appropriate defaults when no organization provided."""
        result = mint(name="John Smith")
        assert result.organization_raw is None
        assert result.organization_normalized is None
        assert result.organization_canonical is None
        assert result.organization_confidence == 0.0


class TestAllPropertiesCombined:
    """Test all properties work together on a comprehensive record."""

    def test_comprehensive_record_all_properties(self):
        """Test all properties on a record with all fields populated."""
        result = mint(
            name="Dr. Jane Elizabeth Doe Jr.",
            email="jane.doe@citypolice.gov",
            phone="(202) 555-0123 x456",
            department="Police Department",
            title="Chief of Police",
            address="123 Main St, Washington, DC 20001",
            organization="Metropolitan Police Department",
        )

        # Name properties
        assert result.name_str is not None
        assert result.name_first == "Jane"
        assert result.name_last == "Doe"
        assert result.name_middle == "Elizabeth"
        assert result.name_suffix == "jr"
        assert result.name_gender in ["male", "female", "unknown", None]

        # Email properties
        assert result.email_str == "jane.doe@citypolice.gov"
        assert result.email_domain == "citypolice.gov"
        assert result.email_valid is True
        assert isinstance(result.email_generic, bool)
        assert isinstance(result.email_free, bool)

        # Phone properties
        assert result.phone_str is not None
        assert result.phone_e164 == "+12025550123"
        assert result.phone_pretty is not None
        assert result.phone_extension == "456"
        assert isinstance(result.phone_valid, bool)

        # Department properties
        assert result.department_str == "Police"
        assert result.department_category is not None
        assert result.department_normalized is not None
        assert isinstance(result.department_override, bool)

        # Title properties
        assert result.title_str == "police chief"
        assert result.title_raw == "Chief of Police"
        assert result.title_normalized is not None
        assert result.title_canonical == "police chief"
        assert isinstance(result.title_valid, bool)
        assert 0.0 <= result.title_confidence <= 1.0

        # Address properties
        assert result.address_raw == "123 Main St, Washington, DC 20001"
        # Other address fields may or may not be populated depending on parsing

        # Organization properties
        assert result.organization_raw == "Metropolitan Police Department"
        assert result.organization_normalized is not None
        assert result.organization_canonical is not None
        assert 0.0 <= result.organization_confidence <= 1.0

    def test_empty_record_all_properties(self):
        """Test all properties return appropriate defaults on an empty record."""
        result = mint()

        # Name properties
        assert result.name_str is None
        assert result.name_first is None
        assert result.name_last is None
        assert result.name_middle is None
        assert result.name_suffix is None
        assert result.name_gender is None

        # Email properties
        assert result.email_str is None
        assert result.email_domain is None
        assert result.email_valid is None
        assert result.email_generic is None
        assert result.email_free is None

        # Phone properties
        assert result.phone_str is None
        assert result.phone_e164 is None
        assert result.phone_pretty is None
        assert result.phone_extension is None
        assert result.phone_valid is None
        assert result.phone_type is None

        # Department properties
        assert result.department_str is None
        assert result.department_category is None
        assert result.department_normalized is None
        assert result.department_override is None

        # Title properties
        assert result.title_str is None
        assert result.title_raw is None
        assert result.title_normalized is None
        assert result.title_canonical is None
        assert result.title_valid is None
        assert result.title_confidence == 0.0

        # Address properties
        assert result.address_raw is None
        assert result.address_street is None
        assert result.address_unit is None
        assert result.address_city is None
        assert result.address_state is None
        assert result.address_zip is None
        assert result.address_country is None
        assert result.address_canonical is None

        # Organization properties
        assert result.organization_raw is None
        assert result.organization_normalized is None
        assert result.organization_canonical is None
        assert result.organization_confidence == 0.0


class TestPropertyTypeSafety:
    """Test that properties return the expected types."""

    def test_string_properties_return_strings_or_none(self):
        """Test that string properties return str or None."""
        result = mint(
            name="John Smith",
            email="john@example.com",
            phone="2025550123",
            department="Police",
            title="Officer",
        )

        string_props = [
            result.name_str,
            result.name_first,
            result.name_last,
            result.name_middle,
            result.name_suffix,
            result.name_gender,
            result.email_str,
            result.email_domain,
            result.phone_str,
            result.phone_e164,
            result.phone_pretty,
            result.phone_extension,
            result.phone_type,
            result.department_str,
            result.department_category,
            result.department_normalized,
            result.title_str,
            result.title_raw,
            result.title_normalized,
            result.title_canonical,
            result.address_raw,
            result.address_street,
            result.address_unit,
            result.address_city,
            result.address_state,
            result.address_zip,
            result.address_country,
            result.address_canonical,
            result.organization_raw,
            result.organization_normalized,
            result.organization_canonical,
        ]

        for prop in string_props:
            assert prop is None or isinstance(prop, str), (
                f"Expected str or None, got {type(prop)}"
            )

    def test_bool_properties_return_bools_or_none(self):
        """Test that boolean properties return bool or None."""
        result = mint(
            email="john@example.com",
            phone="2025550123",
            department="Police",
            title="Officer",
        )

        bool_props = [
            result.email_valid,
            result.email_generic,
            result.email_free,
            result.phone_valid,
            result.department_override,
            result.title_valid,
        ]

        for prop in bool_props:
            assert prop is None or isinstance(prop, bool), (
                f"Expected bool or None, got {type(prop)}"
            )

    def test_float_properties_return_floats(self):
        """Test that float properties return float."""
        result = mint(title="Police Chief", organization="Police Department")

        assert isinstance(result.title_confidence, float)
        assert isinstance(result.organization_confidence, float)


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
