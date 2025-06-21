"""
Test script to verify the catalog fix for handling apostrophes in file paths
"""

import logging
import os

from open_athena.catalog import load_catalog
from open_athena.database import DuckDBManager
from open_athena.opens3_file_proxy import get_proxy_instance

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_catalog_query():
    """Test catalog loading and querying with the apostrophe fix"""
    logger.info("Starting catalog test with apostrophe fix")

    # Create DuckDB manager (which automatically loads the catalog)
    logger.info("Creating DuckDB manager...")
    db_manager = DuckDBManager()
    con = db_manager.connection

    logger.info("Catalog already loaded by DuckDBManager")

    # List tables in catalog
    logger.info("Listing tables in catalog...")
    tables = con.sql("SHOW TABLES;").fetchall()
    logger.info(f"Tables in catalog: {tables}")

    # Test querying each table
    for table in tables:
        table_name = table[0]
        logger.info(f"Testing query for table {table_name}")
        try:
            # Get column list
            columns = con.sql(f"DESCRIBE {table_name};").fetchall()
            logger.info(f"Columns in {table_name}: {[col[0] for col in columns]}")

            # Try a simple query
            result = con.sql(f"SELECT * FROM {table_name} LIMIT 5;").fetchall()
            row_count = len(result)
            logger.info(f"Query successful for {table_name}: {row_count} rows returned")

            if row_count > 0:
                # Show first row
                logger.info(f"Sample row from {table_name}: {result[0]}")
        except Exception as e:
            logger.error(f"Error querying {table_name}: {e}")


if __name__ == "__main__":
    test_catalog_query()
