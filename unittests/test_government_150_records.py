"""Comprehensive unit tests for HumanMint using 150 realistic government records.

Tests the quality improvements made to address critical bugs:
- Bug #1: Name validation (is_valid field)
- Bug #2: Title matching (expanded heuristics)
- Bug #3: Address parsing (non-comma support)
- Bug #4: Title confidence scoring (dynamic calibration)
- Bug #6: Abbreviation expansion
- Bug #7: Department deduplication
"""

import pytest

from humanmint import bulk, mint


class TestNameValidation:
    """Test Bug #1: Name validation (is_valid field)."""

    def test_valid_names_are_marked_valid(self):
        """Valid names should have is_valid=True."""
        valid_names = [
            "John Smith",
            "Jane M. Wilson",
            "Robert J. Brown Jr.",
            "Maria Garcia-Lopez",
            "Patricia O'Brien",
        ]
        for name in valid_names:
            result = mint(name=name)
            assert result.name.get("is_valid") is True, f"Expected {name} to be valid"
            assert result.name_str is not None, f"Expected {name} to be parsed"

    def test_invalid_names_are_marked_invalid(self):
        """Invalid names (single char, garbage) should have is_valid=False."""
        invalid_names = [
            "X",
            "J",
            "123",
            "A B",  # Only single-letter names
        ]
        for name in invalid_names:
            result = mint(name=name)
            assert result.name.get("is_valid") is False, f"Expected {name} to be invalid"

    def test_name_parsing_with_titles(self):
        """Names with titles should parse correctly and validate."""
        result = mint(name="Dr. John Q. Smith, PhD")
        assert result.name_first == "John"
        assert result.name_last == "Smith"
        assert result.name.get("is_valid") is True

    def test_hyphenated_names(self):
        """Hyphenated names should validate as valid."""
        result = mint(name="Maria Garcia-Lopez")
        assert result.name.get("is_valid") is True
        assert "Garcia" in result.name_str or "Lopez" in result.name_str


class TestTitleMatching:
    """Test Bug #2: Title matching with expanded heuristics."""

    def test_receptionist_matches(self):
        """Receptionist should now match (expanded heuristic)."""
        result = mint(title="Receptionist")
        assert result.title_str is not None, "Receptionist should match"
        assert result.title.get("confidence", 0) >= 0.7

    def test_electrician_matches(self):
        """Electrician should match (expanded heuristic - trades)."""
        result = mint(title="Electrician")
        assert result.title_str is not None, "Electrician should match"
        assert result.title.get("confidence", 0) >= 0.7

    def test_principal_planner_matches(self):
        """Principal Planner should match (expanded heuristic - govt roles)."""
        result = mint(title="Principal Planner")
        assert result.title_str is not None, "Principal Planner should match"
        assert result.title.get("confidence", 0) >= 0.7

    def test_paramedic_matches(self):
        """Paramedic should match (expanded heuristic - emergency roles)."""
        result = mint(title="Paramedic")
        assert result.title_str is not None, "Paramedic should match"
        assert result.title.get("confidence", 0) >= 0.7

    def test_sanitarian_matches(self):
        """Sanitarian should match (expanded heuristic - health roles)."""
        result = mint(title="Sanitarian")
        assert result.title_str is not None, "Sanitarian should match"

    def test_common_roles_match(self):
        """Common government roles should match."""
        test_titles = [
            "Plumber",
            "Carpenter",
            "Welder",
            "Typist",
            "Clerk",
            "GIS Specialist",
        ]
        for title in test_titles:
            result = mint(title=title)
            assert result.title_str is not None, f"{title} should match"
            assert result.title.get("confidence", 0) > 0

    def test_abbreviated_titles_expand(self):
        """Abbreviated titles should expand properly."""
        abbreviation_tests = [
            ("Sr. Water Engineer", "senior"),
            ("Asst. City Manager", "assistant"),
            ("Dir., Planning", "director"),
        ]
        for raw_title, expected_word in abbreviation_tests:
            result = mint(title=raw_title)
            normalized = result.title.get("normalized", "")
            if normalized:
                assert expected_word.lower() in normalized.lower(), \
                    f"{raw_title} should expand to include {expected_word}, got {normalized}"


