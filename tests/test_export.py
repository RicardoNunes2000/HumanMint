"""
Comprehensive tests for export functionality.

Tests all export formats (JSON, CSV, Parquet, SQL) with various scenarios:
- Basic export with flattened and nested data
- Empty results handling
- Field flattening correctness
- Multi-record exports
"""

import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

from humanmint import (bulk, export_csv, export_json, export_parquet,
                       export_sql, mint)


def test_export_json_single_record():
    """Test exporting a single normalized record to JSON."""
    result = mint(
        name="John Smith",
        email="john@example.com",
        phone="(202) 555-0123",
        department="Public Works",
        title="Engineer"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.json"
        export_json([result], str(filepath))

        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["email"]["normalized"] == "john@example.com"
        assert data[0]["name"]["full"] == "John Smith"
        assert data[0]["department"]["normalized"] == "Public Works"
        print("[OK] JSON export: single record")


def test_export_json_multiple_records():
    """Test exporting multiple records to JSON."""
    records = [
        {"name": "Alice Johnson", "email": "alice@city.gov"},
        {"name": "Bob Williams", "email": "bob@city.gov"},
        {"name": "Carol Davis", "email": "carol@city.gov"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_multi.json"
        export_json(results, str(filepath))

        with open(filepath) as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["name"]["first"] == "Alice"
        assert data[1]["name"]["first"] == "Bob"
        assert data[2]["name"]["first"] == "Carol"
        print("[OK] JSON export: multiple records")


def test_export_json_empty_results():
    """Test exporting empty results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "empty.json"
        export_json([], str(filepath))

        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)

        assert data == []
        print("[OK] JSON export: empty results")


def test_export_csv_flattened():
    """Test exporting to CSV with flattened structure."""
    records = [
        {"name": "John Smith", "email": "john@example.com", "phone": "(202) 555-0123"},
        {"name": "Jane Doe", "email": "jane@example.com", "phone": "(202) 555-0124"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.csv"
        export_csv(results, str(filepath), flatten=True)

        assert filepath.exists()

        # Verify CSV structure
        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        # Check flattened column names exist
        headers = set(rows[0].keys())
        assert "name_first" in headers
        assert "name_last" in headers
        assert "email_normalized" in headers
        assert "phone_e164" in headers

        # Verify data
        assert rows[0]["name_first"] == "John"
        assert rows[0]["email_normalized"] == "john@example.com"
        assert rows[1]["name_first"] == "Jane"
        print("[OK] CSV export: flattened structure")


def test_export_csv_nested():
    """Test exporting to CSV with nested structure (JSON strings)."""
    records = [
        {"name": "John Smith", "email": "john@example.com"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_nested.csv"
        export_csv(results, str(filepath), flatten=False)

        assert filepath.exists()

        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        # Check that name is a dict (stored as JSON string in CSV)
        assert "name" in rows[0]
        print("[OK] CSV export: nested structure")


def test_export_csv_empty_results():
    """Test exporting empty results to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "empty.csv"
        export_csv([], str(filepath))

        # Should handle gracefully without error
        assert not filepath.exists() or filepath.stat().st_size == 0
        print("[OK] CSV export: empty results")


def test_export_parquet_flattened():
    """Test exporting to Parquet with flattened structure."""
    try:
        import pandas as pd
    except ImportError:
        print("[SKIP] Parquet export: skipped (pandas not installed)")
        return

    records = [
        {"name": "Alice Cooper", "email": "alice@example.com", "phone": "(415) 555-0101"},
        {"name": "Bob Builder", "email": "bob@example.com", "phone": "(415) 555-0102"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.parquet"
        try:
            export_parquet(results, str(filepath), flatten=True)
        except ImportError:
            print("[SKIP] Parquet export: skipped (pyarrow not available)")
            return

        assert filepath.exists()

        # Read back and verify
        df = pd.read_parquet(filepath)
        assert len(df) == 2
        assert "name_first" in df.columns
        assert "email_normalized" in df.columns
        assert df.iloc[0]["name_first"] == "Alice"
        print("[OK] Parquet export: flattened structure")


def test_export_parquet_nested():
    """Test exporting to Parquet with nested structure."""
    try:
        import pandas as pd
    except ImportError:
        print("[SKIP] Parquet export: skipped (pandas not installed)")
        return

    records = [
        {"name": "Carol Day", "email": "carol@example.com"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_nested.parquet"
        try:
            export_parquet(results, str(filepath), flatten=False)
        except ImportError:
            print("[SKIP] Parquet export: skipped (pyarrow not available)")
            return

        assert filepath.exists()

        df = pd.read_parquet(filepath)
        assert len(df) == 1
        print("[OK] Parquet export: nested structure")


def test_export_sql():
    """Test exporting to SQL database."""
    try:
        import pandas as pd
        from sqlalchemy import create_engine
    except ImportError:
        print("[SKIP] SQL export: skipped (sqlalchemy/pandas not installed)")
        return

    records = [
        {"name": "David Evans", "email": "david@example.com", "phone": "(202) 555-0125"},
        {"name": "Eve Foster", "email": "eve@example.com", "phone": "(202) 555-0126"},
    ]

    results = bulk(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        try:
            # Test with flattened structure
            export_sql(results, engine, "contacts", if_exists="replace", flatten=True)

            # Verify by reading back
            df = pd.read_sql("SELECT * FROM contacts", engine)
            assert len(df) == 2
            assert "name_first" in df.columns
            assert df.iloc[0]["name_first"] == "David"
            print("[OK] SQL export: flattened to SQLite")
        finally:
            engine.dispose()


def test_export_sql_append():
    """Test SQL export with append mode."""
    try:
        import pandas as pd
        from sqlalchemy import create_engine
    except ImportError:
        print("[SKIP] SQL export (append): skipped (sqlalchemy/pandas not installed)")
        return

    records_batch1 = [
        {"name": "Frank Garcia", "email": "frank@example.com"},
    ]

    records_batch2 = [
        {"name": "Grace Hill", "email": "grace@example.com"},
    ]

    results1 = bulk(records_batch1)
    results2 = bulk(records_batch2)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "append_test.db"
        engine = create_engine(f"sqlite:///{db_path}")

        try:
            # First export
            export_sql(results1, engine, "contacts", if_exists="replace", flatten=True)

            # Append second batch
            export_sql(results2, engine, "contacts", if_exists="append", flatten=True)

            # Verify total records
            df = pd.read_sql("SELECT * FROM contacts", engine)
            assert len(df) == 2
            assert df.iloc[0]["name_first"] == "Frank"
            assert df.iloc[1]["name_first"] == "Grace"
            print("[OK] SQL export: append mode")
        finally:
            engine.dispose()


def test_csv_field_flattening_correctness():
    """Test that CSV field flattening produces correct column names."""
    result = mint(
        name="Test Person",
        email="test@example.com",
        phone="(202) 555-0127",
        address="123 Main St, City, ST 12345",
        department="Planning",
        title="Coordinator",
        organization="City Hall"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "flatten_test.csv"
        export_csv([result], str(filepath), flatten=True)

        with open(filepath) as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Verify expected flattened columns
        expected_prefixes = ["name_", "email", "phone_", "address_", "title_", "department", "organization_"]

        for expected in expected_prefixes:
            columns_with_prefix = [col for col in row.keys() if col.startswith(expected.rstrip("_"))]
            assert len(columns_with_prefix) > 0, f"Missing columns for {expected}"

        print("[OK] CSV export: field flattening correctness")


def test_export_with_minimal_data():
    """Test export with only required fields."""
    result = mint(name="Minimal Person")

    with tempfile.TemporaryDirectory() as tmpdir:
        # JSON
        json_path = Path(tmpdir) / "minimal.json"
        export_json([result], str(json_path))
        assert json_path.exists()

        # CSV
        csv_path = Path(tmpdir) / "minimal.csv"
        export_csv([result], str(csv_path))
        assert csv_path.exists()

        print("[OK] Export: minimal data (name only)")


def test_export_with_all_fields():
    """Test export with all available fields populated."""
    result = mint(
        name="Complete Record",
        email="complete@example.gov",
        phone="(415) 555-0150 ext 200",
        address="999 Government Blvd, City, CA 94103",
        department="Department of Public Works",
        title="Chief Engineer",
        organization="City of San Francisco"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "complete.json"
        export_json([result], str(json_path))

        with open(json_path) as f:
            data = json.load(f)

        record = data[0]
        assert record["name"]["full"] is not None
        assert record["email"] is not None
        assert record["phone"] is not None
        assert record["address"] is not None
        assert record["department"] is not None
        assert record["title"] is not None
        assert record["organization"] is not None

        print("[OK] Export: all fields populated")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HUMANMINT EXPORT TEST SUITE")
    print("=" * 60 + "\n")

    test_export_json_single_record()
    test_export_json_multiple_records()
    test_export_json_empty_results()
    test_export_csv_flattened()
    test_export_csv_nested()
    test_export_csv_empty_results()
    test_export_parquet_flattened()
    test_export_parquet_nested()
    test_export_sql()
    test_export_sql_append()
    test_csv_field_flattening_correctness()
    test_export_with_minimal_data()
    test_export_with_all_fields()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED [OK]")
    print("=" * 60 + "\n")
