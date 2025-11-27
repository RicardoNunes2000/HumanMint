import sys

import pytest

# Ensure local src/ is importable
sys.path.insert(0, "src")

from humanmint import mint
from humanmint.departments import normalize_department
from humanmint.titles.api import normalize_title_full


def test_planning_overrides_district_noise():
    res = mint(department="Planning (Downtown District)")
    assert res.department["canonical"] == "Planning"
    assert res.department["category"] == "planning & development"


def test_housing_and_recorder_canonicals():
    housing = mint(department="Housing Department")
    recorder = mint(department="Recorder's Office")
    assert housing.department["canonical"] == "Housing"
    assert recorder.department["canonical"] == "Recorder"


def test_rank_in_name_is_not_parsed_as_name():
    res = mint(name="Battalion Chief Eric Stenson")
    assert res.name["first"] == "Eric"
    assert res.name["last"] == "Stenson"


def test_paralegal_and_rank_title_confidence():
    paralegal = normalize_title_full("Paralegal")
    captain = normalize_title_full("Captain", dept_canonical="Fire Department")
    assert paralegal["canonical"] == "paralegal"
    assert paralegal["is_valid"] is True
    assert paralegal["confidence"] >= 0.7
    assert captain["canonical"] == "fire captain"
    assert captain["confidence"] >= 0.7


def test_misc_title_and_department_cases():
    title = normalize_title_full("Epidemiologist")
    dept = normalize_department("Clerk's Office / Administration")
    assert title["canonical"] == "epidemiologist"
    assert title["is_valid"] is True
    assert dept.lower().startswith("clerk")
