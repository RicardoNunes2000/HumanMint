import sys

sys.path.insert(0, "src")

from humanmint import mint, compare


# -------------------------
# CORE HIGH-SIMILARITY CASES
# -------------------------


def test_compare_high_similarity_basic():
    a = mint(
        name="Jane Doe",
        email="jane@example.com",
        phone="+1 202 555 0101",
        department="Public Works",
        title="Engineer",
    )
    b = mint(
        name="J. Doe",
        email="JANE@example.com",
        phone="202-555-0101",
        department="Public Works Dept",
        title="Public Works Engineer",
    )
    assert compare(a, b) > 80


def test_compare_name_initials():
    a = mint(name="Robert J. Thompson")
    b = mint(name="R. Thompson")
    assert compare(a, b) > 70


def test_compare_middle_name_variation():
    a = mint(name="John Alexander Smith")
    b = mint(name="John A. Smith")
    assert compare(a, b) > 85


def test_compare_hyphenated_last_name():
    a = mint(name="Maria Lopez-Santos")
    b = mint(name="Maria Lopez Santos")
    assert compare(a, b) > 75


def test_compare_accented_vs_unaccented():
    a = mint(name="José Ramírez")
    b = mint(name="Jose Ramirez")
    assert compare(a, b) > 80


# -------------------------
# EMAIL-MATCH DRIVEN CASES
# -------------------------


def test_compare_email_exact_match():
    a = mint(email="sara.lee@city.gov")
    b = mint(email="sara.lee@city.gov")
    assert compare(a, b) > 95


def test_compare_email_same_user_different_casing():
    a = mint(email="JOHN.SMITH@CITY.GOV")
    b = mint(email="john.smith@city.gov")
    assert compare(a, b) > 95


def test_compare_email_same_domain_different_user():
    a = mint(email="alex@city.gov")
    b = mint(email="michael@city.gov")
    assert compare(a, b) < 40


def test_compare_email_missing_one_side():
    a = mint(email="linda@city.gov", name="Linda Park")
    b = mint(name="Linda Park")
    assert compare(a, b) > 60


# -------------------------
# PHONE-BASED MATCHES
# -------------------------


def test_compare_phone_exact():
    a = mint(phone="202-555-7711")
    b = mint(phone="+1 202 555 7711")
    assert compare(a, b) > 90


def test_compare_phone_extension_ignored():
    a = mint(phone="202-555-7711 x200")
    b = mint(phone="202-555-7711")
    assert compare(a, b) > 75


def test_compare_phone_different():
    a = mint(phone="202-555-7711")
    b = mint(phone="415-555-9988")
    assert compare(a, b) < 40


# -------------------------
# DEPARTMENT / TITLE MATCHES
# -------------------------


def test_compare_department_canonical_match():
    a = mint(department="Public Works Division")
    b = mint(department="Dept of Public Works")
    assert compare(a, b) > 70


def test_compare_title_fuzzy_match():
    a = mint(title="Chief of Police")
    b = mint(title="Police Chief")
    assert compare(a, b) > 85


def test_compare_department_totally_different():
    a = mint(department="Police Department")
    b = mint(department="Parks and Recreation")
    assert compare(a, b) < 40


# -------------------------
# FULL CONTACT REALISTIC MATCHES
# -------------------------


def test_compare_full_contact_realistic():
    a = mint(
        name="Michael T. Johnson",
        email="mjohnson@springfield.gov",
        phone="(413) 555-9001",
        department="Public Works",
        title="Operations Manager",
    )

    b = mint(
        name="Mike Johnson",
        email="MJOHNSON@SPRINGFIELD.GOV",
        phone="+1 413 555 9001",
        department="PW Dept",
        title="Public Works Operations Manager",
    )

    assert compare(a, b) > 85


# -------------------------
# LOW SIMILARITY / NEGATIVE TESTS
# -------------------------


def test_compare_completely_different_people():
    a = mint(name="Alice Smith", email="alice@example.com")
    b = mint(name="Bob Johnson", email="bob@other.com")
    assert compare(a, b) < 30


def test_compare_name_collision_but_different_context():
    a = mint(name="John Adams", department="Police Department")
    b = mint(name="John Adams", department="Finance Department")
    assert compare(a, b) < 70  # same name, different roles/contexts


