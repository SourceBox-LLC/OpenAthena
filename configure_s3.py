#!/usr/bin/env python3
"""
OpenS3 Connection Configuration Helper for OpenAthena

This script configures the DuckDB S3 connection to use proper settings for OpenS3.
It should be run directly from the OpenAthena server directory.
"""

import os
import sys

import duckdb

# Import our custom S3 authentication middleware
try:
    from open_athena.s3_auth_middleware import (configure_httpfs_headers_auth,
                                                get_opens3_credentials)

    print("✅ Using OpenAthena S3 authentication middleware")
except ImportError:
    # If not running from within OpenAthena package, try relative import
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from open_athena.s3_auth_middleware import (
            configure_httpfs_headers_auth, get_opens3_credentials)

        print("✅ Using OpenAthena S3 authentication middleware from relative path")
    except ImportError:
        print("❌ Could not import s3_auth_middleware. Authentication may fail.")

        # Define stub functions in case we can't import
        def configure_httpfs_headers_auth(conn, username, password, endpoint):
            pass

        def get_opens3_credentials():
            return None, None, None


def configure_s3_for_opens3():
    """Configure DuckDB S3 settings for OpenS3"""
    print("Configuring DuckDB S3 settings for OpenS3...")

    # Create a temporary connection to configure
    conn = duckdb.connect(":memory:")

    # Configure S3 credentials
    endpoint = os.environ.get("S3_ENDPOINT") or os.environ.get(
        "OPENS3_ENDPOINT", "localhost:8001"
    )
    username = os.environ.get("OPENS3_USER") or os.environ.get("S3_USER") or "admin"
    password = os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get(
        "OPENS3_SECRET_KEY", "password"
    )
    access_key = os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get(
        "OPENS3_ACCESS_KEY", "admin"
    )

    print(f"Using S3 access key: {access_key}")
    print(f"Using S3 endpoint: {endpoint}")
    print(f"Using HTTP authentication: {username}:***********")

    # Set up the S3 connection for OpenS3
    conn.sql(f"SET s3_access_key_id='{access_key}';")
    conn.sql(f"SET s3_secret_access_key='{password}';")

    # Important: Remove any existing protocol prefix
    # We only want the host:port part for the S3 configuration
    if endpoint.startswith("http://"):
        endpoint = endpoint[7:]
    elif endpoint.startswith("https://"):
        endpoint = endpoint[8:]

    # Clean any trailing slashes
    endpoint = endpoint.strip("/")
    print(f"Using clean S3 endpoint: '{endpoint}'")

    # Configure S3 endpoint without prefix - DuckDB will add it automatically
    conn.sql(f"SET s3_endpoint='{endpoint}';")

    # Path style URL access is required for most S3 compatible services
    conn.sql("SET s3_url_style='path';")

    # Disable SSL for local testing
    conn.sql("SET s3_use_ssl=false;")

    # Set region (not critical for OpenS3)
    conn.sql("SET s3_region='us-east-1';")

    # Verify our settings
    print("S3 configuration complete with endpoint: " + endpoint)

    # These are the only parameters that modern DuckDB supports for S3
    # No s3_allow_errors parameter in this version

    # Configure HTTP header-based authentication for OpenS3
    try:
        print("Configuring HTTP header-based authentication for OpenS3...")
        conn.sql("INSTALL httpfs;")
        conn.sql("LOAD httpfs;")
        print("✅ Successfully installed and loaded httpfs extension")

        # Configure HTTP Basic Auth headers for OpenS3
        configure_httpfs_headers_auth(conn, username, password, endpoint)
        print("✅ Configured HTTP authentication headers for OpenS3")

        # Print current S3 configuration
        print("Current S3 Configuration:")
        try:
            config_result = conn.sql("PRAGMA show_s3_columns").fetchall()
            for row in config_result:
                print(f"  {row[0]}: {row[1]}")
        except Exception as config_err:
            print(f"  Unable to show S3 config: {config_err}")

        # Try accessing a known bucket
        bucket = "test-analytics"
        print(f"Testing connection to '{bucket}' bucket...")
        try:
            # Test with direct HTTP URL first (avoids S3 protocol complexity)
            test_query = f"SELECT COUNT(*) FROM read_csv_auto('http://{endpoint}/{bucket}/sample_data.csv');"
            print(f"Executing test query: {test_query}")
            conn.sql(test_query)
            print(f"✅ Successfully connected to '{bucket}' bucket via HTTP")
        except Exception as http_error:
            print(f"❌ Could not access bucket via HTTP: {http_error}")

            # Try with S3 protocol as fallback
            try:
                s3_query = f"SELECT COUNT(*) FROM read_csv_auto('s3://{bucket}/sample_data.csv');"
                print(f"Trying S3 protocol: {s3_query}")
                conn.sql(s3_query)
                print(f"✅ Successfully connected to '{bucket}' bucket via S3 protocol")
            except Exception as s3_error:
                print(f"❌ Could not access bucket via S3: {s3_error}")
                print("   Please ensure the bucket exists and has the expected files.")

    except Exception as e:
        print(f"❌ Error testing S3 connection: {e}")

    conn.close()

    # Export environment variables for OpenAthena child process
    os.environ["AWS_ACCESS_KEY_ID"] = access_key
    os.environ["AWS_SECRET_ACCESS_KEY"] = password  # Use password as secret key
    os.environ["S3_ENDPOINT"] = endpoint
    os.environ["S3_REGION"] = "us-east-1"  # Default region
    os.environ["S3_USE_SSL"] = "false"

    print("S3 configuration complete!")


if __name__ == "__main__":
    configure_s3_for_opens3()
