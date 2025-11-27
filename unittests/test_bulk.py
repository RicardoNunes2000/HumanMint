import sys

sys.path.insert(0, "src")

from humanmint import mint, bulk


def test_bulk_processing():
    records = [
        {"name": "Jane Doe", "email": "jane@example.com"},
        {"name": "John Smith", "phone": "202-555-0101"},
    ]
    results = bulk(records, workers=2)
    assert len(results) == 2
    assert results[0].name["first"] == "Jane"
    assert results[1].phone["pretty"] is not None


def test_bulk_with_title_overrides():
    records = [
        {"title": "Chief Happiness Officer", "title_overrides": {"chief happiness officer": "employee experience director"}}
    ]
    res = bulk(records)[0]
    assert res.title["canonical"] == "employee experience director"
