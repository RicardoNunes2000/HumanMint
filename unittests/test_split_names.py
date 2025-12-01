import sys

sys.path.insert(0, "src")

from humanmint import mint


def test_split_two_people_shared_last_name():
    results = mint(name="John and Jane Smith", split_multi=True)
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0].name_first == "John"
    assert results[0].name_last == "Smith"
    assert results[1].name_first == "Jane"
    assert results[1].name_last == "Smith"


def test_split_two_people_with_titles():
    results = mint(name="Dr. Robert Jones & Mrs. Emily Jones", split_multi=True)
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0].name_last == "Jones"
    assert results[1].name_last == "Jones"


def test_split_falls_back_when_no_split_needed():
    result = mint(name="Single Person", split_multi=True)
    assert not isinstance(result, list)
    assert result.name_first == "Single"
