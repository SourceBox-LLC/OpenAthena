"""
Database module for OpenAthena.

This module provides functionality for interacting with DuckDB and configuring
the database connection to work with OpenS3.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import duckdb

from open_athena.catalog import load_catalog


class DuckDBManager:
    """Manages DuckDB connection and operations for OpenAthena."""

    def __init__(
        self,
        database_path: Optional[str] = None,
        catalog_path: str = "catalog.yml",
        threads: int = 4,
        memory_limit: str = "4GB",
        enable_caching: bool = True,
    ):
        """
        Initialize DuckDB connection and configure for OpenS3.

        Args:
            database_path: Path to persistent database file or None for in-memory
            catalog_path: Path to catalog YAML file
            threads: Number of threads to use for query execution
            memory_limit: Memory limit for DuckDB
            enable_caching: Whether to enable result caching
        """
        self.database_path = database_path
        self.catalog_path = catalog_path
        self.connection = self._initialize_connection(
            database_path, threads, memory_limit, enable_caching
        )

        # Install and load httpfs extension for S3 access
        self._initialize_httpfs()

        # Load catalog if it exists
        self._load_catalog()

    def _initialize_connection(
        self,
        database_path: Optional[str],
        threads: int,
        memory_limit: str,
        enable_caching: bool,
    ) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB connection with performance settings."""
        # Create connection (in-memory or file-based)
        conn = duckdb.connect(database_path) if database_path else duckdb.connect()

        # Configure performance settings
        conn.sql(f"PRAGMA threads={threads};")
        conn.sql(f"PRAGMA memory_limit='{memory_limit}';")

        if enable_caching:
            conn.sql("PRAGMA enable_object_cache=true;")

        return conn

    def _initialize_httpfs(self) -> None:
        """Install and load httpfs extension for S3 access."""
        try:
            # First check if httpfs is already installed
            try:
                self.connection.sql("LOAD httpfs;")
                print("✅ Loaded existing httpfs extension for S3 access")
            except Exception:
                # If loading fails, try installing it first
                self.connection.sql("INSTALL httpfs; LOAD httpfs;")
                print("✅ Installed and loaded httpfs extension for S3 access")

            # Verify httpfs is properly installed by testing a basic function
            try:
                self.connection.sql("SELECT httpfs_version() AS version")
                print("✅ Verified httpfs extension is working properly")
            except Exception as verify_error:
                print(f"⚠️ httpfs installed but verification failed: {verify_error}")
                print("   This might affect your ability to connect to OpenS3")
        except Exception as e:
            print(f"❌ Error loading httpfs extension: {e}")
            print("   Without httpfs, OpenAthena cannot connect to OpenS3.")
            print(
                "   Please ensure you have internet connectivity to download extensions."
            )
            print(
                "   Or verify that DuckDB has permission to access the extension directory."
            )
            # We don't re-raise as we want to continue initialization

    def _load_catalog(self) -> None:
        """Load the catalog if it exists."""
        if os.path.exists(self.catalog_path):
            load_catalog(self.connection, self.catalog_path)

    def reload_catalog(self) -> None:
        """Reload the catalog configuration."""
        self._load_catalog()

    def execute_query(self, query: str) -> duckdb.DuckDBPyRelation:
        """
        Execute a SQL query against DuckDB.

        Args:
            query: SQL query to execute

        Returns:
            DuckDB relation result
        """
        return self.connection.sql(query)

    def configure_s3_credentials(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        region: Optional[str] = None,
        use_ssl: bool = True,
    ) -> None:
        """
        Configure S3 credentials for DuckDB httpfs.

        Args:
            access_key: S3 access key
            secret_key: S3 secret key
            endpoint: S3 endpoint URL
            region: S3 region
            use_ssl: Whether to use SSL for S3 connections
        """
        # If parameters were not provided, try to get them from environment variables
        if access_key is None:
            access_key = (
                os.environ.get("OPENS3_ACCESS_KEY")
                or os.environ.get("AWS_ACCESS_KEY_ID")
                or os.environ.get("DUCKDB_S3_ACCESS_KEY_ID")
            )

        if secret_key is None:
            secret_key = (
                os.environ.get("OPENS3_SECRET_KEY")
                or os.environ.get("AWS_SECRET_ACCESS_KEY")
                or os.environ.get("DUCKDB_S3_SECRET_ACCESS_KEY")
            )

        if endpoint is None:
            endpoint = (
                os.environ.get("OPENS3_ENDPOINT")
                or os.environ.get("S3_ENDPOINT")
                or os.environ.get("DUCKDB_S3_ENDPOINT")
            )
            # Add protocol if missing
            if endpoint and not (
                endpoint.startswith("http://") or endpoint.startswith("https://")
            ):
                endpoint = f"http://{endpoint}"

        if region is None:
            region = (
                os.environ.get("AWS_REGION")
                or os.environ.get("AWS_DEFAULT_REGION")
                or "us-east-1"
            )

        if use_ssl is True and os.environ.get("DUCKDB_S3_USE_SSL") is not None:
            use_ssl = os.environ.get("DUCKDB_S3_USE_SSL").lower() in (
                "true",
                "1",
                "yes",
            )
        elif use_ssl is True and os.environ.get("S3_USE_SSL") is not None:
            use_ssl = os.environ.get("S3_USE_SSL").lower() in ("true", "1", "yes")

        print(f"S3 configuration from environment:")
        print(f"  access_key: {'***' if access_key else 'None'}")
        print(f"  secret_key: {'***' if secret_key else 'None'}")
        print(f"  endpoint: {endpoint or 'None'}")
        print(f"  region: {region or 'None'}")
        print(f"  use_ssl: {use_ssl}")

        # Handle OpenS3-specific configurations
        is_opens3 = endpoint and (
            "10.0.0.204" in endpoint
            or "localhost" in endpoint
            or "127.0.0.1" in endpoint
        )

        if access_key and secret_key:
            # Set global variables for httpfs
            try:
                # Fix for protocol dropping issue with DuckDB's httpfs
                if is_opens3 and endpoint:
                    # Remove protocol and trailing slash for better DuckDB compatibility
                    endpoint_no_protocol = (
                        endpoint.replace("http://", "")
                        .replace("https://", "")
                        .rstrip("/")
                    )
                    print(
                        f"Using OpenS3 endpoint (no protocol): {endpoint_no_protocol}"
                    )

                    # Try both URL styles for OpenS3 compatibility
                    # First try virtual host style (default)
                    self.connection.sql("SET s3_url_style='vhost';")
                    print(f"✅ Configured for OpenS3 virtual-host URL access")

                    # Use the endpoint without protocol to avoid DuckDB's double-slash issue
                    self.connection.sql(f"SET s3_access_key_id='{access_key}';")
                    self.connection.sql(f"SET s3_secret_access_key='{secret_key}';")
                    self.connection.sql(f"SET s3_endpoint='{endpoint_no_protocol}';")
                    # Set path style URL access which is required for OpenS3
                    self.connection.sql("SET s3_url_style='path';")
                    # Disable SSL for local testing if using http protocol
                    if endpoint.startswith("http://"):
                        self.connection.sql("SET s3_use_ssl=false;")
                    print(f"✅ Configured OpenS3 server at {endpoint_no_protocol}")
                else:
                    # Standard AWS S3 configuration
                    self.connection.sql(f"SET s3_access_key_id='{access_key}';")
                    self.connection.sql(f"SET s3_secret_access_key='{secret_key}';")

                    if endpoint:
                        self.connection.sql(f"SET s3_endpoint='{endpoint}';")

                self.connection.sql(f"SET s3_region='{region}';")
                self.connection.sql(f"SET s3_use_ssl={str(use_ssl).lower()};")

                # Do a quick test query to verify connection
                try:
                    # We'll query for the S3 configuration which should be accessible with these credentials
                    self.connection.sql("SELECT s3_config_values LIMIT 1;")
                    print(f"✅ Successfully configured S3 credentials for DuckDB")

                    # If it's OpenS3, try a more specific check
                    if is_opens3:
                        try:
                            # Try to access a known bucket in OpenS3 for verification
                            self.connection.sql(
                                "SET s3_allow_errors=true;"
                            )  # Allow errors to continue execution

                            # Test if we can find any available buckets
                            buckets = ["my-test-bucket", "test-bucket-2", "my-bucket"]
                            for bucket in buckets:
                                try:
                                    # Look for files in a common bucket
                                    print(f"Testing connection to bucket '{bucket}'...")
                                    self.connection.sql(
                                        f"SELECT * FROM read_csv_auto('s3://{bucket}/*') LIMIT 0;"
                                    )
                                    print(
                                        f"✅ Successfully verified connection to '{bucket}' bucket in OpenS3"
                                    )
                                    break
                                except Exception:
                                    continue

                        except Exception as opens3_error:
                            print(
                                f"ℹ️ OpenS3 verification attempted but couldn't locate buckets: {opens3_error}"
                            )
                            print("   Make sure you have files in your OpenS3 buckets.")
                except Exception as test_error:
                    print(
                        f"⚠️ S3 credentials set but verification query failed: {test_error}"
                    )
                    print("   This might affect your ability to query S3 data.")

            except Exception as e:
                print(f"❌ Error configuring S3 credentials: {e}")
                print(
                    "   Without S3 credentials, OpenAthena cannot connect to OpenS3 buckets."
                )
                print("   Please check your environment variables.")
        else:
            print("⚠️ S3 credentials not found in environment variables.")
            print(
                "   To connect to OpenS3, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            )
            print(
                "   or OPENS3_ACCESS_KEY and OPENS3_SECRET_KEY environment variables."
            )
            if not os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get(
                "OPENS3_ACCESS_KEY"
            ):
                print("❌ Warning: No S3 credentials found in environment variables.")
                print("   OpenAthena will not be able to connect to OpenS3.")
                print(
                    "   Please set credentials in your .env file or environment variables."
                )
                print(
                    "   Hint: Run 'python -m open_athena.main configure_opens3' to set up credentials."
                )

            # Check endpoint configuration
            if os.environ.get("S3_ENDPOINT") or os.environ.get("OPENS3_ENDPOINT"):
                detected_endpoint = os.environ.get("S3_ENDPOINT") or os.environ.get(
                    "OPENS3_ENDPOINT"
                )
                print(f"   Using S3 endpoint from environment: {detected_endpoint}")
            else:
                print(
                    "⚠️ No S3 endpoint found in environment variables. Using default AWS S3 endpoint."
                )
                print(
                    "   If you're connecting to OpenS3, this will fail. Set S3_ENDPOINT or OPENS3_ENDPOINT."
                )
                print(
                    "   Hint: For your Raspberry Pi OpenS3 server, use: http://10.0.0.204:80"
                )

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
