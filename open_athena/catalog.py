"""
Catalog module for OpenAthena.

This module provides functionality to manage data sources using a YAML-based catalog.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_catalog(con, cat_path: str = "catalog.yml") -> None:
    """
    Load catalog configuration from YAML and create DuckDB views.
    
    Args:
        con: DuckDB connection
        cat_path: Path to the catalog YAML file
    """
    if not os.path.exists(cat_path):
        print(f"Warning: Catalog file {cat_path} not found.")
        return
    
    cfg = yaml.safe_load(Path(cat_path).read_text())
    if not cfg:
        print(f"Warning: Catalog file {cat_path} is empty or invalid.")
        return
    
    for tbl, meta in cfg.items():
        # Check if this is a dummy table for testing
        if meta.get('type') == 'dummy':
            # Create a simple test table with sample data
            con.sql(f"""
                CREATE OR REPLACE VIEW {tbl} AS 
                SELECT 1 as id, 'test' as name, 100.0 as value
                UNION ALL
                SELECT 2 as id, 'test2' as name, 200.0 as value
                UNION ALL
                SELECT 3 as id, 'test3' as name, 300.0 as value;
            """)
            print(f"Created dummy view for table '{tbl}' for testing")
            continue
            
        # Regular S3 table setup
        bucket = meta.get('bucket', '')
        prefix = meta.get('prefix', '')
        file_format = meta.get('format', 'parquet')
        
        try:
            # Build S3 path pattern
            path = f"s3://{bucket}/{prefix}**/*.{file_format}"
            
            # Make sure table name is SQL safe
            safe_tbl = f'"{tbl}"' if "-" in tbl else tbl
            
            # First, test if we can access the S3 bucket
            test_query = f"SELECT COUNT(*) FROM '{path}' LIMIT 1"
            try:
                # Attempt to run a test query
                con.sql(test_query)
                # If successful, create the view
                con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT * FROM '{path}';")
                print(f"✅ Created view for table '{tbl}' pointing to {path}")
            except Exception as access_error:
                # Provide detailed diagnostic information
                print(f"⚠️ S3 access error for bucket '{bucket}': {access_error}")
                print("   Please verify:")
                print("   1. The bucket exists on your OpenS3 server")
                print("   2. The S3 credentials are correct")
                print("   3. The OpenS3 endpoint URL is accessible")
                # Create a dummy view with diagnostic information
                con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT 1 as id, 'Connection error: {bucket}' as error_message WHERE 1=0;")
                print(f"   Created empty fallback view for table '{tbl}'")
                # Raise the error again to be caught by the outer exception handler
                raise
        except Exception as e:
            print(f"❌ Error creating view for table '{tbl}': {e}")
            # Create a dummy view with no data as a fallback
            con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT 1 as id, 'Error: {str(e).replace("'", "''")}' as error_message WHERE 1=0;")
            print(f"   Created empty fallback view for table '{tbl}'")
            # Continue processing other tables
                


def get_catalog_tables(cat_path: str = "catalog.yml") -> Dict[str, Any]:
    """
    Get all tables defined in the catalog.
    
    Args:
        cat_path: Path to the catalog YAML file
        
    Returns:
        Dictionary of table definitions from the catalog
    """
    if not os.path.exists(cat_path):
        return {}
    
    return yaml.safe_load(Path(cat_path).read_text())


def create_catalog_table(
    cat_path: str, 
    table_name: str, 
    bucket: str, 
    prefix: str, 
    file_format: str = "parquet"
) -> bool:
    """
    Add a new table to the catalog.
    
    Args:
        cat_path: Path to the catalog YAML file
        table_name: Name of the table to create
        bucket: S3 bucket name
        prefix: Prefix path within the bucket
        file_format: File format (parquet, csv, json)
        
    Returns:
        True if successful, False otherwise
    """
    # Create catalog file if it doesn't exist
    if not os.path.exists(cat_path):
        catalog = {}
    else:
        catalog = yaml.safe_load(Path(cat_path).read_text()) or {}
    
    # Add or update table definition
    catalog[table_name] = {
        'bucket': bucket,
        'prefix': prefix,
        'format': file_format
    }
    
    # Write back to file
    Path(cat_path).write_text(yaml.dump(catalog, default_flow_style=False))
    
    return True
