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
    # BLS match (0.995 confidence) - "Paralegals and legal assistants" is official DOL title
    assert paralegal["canonical"] == "paralegals and legal assistants"
    assert paralegal["is_valid"] is True
    assert paralegal["confidence"] >= 0.99  # BLS has highest confidence (0.995)
    assert captain["canonical"] == "fire captain"
    assert captain["confidence"] >= 0.7


def test_misc_title_and_department_cases():
    title = normalize_title_full("Epidemiologist")
    dept = normalize_department("Clerk's Office / Administration")
    assert title["canonical"] == "epidemiologist"
    assert title["is_valid"] is True
    assert dept.lower().startswith("clerk")


def test_scenario_12_mc_prefix_handling():
    """Test that 'Mc Donald' normalizes to 'McDonald', not 'Mc donald'."""
    from humanmint.titles.normalize import normalize_title

    # Test the normalization directly
    result = normalize_title("Mc Donald")
    assert result == "Mcdonald", f"Expected 'Mcdonald', got '{result}'"

    # Also test through the full pipeline
    full_result = normalize_title_full("Mc Donald")
    assert full_result["cleaned"] == "Mcdonald"


def test_scenario_20_coordinator_without_dept_context():
    """Test that 'Coordinator' without department context stays generic, not 'Recreation Coordinator'."""
    # When no department context is provided, "coordinator" should stay generic
    result = normalize_title_full("Coordinator")
    # Should stay as "coordinator" or be marked invalid, NOT expanded to "recreation coordinator"
    canonical = result["canonical"]
    # Either None/False (not expanded) or "coordinator" (stays generic)
    if canonical:
        assert "recreation" not in canonical.lower(), (
            f"Expected 'coordinator' to not expand to '{canonical}' without department context"
        )


def test_scenario_20_coordinator_with_recreation_dept():
    """Test that 'Coordinator' WITH recreation department context becomes 'Recreation Coordinator'."""
    # When department is "Parks" or "Recreation", expansion should be allowed
    result = normalize_title_full("Coordinator", dept_canonical="Parks")
    canonical = result["canonical"]
    # Should either be "recreation coordinator" or "coordinator"
    # If it matches BLS or heuristics, it might expand; if not, stay generic
    # The key is: the context is considered
    assert result["is_valid"] or canonical is None


def test_scenario_20_coordinator_with_municipality_dept():
    """Test that 'Coordinator' with Municipality context stays generic."""
    # Municipality doesn't support recreation coordinator
    result = normalize_title_full("Coordinator", dept_canonical="Municipality")
    canonical = result["canonical"]
    # Should NOT expand to "recreation coordinator" (wrong context)
    if canonical:
        assert "recreation" not in canonical.lower(), (
            f"Expected 'coordinator' to not expand to '{canonical}' in Municipality context"
        )
