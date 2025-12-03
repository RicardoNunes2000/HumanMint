from humanmint import mint


def test_raw_fields_are_preserved():
    result = mint(
        name="Jane Q. Public",
        email="jane.public@example.com",
        phone="202-555-0101",
        department="Accounting",
        title="Senior Analyst",
        address="123 Main St Apt 4B, Springfield, IL 62704",
        organization="USDA",
    )

    assert result.name and result.name.get("raw") == "Jane Q. Public"
    assert result.email and result.email.get("raw") == "jane.public@example.com"
    assert result.phone and result.phone.get("raw") == "202-555-0101"
    assert result.department and result.department.get("raw") == "Accounting"
    assert result.title and result.title.get("raw") == "Senior Analyst"
    assert result.address and result.address.get("raw") == "123 Main St Apt 4B, Springfield, IL 62704"
    assert result.organization and result.organization.get("raw") == "USDA"


def test_address_units_and_canonical_keep_unit_letters():
    addr = "Apt 4B, 500 5th Ave New York NY 10110"
    res = mint(address=addr)

    assert res.address
    # Unit should keep the letter suffix
    assert res.address.get("unit") == "Apt 4B"
    # Canonical should include the full unit string
    assert "Apt 4B" in (res.address.get("canonical") or "")
    # Raw should be preserved
    assert res.address.get("raw") == addr


def test_address_suite_first_and_smashed_keep_unit_and_street():
    smashed = "123MainSt Apt4B SpringfieldIL62704"
    res = mint(address=smashed)
    assert res.address
    assert res.address.get("street") and "123 Main St" in res.address.get("street")
    assert res.address.get("unit") and "4" in res.address.get("unit") and "B" in res.address.get("unit")
    assert res.address.get("city") == "Springfield"
    assert res.address.get("state") == "IL"
    assert res.address.get("zip") == "62704"

    suite_first = "Suite 100, 123 Main St Springfield IL 62704"
    res2 = mint(address=suite_first)
    assert res2.address
    assert res2.address.get("unit") == "Suite 100"
    assert "Suite 100" in (res2.address.get("canonical") or "")


def test_address_ordinals_not_split():
    res = mint(address="500 5th Ave New York NY 10110")
    assert res.address
    assert "5th Ave" in (res.address.get("canonical") or "")


def test_department_fallback_preserves_non_gov_text():
    res = mint(department="Accounting")
    assert res.department
    assert res.department.get("canonical") == "Accounting"


def test_name_double_space_and_nickname_parentheses():
    res = mint(name="Double  Space")
    assert res.name and res.name.get("is_valid") is True
    res2 = mint(name="William (Bill) Clinton")
    assert res2.name and res2.name.get("nickname", "").lower() == "bill"


def test_phone_label_stripping_keeps_number():
    res = mint(phone="(Home) 202-555-0101")
    assert res.phone
    assert "202" in (res.phone.get("pretty") or "")


def test_org_acronym_mapping_is_canonicalized():
    res = mint(organization="USDA")
    assert res.organization
    assert "Agriculture" in res.organization.get("canonical", "")
