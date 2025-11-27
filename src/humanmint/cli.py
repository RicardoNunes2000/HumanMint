"""Command-line interface for HumanMint."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Optional

from .column_guess import COLUMN_GUESSES, guess_column
from .mint import mint


def _resolve_columns(
    headers: list[str],
    name_col: Optional[str],
    email_col: Optional[str],
    phone_col: Optional[str],
    dept_col: Optional[str],
    title_col: Optional[str],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Determine which columns to use, guessing when not provided."""
    name_col = guess_column(headers, name_col, COLUMN_GUESSES["name"])
    email_col = guess_column(headers, email_col, COLUMN_GUESSES["email"])
    phone_col = guess_column(headers, phone_col, COLUMN_GUESSES["phone"])
    dept_col = guess_column(headers, dept_col, COLUMN_GUESSES["department"])
    title_col = guess_column(headers, title_col, COLUMN_GUESSES["title"])
    return name_col, email_col, phone_col, dept_col, title_col


def clean_csv(
    input_file: Path,
    output_file: Path,
    name_col: Optional[str] = None,
    email_col: Optional[str] = None,
    phone_col: Optional[str] = None,
    dept_col: Optional[str] = None,
    title_col: Optional[str] = None,
) -> None:
    """Clean a CSV file using humanmint.mint."""
    with input_file.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        if reader.fieldnames is None:
            raise ValueError("Input CSV missing headers.")
        headers = reader.fieldnames

        (
            name_col,
            email_col,
            phone_col,
            dept_col,
            title_col,
        ) = _resolve_columns(headers, name_col, email_col, phone_col, dept_col, title_col)

        if not any([name_col, email_col, phone_col, dept_col, title_col]):
            raise ValueError(
                "No usable columns found. Provide explicit mappings via --name-col/--email-col/--phone-col/--dept-col/--title-col."
            )

        new_fields = [
            "hm_name_full",
            "hm_name_first",
            "hm_name_last",
            "hm_name_gender",
            "hm_email",
            "hm_email_domain",
            "hm_email_is_generic",
            "hm_phone",
            "hm_department",
            "hm_department_category",
            "hm_title_canonical",
            "hm_title_is_valid",
        ]
        fieldnames = headers + new_fields

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8", newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                result = mint(
                    name=row.get(name_col) if name_col else None,
                    email=row.get(email_col) if email_col else None,
                    phone=row.get(phone_col) if phone_col else None,
                    department=row.get(dept_col) if dept_col else None,
                    title=row.get(title_col) if title_col else None,
                )

                row.update(
                    {
                        "hm_name_full": (result.name or {}).get("full") if result.name else None,
                        "hm_name_first": (result.name or {}).get("first") if result.name else None,
                        "hm_name_last": (result.name or {}).get("last") if result.name else None,
                        "hm_name_gender": (result.name or {}).get("gender") if result.name else None,
                        "hm_email": (result.email or {}).get("normalized") if result.email else None,
                        "hm_email_domain": (result.email or {}).get("domain") if result.email else None,
                        "hm_email_is_generic": (result.email or {}).get("is_generic") if result.email else None,
                        "hm_phone": (result.phone or {}).get("pretty") if result.phone else None,
                        "hm_department": (result.department or {}).get("canonical") if result.department else None,
                        "hm_department_category": (result.department or {}).get("category") if result.department else None,
                        "hm_title_canonical": (result.title or {}).get("canonical") if result.title else None,
                        "hm_title_is_valid": (result.title or {}).get("is_valid") if result.title else None,
                    }
                )
                writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean a CSV file using HumanMint.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    clean_parser = subparsers.add_parser("clean", help="Clean a CSV file")
    clean_parser.add_argument("input_file", type=Path, help="Path to input CSV")
    clean_parser.add_argument("output_file", type=Path, help="Path to output CSV")
    clean_parser.add_argument("--name-col", help="Name column")
    clean_parser.add_argument("--email-col", help="Email column")
    clean_parser.add_argument("--phone-col", help="Phone column")
    clean_parser.add_argument("--dept-col", help="Department column")
    clean_parser.add_argument("--title-col", help="Title column")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "clean":
        clean_csv(
            args.input_file,
            args.output_file,
            name_col=args.name_col,
            email_col=args.email_col,
            phone_col=args.phone_col,
            dept_col=args.dept_col,
            title_col=args.title_col,
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
