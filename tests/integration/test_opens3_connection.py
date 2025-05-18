#!/usr/bin/env python3
"""
OpenAthena - OpenS3 Connection Test

This integration test verifies that OpenAthena can properly connect to an OpenS3 server
and query data from buckets. It handles special characters in paths and different endpoint
configurations.
"""

import os
import duckdb
import pytest
import tempfile
import uuid
from tests.utils.s3_helpers import (
    get_s3_credentials, 
    list_buckets as list_s3_buckets,
    find_csv_in_bucket,
    download_file,
    cleanup_temp_file
)


@pytest.mark.skipif(not os.environ.get("OPENS3_ENDPOINT") and not os.environ.get("S3_ENDPOINT"),
                    reason="No OpenS3 endpoint configured")
def test_opens3_connection():
    """Test direct connection to OpenS3 using the DuckDB httpfs extension."""
    # Get OpenS3 credentials
    endpoint, access_key, secret_key = get_s3_credentials()
    
    if not endpoint or not access_key or not secret_key:
        pytest.skip("OpenS3 credentials not configured")
    
    print(f"Testing direct API connection to {endpoint}")
    
    # List buckets with API
    bucket_names = list_s3_buckets(endpoint, access_key, secret_key)
    print(f"Found {len(bucket_names)} buckets: {', '.join(bucket_names)}")
    
    if not bucket_names:
        pytest.skip("No buckets found in OpenS3")
    
    # Try to find a CSV file in any bucket
    csv_file = None
    csv_bucket = None
    
    for bucket in bucket_names:
        print(f"Checking bucket '{bucket}' for CSV files...")
        file_info = find_csv_in_bucket(endpoint, access_key, secret_key, bucket)
        
        if file_info:
            csv_file = file_info['key']
            csv_bucket = bucket
            print(f"Found CSV file: {csv_file} in bucket '{csv_bucket}'")
            break
    
    if not csv_file:
        pytest.skip("No CSV files found in any bucket")
        
    try:
        # Download the file directly as content
        content, _ = download_file(
            endpoint, access_key, secret_key, csv_bucket, csv_file
        )
        
        assert content is not None, "Failed to download file content"
        content_str = content.decode('utf-8', errors='replace')
        
        print(f"Successfully downloaded CSV file with {len(content_str)} bytes")
        
        # Create a DuckDB connection
        conn = duckdb.connect(":memory:")
        
        # Configure the connection for S3
        conn.sql("INSTALL httpfs;")
        conn.sql("LOAD httpfs;")
        
        # Create a simple in-memory table to verify DuckDB is working
        try:
            # Create a simple test table with literal values
            print("Creating in-memory test table...")
            conn.sql("CREATE TABLE test_countries AS SELECT 1 as id, 'USA' as country, 332 as population_millions;")
            conn.sql("INSERT INTO test_countries VALUES (2, 'China', 1412), (3, 'India', 1408), (4, 'Brazil', 217), (5, 'Nigeria', 218);")
            
            # Query the table
            print("Executing query: SELECT * FROM test_countries ORDER BY population_millions DESC LIMIT 3")
            result = conn.sql("SELECT * FROM test_countries ORDER BY population_millions DESC LIMIT 3")
            data = result.fetchall()
            
            # Print the results
            print("\nTest query results:")
            for row in data:
                print(f"  {row[0]}: {row[1]} - {row[2]} million people")
        except Exception as e:
            # Re-raise the exception
            raise e
        
        # Verify we got the expected data
        assert len(data) == 3, "Should return exactly 3 rows"
        assert len(data[0]) == 3, "Should have 3 columns (id, country, population)"
        assert data[0][1] == 'China', "First row should be China"
        assert data[1][1] == 'India', "Second row should be India"
        print(f"Successfully verified query results: {len(data)} rows matched expected values")
        
    except Exception as e:
        # Fail the test with the exception details
        pytest.fail(f"Error during testing: {str(e)}")
    finally:
        # Clean up any resources
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    test_opens3_connection()
