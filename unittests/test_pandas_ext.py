import pytest

pandas = pytest.importorskip("pandas")

import humanmint  # noqa: E402,F401
import humanmint.pandas as humanmint_pandas  # noqa: E402,F401  # ensures accessor registration


def test_accessor_auto_detects_common_columns():
    df = pandas.DataFrame(
        [
            {
                "Full_Name": "Jane Doe",
                "contact_email": "jane.doe@city.gov",
                "cell": "415-555-0100",
                "dept": "Police",
                "job_title": "Police Chief",
            },
            {
                "Full_Name": "John Smith",
                "contact_email": "john.smith@city.gov",
                "cell": "650-253-0000",
                "dept": "Public Works 850-123-1234",
                "job_title": "Director of Public Works",
            },
        ]
    )

    cleaned = df.humanmint.clean()

    # New columns exist
    for col in [
        "hm_name_full",
        "hm_name_first",
        "hm_email",
        "hm_phone",
        "hm_department",
        "hm_title_canonical",
    ]:
        assert col in cleaned.columns

    # Basic normalization expectations
    assert cleaned.loc[0, "hm_email"] == "jane.doe@city.gov"
    assert cleaned.loc[0, "hm_department"] == "Police"
    assert cleaned.loc[0, "hm_title_canonical"].lower() in {"police chief", "chief of police"}
    assert cleaned.loc[1, "hm_department"] == "Public Works"


def test_accessor_respects_explicit_columns():
    df = pandas.DataFrame(
        [
            {
                "col_a": "Alex Rivera",
                "col_b": "alex.rivera@transport.city.gov",
                "col_c": "555-404-2020",
                "col_d": "Transportation Services",
                "col_e": "Transportation Planner",
            }
        ]
    )

    cleaned = df.humanmint.clean(
        name_col="col_a",
        email_col="col_b",
        phone_col="col_c",
        dept_col="col_d",
        title_col="col_e",
        cols=df.columns,  # restrict detection to provided columns
    )

    assert cleaned.loc[0, "hm_email"] == "alex.rivera@transport.city.gov"
    assert cleaned.loc[0, "hm_department"] == "Transportation Services"
    assert cleaned.loc[0, "hm_title_canonical"]
    assert "hm_phone" in cleaned.columns
    # Original data preserved
    assert cleaned.loc[0, "col_a"] == "Alex Rivera"
