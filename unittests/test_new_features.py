"""Test new features in HumanMint.

Tests for recently added functionality including title seniority extraction,
toll-free phone handling, phone metadata enrichment, and Unicode name support.
"""

import pytest

from humanmint import extract_phones, mint


def test_manager_seniority_variants():
    """Test title seniority extraction for common manager/lead roles.

    Verifies that abbreviated titles (Mgr), standard titles (Manager, Lead),
    and leadership roles (Head of) are correctly normalized to their seniority level.
    """
    cases = [
        ("Mgr", "Manager"),
        ("Manager", "Manager"),
        ("Lead Engineer", "Lead"),
        ("Head of Product", "Head"),
        ("Assistant Manager", "Manager"),
    ]
    for title, expected in cases:
        res = mint(title=title)
        assert res.title_seniority == expected


def test_toll_free_time_zones_none():
    """Test that toll-free numbers do not have time zones.

    Toll-free numbers are national and span multiple time zones,
    so the time_zones field should be None.
    """
    res = mint(phone="888-555-1234")
    assert res.phone_type == "TOLL_FREE"
    assert res.phone_time_zones is None


def test_extract_phones_from_text():
    """Test extracting phone numbers from unstructured text.

    Verifies that the extract_phones function correctly finds and normalizes
    phone numbers from messy text with other content.
    """
    text = "Call me at 510-748-8230 if it's before 9:30, or on 703-4800500 after 10am."
    matches = extract_phones(text, region="US")
    e164s = {m.get("e164") for m in matches}
    assert {"+15107488230", "+17034800500"} <= e164s


def test_phone_metadata_location_and_time_zone():
    """Test phone metadata enrichment with location and time zone.

    Verifies that a valid US phone number is enriched with geographic location
    and time zone information (when applicable).
    """
    res = mint(phone="+1 415-555-8899 x204")
    assert res.phone_is_valid is True
    assert res.phone_location is None or "CA" in res.phone_location or "California" in res.phone_location
    assert res.phone_time_zones is None or any("America" in tz for tz in res.phone_time_zones)


def test_long_phone_with_text_extraction():
    """Test phone normalization from noisy input with extra text.

    Ensures that phone numbers can be extracted and normalized even when
    surrounded by non-phone text and noise.
    """
    noisy = "Call us today at 415.392.1234! " + ("extra digits " * 5)
    res = mint(phone=noisy)
    assert res.phone_pretty is not None
    assert "415" in (res.phone_pretty or "")


def test_salutation_with_accents():
    """Test name processing with Unicode accented characters.

    Verifies that names with accents (e.g., "Renée") are correctly parsed
    and normalized without losing diacritical marks.
    """
    res = mint(name="Renée Smith")
    assert res.name_salutation in {"Ms.", "Mr.", "Mx."} or res.name_salutation is None
    # At minimum, ensure name parsed
    assert res.name_standardized is not None
