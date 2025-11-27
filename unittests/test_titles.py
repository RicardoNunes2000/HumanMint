from humanmint.titles.normalize import normalize_title


def test_normalize_title_preserves_stopwords_and_caps():
    cleaned = normalize_title("Dir of Operations (PW)")

    assert cleaned == "Dir of Operations"


def test_normalize_title_keeps_short_abbreviations_uppercase():
    cleaned = normalize_title("Sr. Manager - PW")

    assert cleaned.endswith("PW")
