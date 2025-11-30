from humanmint.departments import (find_best_match, get_all_categories,
                                   get_department_category,
                                   get_departments_by_category, load_mappings,
                                   normalize_department)
from humanmint.processors import process_department


def test_normalize_department_removes_noise():
    cleaned = normalize_department("000171 - Supervisor 850-123-1234 ext 200")
    assert cleaned == "Supervisor"


def test_normalize_department_strips_contact_and_emails():
    cleaned = normalize_department("Clerk Office - reach me at linda.parker@town.gov")
    assert cleaned == "Clerk Office"


def test_find_best_match_prefers_good_candidates():
    assert find_best_match("Water Utilities", threshold=0.5) == "Water"
    assert find_best_match("Police Department", threshold=0.5) == "Police"


def test_load_mappings_is_cached_and_reusable():
    first = load_mappings()
    second = load_mappings()
    assert first is second
    assert "Police" in first  # sanity check data loaded


def test_department_categories_available_and_grouped():
    categories = get_all_categories()
    assert "Public Safety" in categories
    safety_departments = get_departments_by_category("Public Safety")
    assert "Police" in safety_departments and "Fire" in safety_departments
    assert get_department_category("Police") == "Public Safety"


def test_location_like_department_does_not_force_canonical():
    result = process_department("Station #14 - Ladder Unit")

    assert result is not None
    assert result["normalized"] == "Station 14 Ladder Unit"
    assert result["canonical"] is None
    assert result["category"] is None


def test_normalize_department_preserves_slash_separators():
    cleaned = normalize_department("Police / Fire / Emergency Mgt")

    assert " / " in cleaned


def test_sheriff_office_maps_to_police():
    match = find_best_match("Sheriff's Office", threshold=0.5)

    assert match == "Sheriff"


def test_transit_ops_maps_to_transportation():
    match = find_best_match("Transit Operations Division", threshold=0.5)

    assert match == "Transportation Services"
