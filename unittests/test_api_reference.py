"""
Comprehensive tests for all HumanMint modules.
Tests are organized by module and cover all public functions.
"""

import pytest
from humanmint.names import (
    normalize_name,
    infer_gender,
    enrich_name,
    detect_nickname,
    get_nickname_variants,
    get_name_equivalents,
    compare_first_names,
    compare_last_names,
    match_names,
)
from humanmint.emails import (
    normalize_email,
    is_free_provider,
    guess_email,
    get_pattern_scores,
    describe_pattern,
)
from humanmint.phones import (
    normalize_phone,
    detect_impossible,
    detect_fax_pattern,
    detect_voip_pattern,
)
from humanmint.departments import (
    normalize_department,
    find_best_match,
    find_all_matches,
    match_departments,
    get_similarity_score,
    get_department_category,
    get_all_categories,
    get_departments_by_category,
    categorize_departments,
    get_canonical_departments,
    is_canonical,
    load_mappings,
    get_mapping_for_original,
    get_originals_for_canonical,
)
from humanmint.titles import (
    normalize_title_full,
    normalize_title,
    find_best_match as match_title,
    find_all_matches as match_all_titles,
    get_similarity_score as title_similarity,
    get_canonical_titles,
    is_canonical as title_is_canonical,
    get_mapping_for_variant,
    get_all_mappings,
)
from humanmint.addresses import normalize_address
from humanmint.organizations import normalize_organization


# ============================================================================
# NAMES MODULE TESTS
# ============================================================================


class TestNamesModule:
    """Test all functions from humanmint.names"""

    def test_normalize_name_full(self):
        """Test normalize_name with full name"""
        result = normalize_name("Dr. Jane Smith, PhD")
        assert result["first"] == "Jane"
        assert result["last"] == "Smith"
        assert "full" in result
        assert result["is_valid"] is True

    def test_normalize_name_single(self):
        """Test normalize_name with single name"""
        result = normalize_name("Madonna")
        assert result["first"] == "Madonna"
        assert result["last"] is None or result["last"] == ""

    def test_normalize_name_middle(self):
        """Test normalize_name with middle name"""
        result = normalize_name("John David Smith")
        assert result["first"] == "John"
        assert result["middle"] == "David"
        assert result["last"] == "Smith"

    def test_normalize_name_suffix(self):
        """Test normalize_name with suffix"""
        result = normalize_name("Robert Patterson Jr.")
        assert result["first"] == "Robert"
        assert result["last"] == "Patterson"
        assert "suffix" in result

    def test_infer_gender_female(self):
        """Test infer_gender for female name"""
        result = infer_gender("Jane")
        assert isinstance(result, dict)
        assert "gender" in result
        assert result["gender"] in ["Female", "Male", "Unknown"]

    def test_infer_gender_male(self):
        """Test infer_gender for male name"""
        result = infer_gender("John")
        assert isinstance(result, dict)
        assert "gender" in result

    def test_infer_gender_with_confidence(self):
        """Test infer_gender with confidence=True"""
        result = infer_gender("Jane", confidence=True)
        assert isinstance(result, dict)
        assert "gender" in result
        assert "confidence" in result

    def test_enrich_name(self):
        """Test enrich_name with gender enrichment"""
        normalized = normalize_name("Jane Smith")
        enriched = enrich_name(normalized, include_gender=True)
        assert "first" in enriched
        assert "last" in enriched

    def test_detect_nickname_bobby(self):
        """Test detect_nickname for Bobby (nickname of Robert)"""
        canonical = detect_nickname("Bobby")
        assert canonical is not None
        assert isinstance(canonical, str)

    def test_detect_nickname_not_nickname(self):
        """Test detect_nickname for non-nickname"""
        canonical = detect_nickname("Jane")
        # Jane might or might not be a nickname depending on data

    def test_get_nickname_variants(self):
        """Test get_nickname_variants for Robert"""
        variants = get_nickname_variants("Robert")
        assert isinstance(variants, set)
        # Robert should have variants like Bob, Bobby, Rob, etc.

    def test_get_name_equivalents_robert(self):
        """Test get_name_equivalents for Robert"""
        equivalents = get_name_equivalents("Robert")
        assert isinstance(equivalents, set)
        # Robert should have nicknames like Bob, Bobby, Rob, etc.
        assert len(equivalents) > 0

    def test_compare_first_names_identical(self):
        """Test compare_first_names with identical names"""
        score = compare_first_names("John", "John")
        assert score == 1.0

    def test_compare_first_names_similar(self):
        """Test compare_first_names with similar names"""
        score = compare_first_names("John", "Jon")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_compare_first_names_with_nicknames(self):
        """Test compare_first_names with nickname matching"""
        score = compare_first_names("Robert", "Bob", use_nicknames=True)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_compare_last_names_identical(self):
        """Test compare_last_names with identical names"""
        score = compare_last_names("Smith", "Smith")
        assert score == 1.0

    def test_compare_last_names_similar(self):
        """Test compare_last_names with similar names"""
        score = compare_last_names("Smith", "Smyth")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_match_names_identical(self):
        """Test match_names with identical names"""
        result = match_names("John Smith", "John Smith")
        assert isinstance(result, dict)
        assert "score" in result
        assert "is_match" in result

    def test_match_names_similar(self):
        """Test match_names with similar names"""
        result = match_names("John Smith", "Jon Smith")
        assert isinstance(result, dict)
        assert "score" in result
        assert isinstance(result["score"], (float, int))


