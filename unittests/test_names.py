from humanmint.names import enrich_name, normalize_name


def test_normalize_name_extracts_components():
    result = normalize_name("Dr. Michael Brown, PhD")

    assert result["first"] == "Michael"
    assert result["last"] == "Brown"
    assert result["suffix"] is None
    assert result["canonical"] == "michael brown"
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


def test_normalize_name_strips_ranks_and_badges():
    result = normalize_name("Sgt. Daniel Brooks #172")

    assert result["first"] == "Daniel"
    assert result["last"] == "Brooks"
    assert "172" not in result["full"]


def test_normalize_name_preserves_apostrophe_casing():
    result = normalize_name("Anne-Marie D'Angelo")

    assert result["last"] == "D'Angelo"


def test_normalize_name_drops_credentials_from_suffix():
    result = normalize_name("Brian J. Lopez, SHRM-CP")

    assert result["suffix"] is None
    assert result["full"] == "Brian J Lopez"


def test_normalize_name_strips_esq_suffix():
    result = normalize_name("MR. JOHN SMITH, ESQ.")

    assert result["first"] == "John"
    assert result["last"] == "Smith"
    assert result["suffix"] is None
    assert result["canonical"] == "john smith"
    assert result["full"] == "John Smith"


def test_normalize_name_unescapes_html_entities():
    result = normalize_name("Chief&nbsp;David")

    assert result["first"] == "David"
    assert result["last"] is None
    assert result["full"] == "David"


def test_normalize_name_handles_care_of_and_corporate():
    result = normalize_name("Waste Management Inc. c/o Tony Soprano")

    assert result["first"] == "Tony"
    assert result["last"] == "Soprano"
    assert result["suffix"] is None
    assert result["canonical"] == "tony soprano"


def test_normalize_name_handles_delimiter_format():
    result = normalize_name("public works director- vance, bob")

    assert result["first"] == "Bob"
    assert result["last"] == "Vance"
    assert result["canonical"] == "bob vance"


def test_normalize_name_handles_ocr_digits_and_role_prefix():
    from humanmint import mint

    res = mint(
        name="C0uncil  Member   J0hn  S.  D0e",
        title="District 4 Rep.",
        department="City  Council",
    )

    assert res.name_first == "John"
    assert res.name_last == "Doe"
    assert res.title_normalized is not None
    assert "Representative" in res.title_normalized


def test_title_chief_of_police_abbreviation():
    from humanmint import mint

    res = mint(
        name="Chief&nbsp;David&nbsp;O&#39;Connor",
        title="Chf. of Pol.",
        department="Pol. Dept.",
    )

    assert res.name_standardized == "David O'Connor"
    assert res.title_canonical and "police" in res.title_canonical
    assert res.title_normalized == "Chief of Police"


def test_org_like_strings_rejected_as_names():
    from humanmint import mint

    res = mint(name="Human Resources")
    assert res.name is None

    res = mint(name="Information Desk")
    assert res.name is None

    res = mint(name="General Services")
    assert res.name is None


def test_org_strings_rejected_with_city_board_library_support():
    from humanmint import mint

    assert mint(name="City of Austin").name is None
    assert mint(name="Board of Commissioners").name is None
    assert mint(name="The Library").name is None
    assert mint(name="Help Support").name is None


def test_title_placeholder_rejected():
    from humanmint import mint

    assert mint(name="Police Chief (Interim) - TBD").name is None


def test_mojibake_fixed_with_ftfy():
    from humanmint import mint

    res = mint(name="RenÃ© Descartes")
    assert res.name_first == "René"
    assert res.name_last == "Descartes"


def test_sql_injection_artifact_trailing_paren_removed():
    from humanmint import mint

    res = mint(name="Robert'); DROP TABLE students;--")
    assert res.name_first == "Robert"
    assert res.name_last == ""


def test_recursive_title_chain_picks_primary_role():
    from humanmint import mint

    res = mint(title="Exec. Asst. to the Deputy Dir. of Ops.")
    assert res.title_canonical is not None


def test_interim_director_prefix_stripped_from_name():
    from humanmint import mint

    res = mint(name="Interim Director Sarah Connor")
    assert res.name_first == "Sarah"
    assert res.name_last == "Connor"


def test_clerk_of_works_not_generic_clerk():
    from humanmint import mint

    res = mint(title="Clerk of the Works")
    assert res.title_canonical == "clerk of the works"


def test_chief_of_staff_not_demoted_to_mayor():
    from humanmint import mint

    res = mint(title="Chief of Staff to the Mayor")
    assert res.title_canonical == "chief of staff"


def test_placeholder_current_resident_and_system_admin_rejected():
    from humanmint import mint

    assert mint(name="Current Resident").name is None
    assert mint(name="Postal Customer").name is None
    assert mint(name="System Administrator").name is None


def test_normalize_name_handles_quoted_nickname():
    from humanmint import mint

    res = mint(name="OFC. JAMES 'JIMMY' O'CONNOR III")
    assert res.name_first == "James"
    assert res.name_middle is None  # nickname should not become middle
    assert res.name_suffix == "iii"
    assert res.name_nickname.lower() == "jimmy"
    assert res.name_standardized.lower() == "james o'connor iii"


def test_normalize_name_rejects_null_placeholder():
    result = normalize_name("NULL")
    assert result["is_valid"] is False
    assert result["full"] is None


def test_normalize_name_preserves_dotted_initials():
    result = normalize_name("O.J. Simpson")

    assert result["first"] == "O.J."
    assert result["last"] == "Simpson"
    assert result["full"] == "O.J. Simpson"


def test_normalize_name_preserves_mc_apostrophe_casing():
    result = normalize_name("Jamie McDonald's")

    assert result["last"] == "McDonald's"
    assert result["full"] == "Jamie McDonald's"


def test_normalize_name_handles_underscores_as_spaces():
    result = normalize_name("Jane_Doe")

    assert result["first"] == "Jane"
    assert result["last"] == "Doe"
    assert result["full"] == "Jane Doe"


def test_textual_ordinals_become_roman_suffix():
    result = normalize_name("Thurston Howell the Third")

    assert result["last"] == "Howell"
    assert result["suffix"] == "iii"
    assert result["full"] == "Thurston Howell III"

    result = normalize_name("Henry Ford the Fourth")
    assert result["suffix"] == "iv"
    assert result["full"] == "Henry Ford IV"