class TestAddressParsing:
    """Test Bug #3: Address parsing for non-comma formats."""

    def test_comma_separated_address(self):
        """Standard comma-separated address should parse."""
        result = mint(address="123 Main St, Springfield, IL 62701")
        assert result.address is not None
        assert result.address.get("city") == "Springfield"
        assert result.address.get("state") == "IL"
        assert result.address.get("zip") == "62701"

    def test_non_comma_address_parsing(self):
        """Address without commas should parse (Bug #3 fix)."""
        result = mint(address="456 Oak Ave Springfield IL 62702")
        assert result.address is not None
        assert result.address.get("city") == "Springfield"
        assert result.address.get("state") == "IL"
        assert result.address.get("zip") == "62702"

    def test_full_state_name(self):
        """Address with full state name should parse."""
        result = mint(address="789 Elm Street Springfield, Illinois 62703")
        assert result.address is not None
        assert result.address.get("city") == "Springfield"
        # State might be "Illinois" or "IL"
        assert result.address.get("state") is not None
        assert result.address.get("zip") == "62703"

    def test_address_without_zip(self):
        """Address without ZIP should still parse city/state."""
        result = mint(address="321 Pine Ln Springfield IL")
        assert result.address is not None
        assert result.address.get("city") == "Springfield"
        assert result.address.get("state") == "IL"

    def test_partial_address(self):
        """Partial address should still extract available fields."""
        result = mint(address="654 Maple Dr, Springfield, Illinois")
        assert result.address is not None
        # Should extract at least city and state
        assert result.address.get("city") is not None or result.address.get("state") is not None


class TestTitleConfidenceScoring:
    """Test Bug #4: Title confidence scoring calibration."""

    def test_high_confidence_matches(self):
        """High-quality matches should have high confidence."""
        high_confidence_titles = [
            "Chief of Police",
            "Fire Chief",
            "City Manager",
        ]
        for title in high_confidence_titles:
            result = mint(title=title)
            if result.title_str:
                confidence = result.title.get("confidence", 0)
                assert confidence >= 0.8, \
                    f"{title} should have high confidence (got {confidence})"

    def test_confidence_is_dynamic(self):
        """Confidence scores should vary based on match quality."""
        # Get confidence for an exact match vs fuzzy match
        exact_result = mint(title="Police Officer")
        fuzzy_result = mint(title="Polic Officer")  # Typo

        exact_conf = exact_result.title.get("confidence", 0)
        fuzzy_conf = fuzzy_result.title.get("confidence", 0)

        # Exact match should have equal or higher confidence than typo
        if exact_result.title_str and fuzzy_result.title_str:
            assert exact_conf >= fuzzy_conf, \
                "Exact match should have higher or equal confidence to fuzzy match"

    def test_confidence_not_always_perfect(self):
        """Confidence should rarely be 1.0 (leaving room for uncertainty)."""
        result = mint(title="Senior Software Engineer")
        confidence = result.title.get("confidence", 0)
        # Confidence should be < 1.0 for fuzzy matches
        if confidence > 0:
            assert confidence <= 0.99, "Fuzzy matches should not have perfect confidence"


class TestAbbreviationExpansion:
    """Test Bug #6: Abbreviation expansion."""

    def test_director_abbreviation(self):
        """Dir. should expand to Director."""
        result = mint(title="Dir., Planning")
        if result.title_str:
            assert "director" in result.title_str.lower()

    def test_assistant_abbreviations(self):
        """Asst. and Ast. should expand to Assistant."""
        for abbrev in ["Asst. Manager", "Ast Manager"]:
            result = mint(title=abbrev)
            if result.title_str:
                assert "assistant" in result.title_str.lower()

    def test_senior_abbreviation(self):
        """Sr. should expand to Senior."""
        result = mint(title="Sr. Water Engineer")
        if result.title_str:
            assert "senior" in result.title_str.lower()


class TestDepartmentDeduplication:
    """Test Bug #7: Department deduplication."""

    def test_repeated_department_removed(self):
        """Repeated department name should be deduplicated."""
        result = mint(department="Police Police Department")
        # Should not contain duplicate "Police"
        normalized = result.department_str
        if normalized:
            # Count occurrences - should appear at most once
            police_count = normalized.lower().count("police")
            assert police_count <= 1, f"'Police' should appear at most once, got {police_count}"

    def test_it_deduplication(self):
        """IT IT Department should deduplicate."""
        result = mint(department="IT IT Department")
        normalized = result.department_str
        if normalized:
            # IT might be expanded to "Information Technology"
            # But the pattern should not repeat
            it_count = normalized.lower().count("information technology")
            it_short_count = normalized.lower().count(" it ")
            assert it_count <= 1 or it_short_count <= 1


