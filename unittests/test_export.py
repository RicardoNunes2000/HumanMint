"""
Tests for batch export functionality.

Tests JSON, CSV, and Parquet export formats for normalized results.
"""

import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

import pytest

from humanmint import (bulk, export_csv, export_json, export_parquet,
                       export_sql, mint)


def _has_pandas() -> bool:
    """Check if pandas is available."""
    try:
        import pandas  # noqa: F401
        return True
    except ImportError:
        return False


def _has_sqlalchemy() -> bool:
    """Check if sqlalchemy is available."""
    try:
        import sqlalchemy  # noqa: F401
        return True
    except ImportError:
        return False


def _has_pyarrow() -> bool:
    """Check if pyarrow is available."""
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        return False


class TestExportJSON:
    """Test JSON export functionality."""

    def test_export_json_single_result(self):
        """Test exporting a single result to JSON."""
        result = mint(name="John Smith", email="john@example.com")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"
            export_json([result], str(filepath))

            assert filepath.exists()
            with open(filepath, "r") as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["name"]["full"] == "John Smith"
            assert data[0]["email"]["normalized"] == "john@example.com"

    def test_export_json_multiple_results(self):
        """Test exporting multiple results to JSON."""
        results = [
            mint(name="Jane Doe", email="jane@example.com"),
            mint(name="Bob Jones", email="bob@example.com"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"
            export_json(results, str(filepath))

            with open(filepath, "r") as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["name"]["full"] == "Jane Doe"
            assert data[1]["name"]["full"] == "Bob Jones"

    def test_export_json_preserves_unicode(self):
        """Test that JSON export preserves unicode characters."""
        result = mint(name="José García", email="jose@example.com")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"
            export_json([result], str(filepath))

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                assert "José" in content
                assert "García" in content


class TestExportCSV:
    """Test CSV export functionality."""

    def test_export_csv_flattened(self):
        """Test exporting to CSV with flattened structure."""
        results = bulk([
            {"name": "Jane Doe", "email": "jane@example.com", "phone": "(202) 555-0123"},
            {"name": "Bob Jones", "email": "bob@example.com", "phone": "(202) 555-0124"},
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.csv"
            export_csv(results, str(filepath), flatten=True)

            assert filepath.exists()
            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "name_first" in rows[0]
            assert "email_normalized" in rows[0]
            assert rows[0]["name_first"] == "Jane"
            assert rows[1]["name_first"] == "Bob"

    def test_export_csv_nested(self):
        """Test exporting to CSV with nested JSON structure."""
        results = bulk([
            {"name": "Jane Doe", "email": "jane@example.com"},
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.csv"
            export_csv(results, str(filepath), flatten=False)

            assert filepath.exists()
            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            # When not flattened, we expect raw dicts to be written
            assert "name" in rows[0]

    def test_export_csv_empty_results(self):
        """Test exporting empty results list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.csv"
            export_csv([], str(filepath))
            # Should not crash, file may or may not exist


class TestExportParquet:
    """Test Parquet export functionality."""

    @pytest.mark.skipif(
        not (_has_pandas() and _has_pyarrow()),
        reason="pandas and pyarrow required for parquet export"
    )
    def test_export_parquet_flattened(self):
        """Test exporting to Parquet with flattened structure."""
        results = bulk([
            {"name": "Jane Doe", "email": "jane@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.parquet"
            export_parquet(results, str(filepath), flatten=True)

            assert Path(filepath).exists()
            import pandas as pd
            df = pd.read_parquet(filepath)
            assert len(df) == 2
            assert "name_first" in df.columns
            assert df["name_first"].iloc[0] == "Jane"

    @pytest.mark.skipif(
        not (_has_pandas() and _has_pyarrow()),
        reason="pandas and pyarrow required for parquet export"
    )
    def test_export_parquet_empty_results(self):
        """Test exporting empty results to Parquet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.parquet"
            export_parquet([], str(filepath))
            # Should not crash


class TestExportSQL:
    """Test SQL export functionality."""

    @pytest.mark.skipif(
        not _has_sqlalchemy(),
        reason="sqlalchemy required for SQL export"
    )
    def test_export_sql_sqlite(self):
        """Test exporting to SQLite database."""
        from sqlalchemy import create_engine

        results = bulk([
            {"name": "Jane Doe", "email": "jane@example.com"},
            {"name": "Bob Jones", "email": "bob@example.com"},
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = create_engine(f"sqlite:///{db_path}")

            try:
                export_sql(results, engine, "cleaned_contacts", flatten=True)

                # Verify data was written
                import pandas as pd
                df = pd.read_sql("SELECT * FROM cleaned_contacts", engine)
                assert len(df) == 2
                assert "name_first" in df.columns
            finally:
                # Dispose engine to release SQLite locks on Windows
                engine.dispose()

    @pytest.mark.skipif(
        not _has_sqlalchemy(),
        reason="sqlalchemy required for SQL export"
    )
    def test_export_sql_replace_mode(self):
        """Test that replace mode overwrites existing table."""
        from sqlalchemy import create_engine

        results1 = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        results2 = bulk([
            {"name": "Bob Jones", "email": "bob@example.com"},
            {"name": "Alice Brown", "email": "alice@example.com"},
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = create_engine(f"sqlite:///{db_path}")

            try:
                # First export
                export_sql(results1, engine, "contacts", if_exists="replace", flatten=True)

                # Second export with replace
                export_sql(results2, engine, "contacts", if_exists="replace", flatten=True)

                # Verify second data replaced first
                import pandas as pd
                df = pd.read_sql("SELECT * FROM contacts", engine)
                assert len(df) == 2
            finally:
                # Dispose engine to release SQLite locks on Windows
                engine.dispose()

    @pytest.mark.skipif(
        not _has_sqlalchemy(),
        reason="sqlalchemy required for SQL export"
    )
    def test_export_sql_append_mode(self):
        """Test that append mode adds to existing table."""
        from sqlalchemy import create_engine

        results1 = bulk([{"name": "Jane Doe", "email": "jane@example.com"}])
        results2 = bulk([{"name": "Bob Jones", "email": "bob@example.com"}])

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = create_engine(f"sqlite:///{db_path}")

            try:
                # First export
                export_sql(results1, engine, "contacts", if_exists="replace", flatten=True)

                # Second export with append
                export_sql(results2, engine, "contacts", if_exists="append", flatten=True)

                # Verify data was appended
                import pandas as pd
                df = pd.read_sql("SELECT * FROM contacts", engine)
                assert len(df) == 2
            finally:
                # Dispose engine to release SQLite locks on Windows
                engine.dispose()
