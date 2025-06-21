"""
Example script showing how to use OpenAthena programmatically.

This script demonstrates how to connect to DuckDB directly and run queries
against OpenS3 data.
"""

import os

import duckdb

from open_athena.catalog import load_catalog


def main():
    """Run sample queries against OpenS3 data."""
    # Connect to DuckDB
    print("Connecting to DuckDB...")
    con = duckdb.connect()

    # Install and load httpfs extension for S3 access
    print("Loading httpfs extension...")
    con.sql("INSTALL httpfs; LOAD httpfs;")

    # Configure S3 credentials (from environment variables or manually)
    # You can set these in your environment or provide them directly
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    endpoint = os.environ.get("S3_ENDPOINT")  # For OpenS3

    if access_key and secret_key:
        print("Configuring S3 credentials...")
        con.sql(f"SET s3_access_key_id='{access_key}';")
        con.sql(f"SET s3_secret_access_key='{secret_key}';")

        if endpoint:
            con.sql(f"SET s3_endpoint='{endpoint}';")

    # Load catalog from YAML
    print("Loading catalog...")
    load_catalog(con, "../catalog.yml")

    # Run a query using catalog view
    print("\nRunning query on sales_2025 table...")
    try:
        result = con.sql(
            """
            SELECT * 
            FROM sales_2025
            LIMIT 10
        """
        )
        result.show()
    except Exception as e:
        print(f"Error running query: {e}")

    # Direct query without catalog (with S3 path)
    print("\nRunning direct query on S3 path...")
    try:
        result = con.sql(
            """
            SELECT * 
            FROM 's3://analytics/2025/05/**.parquet'
            LIMIT 10
        """
        )
        result.show()
    except Exception as e:
        print(f"Error running direct query: {e}")

    # Using SQL aggregation
    print("\nRunning aggregation query...")
    try:
        result = con.sql(
            """
            SELECT 
                date_trunc('month', order_date) as month,
                COUNT(*) as order_count,
                SUM(total) as total_revenue
            FROM sales_2025
            GROUP BY month
            ORDER BY month
        """
        )
        result.show()
    except Exception as e:
        print(f"Error running aggregation query: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
