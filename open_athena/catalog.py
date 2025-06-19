"""
Catalog module for OpenAthena.

This module provides functionality to manage data sources using a YAML-based catalog.
"""

import os
import yaml
from pathlib import Path
import tempfile
from typing import Dict, Any, Optional
import logging

# Import the OpenS3 file proxy
from open_athena.opens3_file_proxy import get_proxy_instance, initialize_proxy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    # Initialize the OpenS3 file proxy
    proxy = initialize_proxy()
    logger.info("OpenS3 file proxy initialized for catalog loading")
    
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
            
        # Check if there's a query defined in the catalog
        if 'query' in meta:
            query = meta['query']
            try:
                # Use our proxy to process the query and download any OpenS3 files it references
                processed_query = proxy.update_catalog_query(query)
                
                # Make sure table name is SQL safe
                safe_tbl = f'"{tbl}"' if "-" in tbl else tbl
                
                # Create the view with the processed query
                view_query = f"CREATE OR REPLACE VIEW {safe_tbl} AS {processed_query}"
                con.sql(view_query)
                
                logger.info(f"✅ Created view for table '{tbl}' using proxy")
                print(f"✅ Created view for table '{tbl}' using local file proxy")
            except Exception as e:
                logger.error(f"❌ Error creating view for table '{tbl}': {e}")
                print(f"❌ Error creating view for table '{tbl}': {e}")
                # Create a dummy view with error information as fallback
                con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT 1 as id, 'Error: {str(e).replace("'", "''")}' as error_message WHERE 1=0;")
            continue
            
        # Regular S3 table setup (legacy method)
        bucket = meta.get('bucket', '')
        prefix = meta.get('prefix', '')
        file_format = meta.get('format', 'parquet')
        
        try:
            # Build S3 path pattern
            original_path = f"s3://{bucket}/{prefix}**/*.{file_format}"
            
            # Make sure table name is SQL safe
            safe_tbl = f'"{tbl}"' if "-" in tbl else tbl
            
            # Use our proxy to create a local path instead of S3 path
            # For wildcard paths, we'll list objects and download the first one as a sample
            logger.info(f"Listing objects in bucket {bucket} with prefix {prefix}")
            objects = proxy.list_objects(bucket)
            
            if objects:
                # Filter by file format and prefix
                matching_objects = []
                for obj in objects:
                    # Handle different possible object structures
                    if isinstance(obj, dict):
                        # Get name from dict (could be 'name' or 'key')
                        name = obj.get('name', obj.get('key', ''))
                    else:
                        # Or handle case where object is just a string
                        name = str(obj)
                        
                    # Check if this object matches our criteria
                    if name.endswith(f".{file_format}") and (not prefix or name.startswith(prefix)):
                        matching_objects.append({'name': name})  # Standardize to dict with 'name' key
                        logger.info(f"Added matching object: {name}")
                
                if matching_objects:
                    # Download the first matching object
                    first_object = matching_objects[0]['name']
                    local_path = proxy.download_file(bucket, first_object)
                    
                    if local_path:
                        # Double escape the apostrophes in the path for SQL
                        sql_safe_path = local_path.replace("'", "''")
                        
                        # Create the view using the local file
                        if file_format.lower() == 'parquet':
                            con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT * FROM read_parquet('{sql_safe_path}');")
                        elif file_format.lower() == 'csv':
                            con.sql(f"CREATE OR REPLACE VIEW {safe_tbl} AS SELECT * FROM read_csv_auto('{sql_safe_path}');")
                        else:
                            # Other formats as needed
                            raise ValueError(f"Unsupported file format: {file_format}")
                        
                        logger.info(f"✅ Created view for table '{tbl}' using proxy with local file {local_path}")
                        print(f"✅ Created view for table '{tbl}' using local file proxy")
                    else:
                        raise Exception(f"Failed to download file from bucket {bucket}")
                else:
                    raise Exception(f"No files found matching {file_format} format with prefix {prefix} in bucket {bucket}")
            else:
                raise Exception(f"No objects found in bucket {bucket}")
                
        except Exception as e:
            logger.error(f"❌ Error creating view for table '{tbl}': {e}")
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
