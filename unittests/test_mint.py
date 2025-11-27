from humanmint import mint


def test_mint_facade_full_record():
    contact = {
        "name": "John Michael Smith",
        "email": "john.smith@city.gov",
        "phone": "(650) 253-0000",
        "department": "Public Works 850-123-1234 ext 200",
    }

    result = mint(**contact)

    assert result.department["canonical"] == "Public Works"
    assert result.department["category"] == "infrastructure"
    assert result.phone["pretty"] == "+1 650-253-0000"
    assert result.name["first"] == "John"
    assert result.name["last"] == "Smith"
    assert result.name["gender"] in {"male", "female", "unknown"}


def test_mint_gracefully_handles_invalid_fields():
    result = mint(name="", email="not-an-email", phone="abc", department="")

    assert result.name is None
    assert result.email is not None and not result.email["is_valid"]
    assert result.phone is not None and not result.phone["is_valid"]
    assert result.department is None