def test_compare_same_name_but_different_emails_domains():
    a = mint(name="Michael Chen", email="mchen@lapd.gov")
    b = mint(name="Michael Chen", email="mchen@finance.city.gov")
    assert compare(a, b) < 60


# -------------------------
# EDGE CASES
# -------------------------


def test_compare_empty_records():
    a = mint()
    b = mint()
    assert compare(a, b) == 0


def test_compare_only_last_name_shared():
    a = mint(name="Daniel Roberts")
    b = mint(name="Emily Roberts")
    assert 20 < compare(a, b) < 60  # some overlap, not same person


def test_compare_first_name_shared():
    a = mint(name="James Carter")
    b = mint(name="James Kelly")
    assert compare(a, b) < 55


def test_compare_missing_everything():
    a = mint()
    b = mint(name="John Doe")
    assert compare(a, b) < 10


# -------------------------
# ADDITIONAL REAL-WORLD & EDGE-CASE TESTS
# -------------------------


def test_compare_name_with_prefix_suffix():
    a = mint(name="Dr. Samantha Lee Jr.")
    b = mint(name="Samantha Lee")
    assert compare(a, b) > 75


def test_compare_name_with_order_swapped():
    a = mint(name="Lopez Maria")
    b = mint(name="Maria Lopez")
    assert compare(a, b) > 80


def test_compare_unicode_normalization():
    a = mint(name="Łukasz Kowalski")
    b = mint(name="Lukasz Kowalski")
    assert compare(a, b) > 75


def test_compare_messy_whitespace_and_punctuation():
    a = mint(name="  John   P.   Doe !! ")
    b = mint(name="John P Doe")
    assert compare(a, b) > 80


def test_compare_department_with_noise_tokens():
    a = mint(department="### Dept. of Finance ###")
    b = mint(department="Finance Department")
    assert compare(a, b) > 70


def test_compare_title_with_parenthesis():
    a = mint(title="Director (Interim)")
    b = mint(title="Interim Director")
    assert compare(a, b) > 80


def test_compare_corrupted_email_trailing_chars():
    a = mint(email="carlos@city.gov   ")
    b = mint(email="carlos@city.gov")
    assert compare(a, b) > 90


def test_compare_email_plus_alias():
    a = mint(email="sara+hr@city.gov")
    b = mint(email="sara@city.gov")
    assert compare(a, b) > 90


def test_compare_phone_with_country_missing():
    a = mint(phone="4155559000")
    b = mint(phone="+1 415 555 9000")
    assert compare(a, b) > 85


def test_compare_phone_with_text_noise():
    a = mint(phone="Tel: (415) 555-1234 ext.22")
    b = mint(phone="415-555-1234")
    assert compare(a, b) > 70


def test_compare_mixed_good_and_bad_signals():
    a = mint(
        name="John Michaels",
        email="jmichaels@city.gov",
        department="Public Works",
    )
    b = mint(
        name="John M. Michaels",
        email="jmich@other.gov",
        department="Finance",
    )
    score = compare(a, b)
    assert 40 < score < 80  # name pushes up, email/domain/department pull down


def test_compare_different_people_same_department():
    a = mint(name="Mark Green", department="IT")
    b = mint(name="Julia Green", department="IT")
    assert compare(a, b) < 50


def test_compare_same_person_different_title_seniority():
    a = mint(title="Manager")
    b = mint(title="Senior Manager")
    assert compare(a, b) > 60


def test_compare_similar_titles_but_different_domain():
    a = mint(title="Fire Chief")
    b = mint(title="Chief Financial Officer")
    assert compare(a, b) < 40


def test_compare_people_with_same_initials_but_not_same():
    a = mint(name="A. Johnson")
    b = mint(name="Adam Johansson")
    assert compare(a, b) < 60


def test_compare_mismatch_email_but_exact_name():
    a = mint(name="Hannah Lee", email="hannahl@schools.gov")
    b = mint(name="Hannah Lee", email="hlee@finance.gov")
    assert compare(a, b) < 70


