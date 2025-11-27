from humanmint import mint


def test_us_address_sets_country():
    result = mint(address="123 N. Main St Apt #4B, Springfield, MA 01103")
    assert result.address
    assert result.address.get("country") == "US"
    assert result.address.get("state") == "MA"


def test_foreign_like_address_does_not_set_country():
    result = mint(address="42 Wallaby Way, Sydney NSW")
    assert result.address
    assert result.address.get("country") is None
    assert result.address.get("state") is None
    assert result.address.get("confidence") <= 0.5


def test_explicit_usa_indicator_sets_country():
    result = mint(address="123 Example Street, Ottawa, ON K1A0B1, Canada, USA")
    assert result.address
    assert result.address.get("country") == "US"
