"""
Database module for OpenAthena.

This module provides functionality for interacting with DuckDB and configuring
the database connection to work with OpenS3.
"""

import os
import duckdb
from pathlib import Path
from typing import Optional, Union, Dict, Any

from open_athena.catalog import load_catalog


class DuckDBManager:
    """Manages DuckDB connection and operations for OpenAthena."""
    
    def __init__(
        self,
        database_path: Optional[str] = None,
        catalog_path: str = "catalog.yml",
        threads: int = 4,
        memory_limit: str = "4GB",
        enable_caching: bool = True
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
        enable_caching: bool
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
            self.connection.sql("INSTALL httpfs; LOAD httpfs;")
            print("Loaded httpfs extension for S3 access")
        except Exception as e:
            print(f"Error loading httpfs extension: {e}")
    
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
        use_ssl: bool = True
    ) -> None:
        """
        Configure S3 credentials for DuckDB httpfs.
        
        Args:
            access_key: S3 access key
            secret_key: S3 secret key
            endpoint: S3 endpoint (for OpenS3)
            region: S3 region
            use_ssl: Whether to use SSL
        """
        # Use provided credentials or environment variables
        access_key = access_key or os.environ.get("AWS_ACCESS_KEY_ID")
        secret_key = secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
        endpoint = endpoint or os.environ.get("S3_ENDPOINT")
        region = region or os.environ.get("AWS_REGION", "us-east-1")
        
        if access_key and secret_key:
            # Set global variables for httpfs
            self.connection.sql(f"SET s3_access_key_id='{access_key}';")
            self.connection.sql(f"SET s3_secret_access_key='{secret_key}';")
            
            if endpoint:
                self.connection.sql(f"SET s3_endpoint='{endpoint}';")
            
            self.connection.sql(f"SET s3_region='{region}';")
            self.connection.sql(f"SET s3_use_ssl={str(use_ssl).lower()};")
            
            print("Configured S3 credentials for DuckDB")
        else:
            print("No S3 credentials provided - relying on environment variables")
    
    def close(self) -> None:
        """Close the DuckDB connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
