from humanmint.names import enrich_name, normalize_name


def test_normalize_name_extracts_components():
    result = normalize_name("Dr. Michael Brown, PhD")

    assert result["first"] == "Michael"
    assert result["last"] == "Brown"
    assert result["suffix"] == "phd"
    assert result["canonical"] == "michael brown phd"
    assert result["is_valid"] is True


def test_enrich_name_adds_gender_without_side_effects():
    normalized = normalize_name("Jane Marie Doe")
    enriched = enrich_name(normalized)
    enriched_again = enrich_name(normalized)

    assert enriched["gender"] in {"Male", "Female", "Unknown"}
    assert enriched is not enriched_again


def test_normalize_name_strips_markup_and_embedded_phone():
    result = normalize_name("<b>Mrs. Linda  Parker</b> (Cell: 555-0202)")

    assert result["first"] == "Linda"
    assert result["last"] == "Parker"
    assert result["middle"] is None
    assert result["suffix"] is None
    assert result["full"] == "Linda Parker"


def test_normalize_name_handles_curly_apostrophes():
    result = normalize_name("Lt. Mark O\u2019Donnell")

    assert result["first"] == "Mark"
    assert result["last"] == "O'Donnell"
    assert result["full"] == "Mark O'Donnell"