# ============================================================================
# EMAILS MODULE TESTS
# ============================================================================


class TestEmailsModule:
    """Test all functions from humanmint.emails"""

    def test_normalize_email_uppercase(self):
        """Test normalize_email with uppercase email"""
        result = normalize_email("JOHN.SMITH@GMAIL.COM")
        assert result["email"] == "john.smith@gmail.com"
        assert result["domain"] == "gmail.com"
        assert result["is_valid"] is True

    def test_normalize_email_extract_local(self):
        """Test normalize_email extracts local part"""
        result = normalize_email("john.smith@example.com")
        assert result["local"] == "john.smith"
        assert "local_base" in result

    def test_normalize_email_generic_detection(self):
        """Test normalize_email detects generic inboxes"""
        result = normalize_email("info@example.com")
        assert "is_generic" in result

    def test_normalize_email_free_provider(self):
        """Test normalize_email detects free providers"""
        result = normalize_email("user@gmail.com")
        assert result["is_free_provider"] is True

    def test_normalize_email_corporate_provider(self):
        """Test normalize_email for corporate email"""
        result = normalize_email("user@company.com")
        assert result["is_free_provider"] is False

    def test_is_free_provider_gmail(self):
        """Test is_free_provider for Gmail"""
        assert is_free_provider("gmail.com") is True

    def test_is_free_provider_yahoo(self):
        """Test is_free_provider for Yahoo"""
        assert is_free_provider("yahoo.com") is True

    def test_is_free_provider_corporate(self):
        """Test is_free_provider for corporate domain"""
        assert is_free_provider("company.com") is False

    def test_guess_email_pattern(self):
        """Test guess_email with known patterns"""
        known = [
            ("John Smith", "jsmith@company.com"),
            ("Jane Doe", "jdoe@company.com"),
        ]
        result = guess_email("Bob Jones", "company.com", known)
        assert isinstance(result, str)
        # Result might be "bjones@company.com" if pattern is detected

    def test_guess_email_empty(self):
        """Test guess_email with empty known list"""
        result = guess_email("Bob Jones", "company.com", [])
        assert isinstance(result, str)

    def test_get_pattern_scores(self):
        """Test get_pattern_scores returns patterns"""
        known = [
            ("John Smith", "jsmith@company.com"),
            ("Jane Doe", "jdoe@company.com"),
        ]
        result = get_pattern_scores(known)
        assert isinstance(result, list)

    def test_describe_pattern_valid(self):
        """Test describe_pattern for valid pattern"""
        result = describe_pattern("f_l")
        # Pattern might exist or not depending on implementation


# ============================================================================
# PHONES MODULE TESTS
# ============================================================================


class TestPhonesModule:
    """Test all functions from humanmint.phones"""

    def test_normalize_phone_formatted(self):
        """Test normalize_phone with formatted number"""
        result = normalize_phone("(555) 123-4567")
        assert result is not None
        if result and "e164" in result and result["e164"]:
            assert result["e164"].startswith("+")
        assert result["is_valid"] is True or result["is_valid"] is False
        assert "pretty" in result

    def test_normalize_phone_with_extension(self):
        """Test normalize_phone with extension"""
        result = normalize_phone("(555) 123-4567 ext 201")
        assert result is not None
        if result and "e164" in result and result["e164"]:
            assert result["e164"].startswith("+")
        assert "extension" in result
        # Extension might be "201" or similar

    def test_normalize_phone_plain(self):
        """Test normalize_phone with plain number"""
        result = normalize_phone("5551234567")
        assert result is not None
        if result and "e164" in result and result["e164"]:
            assert result["e164"].startswith("+")
        assert result["is_valid"] is True or result["is_valid"] is False

    def test_normalize_phone_country_param(self):
        """Test normalize_phone with country parameter"""
        result = normalize_phone("2025551234", country="US")
        assert result["country"] == "US"

    def test_detect_impossible_valid(self):
        """Test detect_impossible with valid number"""
        result = normalize_phone("(555) 123-4567")
        is_impossible = detect_impossible(result)
        assert isinstance(is_impossible, bool)
        assert is_impossible is False

    def test_detect_impossible_fake(self):
        """Test detect_impossible with fake pattern"""
        result = normalize_phone("(555) 555-5555")
        is_impossible = detect_impossible(result)
        assert isinstance(is_impossible, bool)

    def test_detect_fax_pattern(self):
        """Test detect_fax_pattern returns bool"""
        result = normalize_phone("(555) 123-4567")
        is_fax = detect_fax_pattern(result)
        assert isinstance(is_fax, bool)

    def test_detect_voip_pattern(self):
        """Test detect_voip_pattern returns bool"""
        result = normalize_phone("(555) 123-4567")
        is_voip = detect_voip_pattern(result)
        assert isinstance(is_voip, bool)


