"""
Example script showing how to use the OpenAthena client API.

This script demonstrates how to connect to OpenAthena API and run queries.
"""

import pandas as pd
from open_athena.client import OpenAthenaClient


def main():
    """Run sample queries using the OpenAthena client API."""
    # Create an OpenAthena client
    print("Connecting to OpenAthena API...")
    client = OpenAthenaClient("http://localhost:8000")

    # Check API health
    try:
        health = client.health_check()
        print(f"API Health: {health}")
    except Exception as e:
        print(f"API health check failed: {e}")
        print("Make sure the OpenAthena API server is running.")
        return

    # List available tables
    print("\nListing available tables...")
    try:
        tables = client.list_tables()
        print(f"Available tables: {tables}")
    except Exception as e:
        print(f"Error listing tables: {e}")

    # Run a query and get results as a pandas DataFrame
    print("\nRunning query...")
    try:
        query = """
            SELECT * 
            FROM sales_2025
            LIMIT 10
        """
        df = client.execute_query(query)
        print("\nQuery results (DataFrame):")
        print(df)

        # Example: Calculate some statistics
        if not df.empty and "total" in df.columns:
            print("\nStatistics for 'total' column:")
            print(f"Mean: {df['total'].mean()}")
            print(f"Min: {df['total'].min()}")
            print(f"Max: {df['total'].max()}")
    except Exception as e:
        print(f"Error running query: {e}")

    # Run a different query with CSV output
    print("\nRunning query with CSV output...")
    try:
        query = """
            SELECT 
                date_trunc('month', order_date) as month,
                COUNT(*) as order_count,
                SUM(total) as total_revenue
            FROM sales_2025
            GROUP BY month
            ORDER BY month
        """
        csv_data = client.execute_query(query, format="csv")
        print("\nQuery results (CSV):")
        print(csv_data)
    except Exception as e:
        print(f"Error running query with CSV output: {e}")

    # Add a new table to the catalog
    print("\nAdding a new table to the catalog...")
    try:
        result = client.add_table(
            table_name="customer_orders",
            bucket="data",
            prefix="orders/",
            file_format="parquet",
        )
        print(f"Add table result: {result}")
    except Exception as e:
        print(f"Error adding table: {e}")

    # Reload the catalog
    print("\nReloading the catalog...")
    try:
        result = client.reload_catalog()
        print(f"Reload catalog result: {result}")
    except Exception as e:
        print(f"Error reloading catalog: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
