from humanmint.phones import normalize_phone


def test_normalize_phone_formats_us_numbers_and_extension():
    result = normalize_phone("650-253-0000 x123", country="US")

    assert result["is_valid"] is True
    assert result["pretty"] == "+1 650-253-0000"
    assert result["extension"] == "123"
    assert result["country"] == "US"


def test_normalize_phone_rejects_invalid_inputs():
    result = normalize_phone("not-a-number", country="US")

    assert result["is_valid"] is False
    assert result["e164"] is None


def test_normalize_phone_handles_spelled_out_extension():
    result = normalize_phone("555-1234 EXTENSION 77", country="US")

    assert result["extension"] == "77"
    assert result["is_valid"] is False
    assert result["e164"] is None


def test_normalize_phone_accepts_international_numbers():
    cases = {
        "+91 98765 43210": ("+919876543210", "IN"),
        "+33 1 23 45 67 89": ("+33123456789", "FR"),
        "+34 600 12 34 56": ("+34600123456", "ES"),
        "+52 55 1234 5678": ("+525512345678", "MX"),
    }
    for raw, (expected_e164, expected_country) in cases.items():
        result = normalize_phone(raw, country="US")
        assert result["is_valid"] is True
        assert result["e164"] == expected_e164
        assert result["country"] == expected_country


def test_normalize_phone_preserves_raw_when_invalid():
    result = normalize_phone("++999 0000", country="US")

    assert result["is_valid"] is False
    assert result["pretty"] == "++999 0000"


def test_normalize_org_trailing_ampersand_is_trimmed():
    from humanmint.organizations import normalize_organization

    org = normalize_organization("Merck & Co.")
    assert org["canonical"] == "Merck"
