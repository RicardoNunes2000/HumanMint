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
