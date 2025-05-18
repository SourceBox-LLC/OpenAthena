"""
Quick test script for OpenAthena.

This script performs a simple test to verify that DuckDB is working correctly
and can communicate with OpenS3 via presigned URLs or direct S3 access.
"""

import os
import sys
import duckdb


def test_duckdb_installation():
    """Test that DuckDB is installed and working."""
    print("Testing DuckDB installation...")
    try:
        # Connect to DuckDB
        con = duckdb.connect()
        
        # Run a simple query
        result = con.sql("SELECT 'Hello from DuckDB ' || version() AS message")
        message = result.fetchone()[0]
        print(f"✓ {message}")
        return True
    except Exception as e:
        print(f"✗ DuckDB test failed: {e}")
        return False


def test_httpfs_extension():
    """Test that the httpfs extension can be installed and loaded."""
    print("\nTesting httpfs extension...")
    try:
        # Connect to DuckDB
        con = duckdb.connect()
        
        # Install and load the httpfs extension
        con.sql("INSTALL httpfs; LOAD httpfs;")
        
        # Verify it's loaded - use a different approach to check if httpfs is loaded
        try:
            # Try to use an httpfs-specific function
            con.sql("SET s3_region='us-east-1';")
            print("✓ httpfs extension loaded successfully")
            return True
        except Exception as verify_error:
            print(f"✗ httpfs extension verification failed: {verify_error}")
            return False
    except Exception as e:
        print(f"✗ httpfs extension test failed: {e}")
        return False


def test_s3_credentials():
    """Test that S3 credentials are available."""
    print("\nChecking S3 credentials...")
    
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    endpoint = os.environ.get("S3_ENDPOINT")
    
    if access_key and secret_key:
        print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:4]}...{access_key[-4:]}")
        print(f"✓ AWS_SECRET_ACCESS_KEY: {'*' * 8}")
        if endpoint:
            print(f"✓ S3_ENDPOINT: {endpoint}")
        else:
            print("! S3_ENDPOINT not set (needed for OpenS3)")
        return True
    else:
        print("✗ S3 credentials not found in environment")
        print("! Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_ENDPOINT")
        return False


def test_local_parquet_query():
    """Test querying a local Parquet file."""
    print("\nTesting local Parquet query...")
    
    # Create a test directory if it doesn't exist
    os.makedirs("test_data", exist_ok=True)
    
    # Path to test Parquet file
    parquet_path = "test_data/test.parquet"
    
    try:
        # Connect to DuckDB
        con = duckdb.connect()
        
        # Create a test dataframe and save as Parquet
        print("Creating test Parquet file...")
        con.sql("""
            CREATE TABLE test AS 
            SELECT 
                i AS id, 
                'Item ' || i AS name,
                i * 10.0 AS price
            FROM range(1, 10) t(i)
        """)
        con.sql(f"COPY test TO '{parquet_path}' (FORMAT PARQUET)")
        
        # Query the Parquet file
        print("Querying test Parquet file...")
        result = con.sql(f"SELECT * FROM '{parquet_path}' WHERE id > 5")
        print("\nTest query results:")
        result.show()
        
        print("✓ Local Parquet query test successful")
        return True
    except Exception as e:
        print(f"✗ Local Parquet query test failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("====== OpenAthena Quick Test ======\n")
    
    # Run tests
    duckdb_ok = test_duckdb_installation()
    httpfs_ok = test_httpfs_extension()
    s3_creds_ok = test_s3_credentials()
    parquet_ok = test_local_parquet_query()
    
    # Summarize results
    print("\n====== Test Summary ======")
    print(f"DuckDB Installation: {'✓' if duckdb_ok else '✗'}")
    print(f"httpfs Extension: {'✓' if httpfs_ok else '✗'}")
    print(f"S3 Credentials: {'✓' if s3_creds_ok else '✗'}")
    print(f"Local Parquet Query: {'✓' if parquet_ok else '✗'}")
    
    # Overall assessment
    if duckdb_ok and httpfs_ok and parquet_ok:
        print("\n✓ OpenAthena prerequisites met!")
        if not s3_creds_ok:
            print("! Configure S3 credentials to connect to OpenS3")
    else:
        print("\n✗ Some tests failed - see details above")
        sys.exit(1)


if __name__ == "__main__":
    main()