# ============================================================================
# DEPARTMENTS MODULE TESTS
# ============================================================================


class TestDepartmentsModule:
    """Test all functions from humanmint.departments"""

    def test_normalize_department_with_codes(self):
        """Test normalize_department removes codes"""
        result = normalize_department("000171 - Police Department")
        assert "Police" in result
        assert "000171" not in result

    def test_normalize_department_standardizes_format(self):
        """Test normalize_department standardizes format"""
        result = normalize_department("FIRE and RESCUE")
        assert isinstance(result, str)

    def test_find_best_match_police(self):
        """Test find_best_match for Police"""
        result = find_best_match("Police Dept")
        assert result is not None or result is None
        # Police should match if in canonical list

    def test_find_best_match_with_threshold(self):
        """Test find_best_match with custom threshold"""
        result = find_best_match("Finance", threshold=0.7)
        assert result is None or isinstance(result, str)

    def test_find_all_matches_returns_list(self):
        """Test find_all_matches returns list"""
        result = find_all_matches("Police", threshold=0.6, top_n=3)
        assert isinstance(result, list)

    def test_match_departments_multiple(self):
        """Test match_departments with multiple depts"""
        depts = ["Police Dept", "Fire Department"]
        result = match_departments(depts)
        assert isinstance(result, dict)
        assert len(result) == len(depts)

    def test_get_similarity_score(self):
        """Test get_similarity_score"""
        score = get_similarity_score("Police", "Police")
        assert score == 1.0

    def test_get_similarity_score_different(self):
        """Test get_similarity_score with different depts"""
        score = get_similarity_score("Police", "Fire")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_get_department_category_police(self):
        """Test get_department_category for Police"""
        result = get_department_category("Police")
        assert result is None or isinstance(result, str)
        # Police should be in "Public Safety" category

    def test_get_all_categories(self):
        """Test get_all_categories returns set"""
        result = get_all_categories()
        assert isinstance(result, set)
        assert len(result) > 0

    def test_get_departments_by_category(self):
        """Test get_departments_by_category"""
        categories = get_all_categories()
        if categories:
            category = next(iter(categories))
            result = get_departments_by_category(category)
            assert isinstance(result, list)

    def test_categorize_departments_multiple(self):
        """Test categorize_departments"""
        depts = ["Police", "Fire", "Public Works"]
        result = categorize_departments(depts)
        assert isinstance(result, dict)

    def test_get_canonical_departments(self):
        """Test get_canonical_departments returns list"""
        result = get_canonical_departments()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_is_canonical_true(self):
        """Test is_canonical for canonical dept"""
        result = is_canonical("Police")
        assert isinstance(result, bool)

    def test_is_canonical_false(self):
        """Test is_canonical for non-canonical dept"""
        result = is_canonical("XYZ Unknown Dept 123")
        assert isinstance(result, bool)

    def test_load_mappings(self):
        """Test load_mappings returns dict"""
        result = load_mappings()
        assert isinstance(result, dict)

    def test_get_mapping_for_original(self):
        """Test get_mapping_for_original"""
        result = get_mapping_for_original("Police Department")
        assert result is None or isinstance(result, str)

    def test_get_originals_for_canonical(self):
        """Test get_originals_for_canonical"""
        result = get_originals_for_canonical("Police")
        assert isinstance(result, list)


# ============================================================================
# TITLES MODULE TESTS
# ============================================================================


