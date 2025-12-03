from humanmint.emails import normalize_email


def test_normalize_email_parses_fields():
    result = normalize_email("john.smith@example.com")

    assert result["email"] == "john.smith@example.com"
    assert result["domain"] == "example.com"
    assert result["local_base"] == "john.smith"
    assert result["is_valid"] is True


def test_generic_inbox_detection_and_copies():
    inbox = normalize_email("info@company.org")
    again = normalize_email("info@company.org")

    assert inbox["is_generic"] is True
    assert inbox is not again  # cached path still returns fresh dict


def test_normalize_email_handles_anti_scraper_format():
    result = normalize_email("pat [at] city [dot] gov")

    assert result["email"] == "pat@city.gov"
    assert result["domain"] == "city.gov"
    assert result["is_valid"] is True


def test_normalize_email_rejects_name_like_input():
    result = normalize_email("John Smith")

    assert result["email"] is None
    assert result["is_valid"] is False
