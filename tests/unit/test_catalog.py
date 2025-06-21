"""
Unit tests for OpenAthena catalog functionality.
"""

import os
from pathlib import Path

import pytest
import yaml

from open_athena.catalog import get_catalog_tables, load_catalog


def test_load_catalog_with_dummy_tables(db_connection, temp_catalog):
    """Test loading a catalog with dummy tables."""
    # Load the catalog
    load_catalog(db_connection, temp_catalog)

    # Execute a query against each dummy table to verify they were created
    result1 = db_connection.sql("SELECT COUNT(*) FROM test_table").fetchall()
    assert result1[0][0] == 3  # Our dummy tables have 3 rows

    result2 = db_connection.sql("SELECT COUNT(*) FROM test_table_2").fetchall()
    assert result2[0][0] == 3


def test_get_catalog_tables(temp_catalog):
    """Test getting the list of tables from a catalog file."""
    # Get the tables
    tables = get_catalog_tables(temp_catalog)

    # Verify the tables match what we expect
    assert "test_table" in tables
    assert "test_table_2" in tables
    assert tables["test_table"]["type"] == "dummy"


def test_catalog_with_nonexistent_path():
    """Test catalog handling when the file doesn't exist."""
    non_existent_path = "/path/that/doesnt/exist/catalog.yml"
    tables = get_catalog_tables(non_existent_path)
    assert tables == {}


def test_load_catalog_with_empty_file(db_connection, tmp_path):
    """Test loading a catalog from an empty file."""
    # Create an empty catalog file
    empty_catalog = tmp_path / "empty_catalog.yml"
    empty_catalog.write_text("")

    # Load the catalog - should not raise an exception
    load_catalog(db_connection, str(empty_catalog))

    # No tables should be created
    with pytest.raises(Exception):
        db_connection.sql("SELECT * FROM non_existent_table").fetchall()