def test_compare_department_abbreviation():
    a = mint(department="HR")
    b = mint(department="Human Resources")
    assert compare(a, b) > 70


def test_compare_role_specialization_vs_generic():
    a = mint(title="Deputy Fire Marshal")
    b = mint(title="Fire Marshal")
    assert compare(a, b) > 65


def test_compare_name_reversed_and_extra_middle():
    a = mint(name="Christopher Paul Jenkins")
    b = mint(name="Jenkins, Chris P.")
    assert compare(a, b) > 80


def test_compare_name_script_mixing():
    a = mint(name="Аndrew Miller")  # first A is Cyrillic
    b = mint(name="Andrew Miller")
    assert compare(a, b) > 60


def test_compare_department_numeric_codes():
    a = mint(department="PW-200")
    b = mint(department="Public Works")
    assert compare(a, b) > 60


def test_compare_title_with_stopwords_removed():
    a = mint(title="Office of the Assistant Director")
    b = mint(title="Assistant Director")
    assert compare(a, b) > 70


def test_compare_name_misspelling_close():
    a = mint(name="Jonathan McKinley")
    b = mint(name="Johnathan McKinley")
    assert compare(a, b) > 70


def test_compare_name_misspelling_far():
    a = mint(name="Jonathan McKinley")
    b = mint(name="Jonas McKinney")
    assert compare(a, b) < 60


def test_compare_name_with_random_noise_tokens():
    a = mint(name="## John ## Walker ##")
    b = mint(name="John Walker")
    assert compare(a, b) > 80


def test_compare_full_contact_one_side_sparse():
    a = mint(name="Laura Chen", email="lchen@city.gov", phone="555-1200")
    b = mint(name="Laura Chen")
    assert compare(a, b) > 60


def test_compare_full_contact_with_conflicting_signals():
    a = mint(
        name="Brian Adams",
        email="badams@police.gov",
        department="Police",
        phone="202-555-1100",
    )
    b = mint(
        name="Brian Adams",
        email="b.adams@parks.gov",
        department="Parks",
        phone="202-555-9900",
    )
    # Name same, everything else disagree
    assert compare(a, b) < 70


# -------------------------
# CUSTOM WEIGHTS
# -------------------------


def test_compare_weights_default_is_used_when_missing():
    a = mint(name="Jane Doe", email="jane@example.com")
    b = mint(name="J. Doe", email="jane@example.com")
    assert compare(a, b) == compare(a, b, weights={})


def test_compare_custom_weights_emphasize_name():
    a = mint(name="Jane Doe", email="jane@example.com")
    b = mint(name="Jane Doe", email="jane@other.com")
    default_score = compare(a, b)
    custom_score = compare(a, b, weights={"name": 0.9, "email": 0.1})
    assert custom_score > default_score


def test_compare_name_only_weight():
    a = mint(name="Jane Doe", email="jane@example.com")
    b = mint(name="Jane Doe", email="jane@other.com")
    score = compare(
        a,
        b,
        weights={"name": 1.0, "email": 0.0, "phone": 0.0, "department": 0.0, "title": 0.0},
    )
    assert score >= 90


def test_compare_email_disabled_does_not_floor():
    a = mint(name="Alice Smith", email="shared@example.com")
    b = mint(name="Bob Johnson", email="shared@example.com")
    score = compare(
        a,
        b,
        weights={"name": 0.0, "email": 0.0, "phone": 0.0, "department": 0.0, "title": 0.0},
    )
    assert score == 0


def test_compare_email_only_weight():
    a = mint(name="Alice Smith", email="shared@example.com")
    b = mint(name="Bob Johnson", email="shared@example.com")
    score = compare(
        a,
        b,
        weights={"name": 0.0, "email": 1.0, "phone": 0.0, "department": 0.0, "title": 0.0},
    )
    assert score >= 90


def test_compare_department_penalty_respects_weight():
    a = mint(name="John Adams", department="Police Department")
    b = mint(name="John Adams", department="Finance Department")
    default_score = compare(a, b)
    no_dept_penalty_score = compare(
        a,
        b,
        weights={"name": 1.0, "email": 0.0, "phone": 0.0, "department": 0.0, "title": 0.0},
    )
    assert no_dept_penalty_score > default_score
