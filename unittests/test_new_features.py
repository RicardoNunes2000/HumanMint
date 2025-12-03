import pytest

from humanmint import extract_phones, mint


def test_manager_seniority_variants():
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
    res = mint(phone="888-555-1234")
    assert res.phone_type == "TOLL_FREE"
    assert res.phone_time_zones is None


def test_extract_phones_from_text():
    text = "Call me at 510-748-8230 if it's before 9:30, or on 703-4800500 after 10am."
    matches = extract_phones(text, region="US")
    e164s = {m.get("e164") for m in matches}
    assert {"+15107488230", "+17034800500"} <= e164s


def test_phone_metadata_location_and_time_zone():
    res = mint(phone="+1 415-555-8899 x204")
    assert res.phone_is_valid is True
    assert res.phone_location is None or "CA" in res.phone_location or "California" in res.phone_location
    assert res.phone_time_zones is None or any("America" in tz for tz in res.phone_time_zones)


def test_long_phone_with_text_extraction():
    noisy = "Call us today at 415.392.1234! " + ("extra digits " * 5)
    res = mint(phone=noisy)
    assert res.phone_pretty is not None
    assert "415" in (res.phone_pretty or "")


def test_salutation_with_accents():
    res = mint(name="Renée Smith")
    assert res.name_salutation in {"Ms.", "Mr.", "Mx."} or res.name_salutation is None
    # At minimum, ensure name parsed
    assert res.name_standardized is not None