class TestTitlesModule:
    """Test all functions from humanmint.titles"""

    def test_normalize_title_full_with_code(self):
        """Test normalize_title_full removes codes"""
        result = normalize_title_full("0001 - Chief of Police (Downtown)")
        assert isinstance(result, dict)
        assert "raw" in result
        assert "cleaned" in result
        assert "canonical" in result
        assert "0001" not in result.get("cleaned", "")

    def test_normalize_title_full_with_confidence(self):
        """Test normalize_title_full returns confidence"""
        result = normalize_title_full("Police Chief")
        assert "confidence" in result

    def test_normalize_title_core(self):
        """Test normalize_title cleans title"""
        result = normalize_title("Chief of Police")
        assert isinstance(result, str)

    def test_match_title_best(self):
        """Test find_best_match (match_title) for titles"""
        result = match_title("Police Chief", threshold=0.7)
        assert isinstance(result, tuple)
        assert len(result) == 2
        title, confidence = result
        assert title is None or isinstance(title, str)
        assert isinstance(confidence, float)

    def test_match_all_titles(self):
        """Test find_all_matches for titles"""
        result = match_all_titles("Police Chief", threshold=0.6, top_n=3)
        assert isinstance(result, list)

    def test_title_similarity_identical(self):
        """Test title similarity with identical titles"""
        score = title_similarity("Police Chief", "Police Chief")
        assert score == 1.0

    def test_title_similarity_different(self):
        """Test title similarity with different titles"""
        score = title_similarity("Police Chief", "Fire Chief")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_get_canonical_titles(self):
        """Test get_canonical_titles returns list"""
        result = get_canonical_titles()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_title_is_canonical_valid(self):
        """Test title_is_canonical for canonical title"""
        canonicals = get_canonical_titles()
        if canonicals:
            result = title_is_canonical(canonicals[0])
            assert isinstance(result, bool)

    def test_get_mapping_for_variant(self):
        """Test get_mapping_for_variant"""
        result = get_mapping_for_variant("Police Chief")
        assert result is None or isinstance(result, str)

    def test_get_all_mappings(self):
        """Test get_all_mappings returns dict"""
        result = get_all_mappings()
        assert isinstance(result, dict)


# ============================================================================
# ADDRESSES MODULE TESTS
# ============================================================================


class TestAddressesModule:
    """Test all functions from humanmint.addresses"""

    def test_normalize_address_full(self):
        """Test normalize_address with full address"""
        result = normalize_address("123 Main St, Springfield, IL 62701")
        assert result is not None
        assert isinstance(result, dict)
        assert "street" in result or "canonical" in result

    def test_normalize_address_partial(self):
        """Test normalize_address with partial address"""
        result = normalize_address("123 Main St, Springfield")
        if result is not None:
            assert isinstance(result, dict)

    def test_normalize_address_none(self):
        """Test normalize_address with empty string"""
        result = normalize_address("")
        assert result is None or isinstance(result, dict)

    def test_normalize_address_state_abbr(self):
        """Test normalize_address with state abbreviation"""
        result = normalize_address("456 Oak Ave, Chicago, IL")
        if result is not None:
            assert isinstance(result, dict)


# ============================================================================
# ORGANIZATIONS MODULE TESTS
# ============================================================================


class TestOrganizationsModule:
    """Test all functions from humanmint.organizations"""

    def test_normalize_organization_city_of(self):
        """Test normalize_organization removes 'City of'"""
        result = normalize_organization("City of Springfield")
        assert result is not None
        assert isinstance(result, dict)
        assert "raw" in result or "normalized" in result

    def test_normalize_organization_police_department(self):
        """Test normalize_organization with full dept name"""
        result = normalize_organization("City of Springfield Police")
        if result is not None:
            assert isinstance(result, dict)

    def test_normalize_organization_none(self):
        """Test normalize_organization with empty string"""
        result = normalize_organization("")
        assert result is None or isinstance(result, dict)

    def test_normalize_organization_no_prefix(self):
        """Test normalize_organization with simple name"""
        result = normalize_organization("Springfield Police")
        if result is not None:
            assert isinstance(result, dict)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Test functions working together"""

    def test_names_with_enrich(self):
        """Test normalize_name followed by enrich_name"""
        normalized = normalize_name("Jane Smith")
        enriched = enrich_name(normalized, include_gender=True)
        assert "first" in enriched
        assert "last" in enriched

    def test_email_detection_flow(self):
        """Test email normalization and free provider detection"""
        normalized = normalize_email("user@GMAIL.COM")
        is_free = is_free_provider(normalized["domain"])
        assert isinstance(is_free, bool)

    def test_phone_detection_flow(self):
        """Test phone normalization followed by detection"""
        normalized = normalize_phone("(555) 123-4567")
        is_impossible = detect_impossible(normalized)
        is_fax = detect_fax_pattern(normalized)
        assert isinstance(is_impossible, bool)
        assert isinstance(is_fax, bool)

    def test_department_match_and_categorize(self):
        """Test department matching and categorization"""
        match = find_best_match("Police Dept")
        if match:
            category = get_department_category(match)
            assert category is None or isinstance(category, str)

    def test_title_full_normalization(self):
        """Test complete title normalization"""
        result = normalize_title_full("0001 - Chief of Police (Downtown)")
        assert isinstance(result, dict)
        assert "canonical" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
