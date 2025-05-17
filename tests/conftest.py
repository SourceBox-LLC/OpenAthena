"""
OpenAthena test configuration.

This file contains fixtures and configuration for tests.
"""
import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from open_athena.database import DuckDBManager

@pytest.fixture
def temp_catalog():
    """Create a temporary catalog file with test tables."""
    with tempfile.NamedTemporaryFile(suffix='.yml', delete=False, mode='w') as f:
        catalog_content = {
            'test_table': {
                'type': 'dummy'
            },
            'test_table_2': {
                'type': 'dummy'
            }
        }
        yaml.dump(catalog_content, f)
        catalog_path = f.name

    yield catalog_path
    
    # Cleanup
    if os.path.exists(catalog_path):
        os.unlink(catalog_path)

@pytest.fixture
def db_connection():
    """Get a fresh DuckDBManager instance for testing."""
    manager = DuckDBManager(database_path=None)  # in-memory database
    yield manager.connection
    manager.close()

@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    from open_athena.api import app
    
    # Set environment variables for testing
    os.environ["OPENATHENA_USE_DUMMY_DATA"] = "true"
    
    client = TestClient(app)
    yield client
