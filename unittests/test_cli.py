import csv
from pathlib import Path

from humanmint.cli import clean_csv


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_cli_auto_guess(tmp_path: Path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    rows = [
        {
            "Full_Name": "Jane Doe",
            "Email": "jane.doe@city.gov",
            "Phone": "(415) 555-0100",
            "Dept": "Police",
            "Title": "Police Chief",
        }
    ]

    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    clean_csv(input_path, output_path)

    data = _read_csv(output_path)
    assert data[0]["hm_email"] == "jane.doe@city.gov"
    assert data[0]["hm_department"] == "Police"
    assert data[0]["hm_phone"] is not None
    assert data[0]["hm_title_canonical"].lower() in {"police chief", "chief of police"}


def test_cli_explicit_columns(tmp_path: Path):
    input_path = tmp_path / "input2.csv"
    output_path = tmp_path / "output2.csv"

    rows = [
        {
            "col_a": "Alex Rivera",
            "col_b": "alex.rivera@transport.city.gov",
            "col_c": "555-404-2020",
            "col_d": "Transportation Services",
            "col_e": "Transportation Planner",
        }
    ]

    with input_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    clean_csv(
        input_path,
        output_path,
        name_col="col_a",
        email_col="col_b",
        phone_col="col_c",
        dept_col="col_d",
        title_col="col_e",
    )

    data = _read_csv(output_path)
    assert data[0]["hm_email"] == "alex.rivera@transport.city.gov"
    assert data[0]["hm_department"] == "Transportation Services"
    assert data[0]["hm_title_canonical"]
