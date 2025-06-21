#!/usr/bin/env python3
"""
S3 Authentication Middleware for OpenAthena

This module provides middleware for DuckDB's httpfs extension to authenticate
with OpenS3 using HTTP headers instead of embedded credentials in URLs.
"""

import os
import base64
import duckdb
from typing import Optional


def configure_httpfs_headers_auth(
    connection: duckdb.DuckDBPyConnection, username: str, password: str, endpoint: str
) -> None:
    """
    Configure DuckDB's httpfs extension to authenticate with OpenS3.
    For DuckDB 1.2.2, we'll use the most compatible approach - setting S3 credentials
    and using the S3 protocol instead of HTTP headers which aren't supported.

    Args:
        connection: DuckDB connection to configure
        username: OpenS3 username
        password: OpenS3 password
        endpoint: OpenS3 endpoint URL (e.g., localhost:8001)
    """
    # Format endpoint without protocol
    if endpoint.startswith("http://"):
        endpoint_with_protocol = endpoint
        endpoint = endpoint[7:]
    elif endpoint.startswith("https://"):
        endpoint_with_protocol = endpoint
        endpoint = endpoint[8:]
    else:
        endpoint_with_protocol = f"http://{endpoint}"

    # Remove trailing slashes
    endpoint = endpoint.rstrip("/")

    try:
        # Make sure httpfs is loaded
        connection.sql("INSTALL httpfs; LOAD httpfs;")

        # Configure the S3 credentials (using the same credentials for HTTP Basic Auth)
        # This is our best alternative since we can't set HTTP headers directly
        connection.sql(f"SET s3_access_key_id='{username}';")
        connection.sql(f"SET s3_secret_access_key='{password}';")
        connection.sql(f"SET s3_endpoint='http://{endpoint}';")
        connection.sql("SET s3_url_style='path';")  # Required for OpenS3
        connection.sql("SET s3_use_ssl=false;")  # For local testing

        # Set only OpenS3-related environment variables in this process
        os.environ["OPENS3_ACCESS_KEY"] = username
        os.environ["OPENS3_SECRET_KEY"] = password
        os.environ["OPENS3_ENDPOINT"] = endpoint_with_protocol
        os.environ["S3_ENDPOINT"] = endpoint_with_protocol

        print(f"✅ Configured S3 credentials for OpenS3 at {endpoint}")
        print(
            f"✅ Environment variables set: OPENS3_ACCESS_KEY={username}, OPENS3_ENDPOINT={endpoint_with_protocol}"
        )

        # Verify httpfs extension is properly loaded
        try:
            connection.sql("SELECT httpfs_version() as version")
        except:
            print("⚠️ httpfs_version() not available in this DuckDB version")

    except Exception as e:
        print(f"❌ Error configuring S3 authentication: {e}")
        print("   Authentication with OpenS3 may fail.")


def get_opens3_credentials():
    """Get OpenS3 endpoint and credentials from environment variables.

    Returns:
        Tuple of (endpoint, username, password)
    """
    # Try to get endpoint from environment variables
    endpoint = os.environ.get("OPENS3_ENDPOINT") or os.environ.get("S3_ENDPOINT")

    # Print debug information about the environment
    print(f"Debug: OPENS3_ENDPOINT = {os.environ.get('OPENS3_ENDPOINT')}")
    print(f"Debug: S3_ENDPOINT = {os.environ.get('S3_ENDPOINT')}")
    print(
        f"Debug: OPENS3_ACCESS_KEY = {'Set' if os.environ.get('OPENS3_ACCESS_KEY') else 'Not set'}"
    )
    print(
        f"Debug: OPENS3_SECRET_KEY = {'Set' if os.environ.get('OPENS3_SECRET_KEY') else 'Not set'}"
    )

    # Ensure endpoint has a protocol
    if endpoint and not (
        endpoint.startswith("http://") or endpoint.startswith("https://")
    ):
        endpoint = f"http://{endpoint}"

    # Get credentials from environment variables - focus on OpenS3 variables
    # For username/access_key - prioritize OpenS3-specific variables
    username = (
        os.environ.get("OPENS3_USER")
        or os.environ.get("OPENS3_ACCESS_KEY")
        or os.environ.get("S3_USER")
        or os.environ.get("S3_ACCESS_KEY_ID")
    )

    # For password/secret_key
    password = (
        os.environ.get("OPENS3_PASSWORD")
        or os.environ.get("OPENS3_SECRET_KEY")
        or os.environ.get("S3_PASSWORD")
        or os.environ.get("S3_SECRET_ACCESS_KEY")
        or "password"
    )

    # Log credentials being used (without revealing full password)
    masked_password = (
        password[:2] + "*" * (len(password) - 4) + password[-2:]
        if len(password) > 4
        else "****"
    )
    print(f"Using credentials: username={username}, password={masked_password}")

    # Default values for local testing
    if not endpoint:
        endpoint = "http://localhost:8001"
    if not username:
        username = "admin"
    if not password:
        password = "password"

    # Format endpoint with protocol if missing
    if not (endpoint.startswith("http://") or endpoint.startswith("https://")):
        endpoint = f"http://{endpoint}"

    # Strip trailing slashes
    endpoint = endpoint.rstrip("/")

    # Always set environment variables here to ensure they're accessible
    # across the entire process - only use OpenS3-specific variables
    os.environ["OPENS3_ACCESS_KEY"] = username
    os.environ["OPENS3_SECRET_KEY"] = password
    os.environ["S3_ENDPOINT"] = endpoint
    os.environ["OPENS3_ENDPOINT"] = endpoint

    print(f"✅ Environment variables set/refreshed for OpenS3 access:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Username: {username}")

    return endpoint, username, password
