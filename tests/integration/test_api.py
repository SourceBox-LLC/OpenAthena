"""
Integration tests for OpenAthena API endpoints.
"""
import os
import json
import pytest
import tempfile
from fastapi.testclient import TestClient

from open_athena.api import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    # Create a temporary catalog file in a temp directory
    temp_dir = tempfile.gettempdir()
    catalog_path = os.path.join(temp_dir, "openathena_test_catalog.yml")
    
    # Set environment variables for testing
    os.environ["OPENATHENA_USE_DUMMY_DATA"] = "true"
    os.environ["OPENATHENA_CATALOG_PATH"] = catalog_path
    
    # Create the test catalog file
    with open(catalog_path, "w") as f:
        f.write('''test_table:
  type: "dummy"
''')
    
    # Create test client
    with TestClient(app) as client:
        yield client
        
    # Cleanup
    if os.path.exists(catalog_path):
        try:
            os.remove(catalog_path)
        except (PermissionError, OSError):
            # Log but don't fail if we can't remove it
            print(f"Warning: Could not remove temporary catalog file {catalog_path}")
            pass


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_tables_endpoint(client):
    """Test the tables listing endpoint."""
    response = client.get("/tables")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "test_table" in data["tables"]
    assert data["tables"]["test_table"]["type"] == "dummy"


def test_sql_query_endpoint(client):
    """Test executing SQL queries."""
    query = "SELECT * FROM test_table"
    response = client.post("/sql", content=query)
    
    # Verify response
    assert response.status_code == 200
    # The response should be Arrow format by default
    assert response.headers["Content-Type"] == "application/vnd.apache.arrow.stream"
    
    # Test with an invalid query
    invalid_query = "SELECT * FROM non_existent_table"
    response = client.post("/sql", content=invalid_query)
    assert response.status_code == 500  # Expect an error
    

def test_catalog_reload_endpoint(client):
    """Test reloading the catalog."""
    response = client.post("/catalog/reload")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["success", "ok"]  # Accept either success or ok as valid status
    
    # The API might return either a tables key or a message key depending on the implementation
    # Check that we have either one of these patterns
    assert ("tables" in data) or ("message" in data and "Catalog reloaded successfully" in data["message"])