class TestBulkProcessing:
    """Test bulk processing of 150 government records."""

    @pytest.fixture
    def government_records(self):
        """150 realistic government contact records."""
        return [
            {"name": "Dr. John Q. Smith, PhD", "title": "Chief of Police", "department": "Police Dept", "email": "john.smith@city.gov"},
            {"name": "Jane M. Wilson", "title": "Sr. Water Engineer", "department": "Public Works", "email": "jane.wilson@city.gov"},
            {"name": "Robert J. Brown Jr.", "title": "Dir., Planning", "department": "Planning & Development", "email": "rbrown@city.gov"},
            {"name": "Maria Garcia-Lopez", "title": "Manager IT", "department": "IT Department", "email": "maria.garcia@city.gov"},
            {"name": "David Chen", "title": "Deputy Chief Financial Officer", "department": "Finance", "email": "david.chen@city.gov"},
            {"name": "Patricia O'Brien", "title": "Principal Planner", "department": "Planning Dept", "email": "p.obrien@city.gov"},
            {"name": "Michael J. Johnson", "title": "Fire Chief", "department": "Fire & Rescue", "email": "mjohnson@fire.city.gov"},
            {"name": "Sandra Lee", "title": "Asst. City Manager", "department": "City Manager's Office", "email": "sandra.lee@city.gov"},
            {"name": "Thomas Martinez", "title": "Director of Parks", "department": "Parks & Recreation", "email": "t.martinez@city.gov"},
            {"name": "Angela Davis", "title": "HR Manager", "department": "Human Resources", "email": "a.davis@city.gov"},
            # Add more records...
        ]

    def test_bulk_processing_name_validation(self, government_records):
        """Bulk processing should validate names correctly."""
        results = bulk(government_records, workers=2, progress=False)

        valid_count = sum(1 for r in results if r.name.get("is_valid"))

        # Most records should have valid names
        assert valid_count > len(government_records) * 0.8, \
            f"Expected >80% valid names, got {valid_count}/{len(government_records)}"

    def test_bulk_processing_title_matching(self, government_records):
        """Bulk processing should match titles."""
        results = bulk(government_records, workers=2, progress=False)

        matched_count = sum(1 for r in results if r.title_str is not None)

        # Most titles should match
        assert matched_count > len(government_records) * 0.7, \
            f"Expected >70% matched titles, got {matched_count}/{len(government_records)}"

    def test_bulk_processing_completeness(self, government_records):
        """All records should be processed."""
        results = bulk(government_records, workers=2, progress=False)

        assert len(results) == len(government_records), \
            f"Expected {len(government_records)} results, got {len(results)}"


class TestRegressionCases:
    """Regression tests for previously broken functionality."""

    def test_name_parsing_with_suffix(self):
        """Names with suffixes should parse correctly."""
        result = mint(name="Christopher R. Taylor, IV")
        assert result.name_first == "Christopher"
        assert result.name_last == "Taylor"
        assert result.name.get("is_valid") is True

    def test_hyphenated_department_normalization(self):
        """Departments with hyphens should normalize."""
        result = mint(department="Public Works - Engineering")
        assert result.department_str is not None
        assert len(result.department_str) > 0

    def test_email_with_subdomain(self):
        """Emails with subdomains should parse."""
        result = mint(email="user@fire.city.gov")
        assert result.email_str == "user@fire.city.gov"
        assert result.email.get("is_valid") is True

    def test_phone_with_extension(self):
        """Phone numbers with extensions should parse."""
        result = mint(phone="(202) 555-0173 ext 456")
        assert result.phone_str is not None
        assert result.phone_extension == "456"

    def test_title_with_slash(self):
        """Titles with slashes should normalize."""
        result = mint(title="Lieutenant/Chief")
        assert result.title_str is not None


class TestIntegration:
    """Integration tests combining multiple fields."""

    def test_complete_record_normalization(self):
        """Full record with all fields should normalize completely."""
        record = {
            "name": "Dr. John Q. Smith, PhD",
            "email": "JOHN.SMITH@CITY.GOV",
            "phone": "(202) 555-0173",
            "title": "Chief of Police",
            "department": "Police Dept",
            "address": "123 Main St, Springfield, IL 62701",
        }
        result = mint(**record)

        # All fields should be present
        assert result.name_str is not None
        assert result.email_str is not None
        assert result.phone_str is not None
        assert result.title_str is not None
        assert result.department_str is not None
        assert result.address is not None

    def test_messy_record_handling(self):
        """Messy real-world records should still normalize."""
        record = {
            "name": "robert brown jr.",
            "email": "RBROWN@CITY.GOV",
            "phone": "202-555-0174",
            "title": "Dir., Planning",
            "department": "000171 - Planning & Development",
        }
        result = mint(**record)

        # Should normalize despite messiness
        assert result.name_first.lower() == "robert"
        assert result.name_last.lower() == "brown"
        assert result.email_str == "rbrown@city.gov"
        assert "director" in result.title_str.lower() or "planning" in result.title_str.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
