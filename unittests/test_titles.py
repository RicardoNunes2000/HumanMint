from humanmint.titles.normalize import normalize_title


def test_normalize_title_preserves_stopwords_and_caps():
    cleaned = normalize_title("Dir of Operations (PW)")

    # Dir is expanded to Director as part of abbreviation expansion
    assert cleaned == "Director of Operations"


def test_normalize_title_keeps_short_abbreviations_uppercase():
    cleaned = normalize_title("Sr. Manager - PW")

    assert cleaned.endswith("PW")


def test_normalize_title_marks_functional_roles_valid_without_canonical():
    from humanmint.titles.api import normalize_title_full

    res = normalize_title_full("Program Supervisor")
    assert res["is_valid"] is True
    assert res["canonical"] == "program supervisor"
