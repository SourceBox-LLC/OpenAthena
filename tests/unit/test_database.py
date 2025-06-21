"""
Unit tests for OpenAthena database functionality.
"""

import os
import pytest
import duckdb

from open_athena.database import DuckDBManager


def test_duckdb_manager_init():
    """Test creating a DuckDBManager instance."""
    # Create an in-memory database manager
    manager = DuckDBManager(database_path=None)

    # Verify it has a valid connection
    assert manager.connection is not None
    assert isinstance(manager.connection, duckdb.DuckDBPyConnection)

    # Test executing a simple query
    result = manager.connection.sql("SELECT 1 AS test").fetchall()
    assert result[0][0] == 1

    # Clean up
    manager.close()


def test_execute_query():
    """Test executing a query and retrieving results."""
    # Create an in-memory database manager
    manager = DuckDBManager(database_path=None)

    # Create a test table
    manager.connection.sql("CREATE TABLE test_table (id INTEGER, name VARCHAR)")
    manager.connection.sql(
        "INSERT INTO test_table VALUES (1, 'test1'), (2, 'test2'), (3, 'test3')"
    )

    # Execute a query
    result = manager.execute_query("SELECT * FROM test_table ORDER BY id")

    # Convert the relation to a result set we can index
    rows = result.fetchall()

    # Verify the results
    assert len(rows) == 3
    assert rows[0][0] == 1
    assert rows[0][1] == "test1"
    assert rows[2][0] == 3
    assert rows[2][1] == "test3"

    # Clean up
    manager.close()


def test_execute_query_with_error():
    """Test handling of SQL errors."""
    # Create an in-memory database manager
    manager = DuckDBManager(database_path=None)

    # Execute a query with syntax error
    with pytest.raises(Exception):
        manager.execute_query("SELECT * FROM nonexistent_table")

    # Clean up
    manager.close()


def test_connection_parameters():
    """Test connection parameters affect DuckDB behavior."""
    # Test with specific memory limit
    manager = DuckDBManager(database_path=None, memory_limit="100MB")

    # Create a large table that should fit within limits
    manager.connection.sql("CREATE TABLE small_table AS SELECT * FROM range(1000)")
    result = manager.connection.sql("SELECT COUNT(*) FROM small_table").fetchall()
    assert result[0][0] == 1000

    # Clean up
    manager.close()


def test_close_connection():
    """Test closing a connection properly."""
    # Get a manager and its connection
    manager = DuckDBManager(database_path=None)
    con = manager.connection

    # Close it
    manager.close()

    # Attempting to use a closed connection should raise an exception
    with pytest.raises(Exception):
        con.sql("SELECT 1").fetchall()
