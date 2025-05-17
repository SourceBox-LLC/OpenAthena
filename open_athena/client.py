"""
Client module for OpenAthena.

This module provides a client for interacting with the OpenAthena API.
"""

import io
import json
import requests
import pyarrow as pa
import pandas as pd
from typing import Dict, List, Any, Optional, Union


class OpenAthenaClient:
    """Client for interacting with the OpenAthena API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize OpenAthena client.
        
        Args:
            base_url: Base URL of the OpenAthena API
        """
        self.base_url = base_url.rstrip("/")
    
    def execute_query(
        self, 
        query: str, 
        format: str = "arrow"
    ) -> Union[pd.DataFrame, str]:
        """
        Execute a SQL query against OpenAthena.
        
        Args:
            query: SQL query to execute
            format: Output format (arrow or csv)
            
        Returns:
            Pandas DataFrame for arrow format, CSV string for csv format
        """
        url = f"{self.base_url}/sql"
        params = {"format": format}
        
        response = requests.post(url, data=query, params=params)
        response.raise_for_status()
        
        if format.lower() == "csv":
            return response.text
        else:
            # Parse Arrow response
            reader = pa.ipc.RecordBatchStreamReader(pa.BufferReader(response.content))
            table = reader.read_all()
            return table.to_pandas()
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the catalog.
        
        Returns:
            Dictionary of tables from the catalog
        """
        url = f"{self.base_url}/tables"
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def reload_catalog(self) -> Dict[str, str]:
        """
        Reload the catalog configuration.
        
        Returns:
            Success message
        """
        url = f"{self.base_url}/catalog/reload"
        response = requests.post(url)
        response.raise_for_status()
        
        return response.json()
    
    def add_table(
        self,
        table_name: str,
        bucket: str,
        prefix: str,
        file_format: str = "parquet"
    ) -> Dict[str, str]:
        """
        Add a new table to the catalog.
        
        Args:
            table_name: Name of the table to create
            bucket: S3 bucket name
            prefix: Prefix path within the bucket
            file_format: File format (parquet, csv, json)
            
        Returns:
            Success message
        """
        url = f"{self.base_url}/catalog/tables"
        params = {
            "table_name": table_name,
            "bucket": bucket,
            "prefix": prefix,
            "file_format": file_format
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def health_check(self) -> Dict[str, str]:
        """
        Check if the OpenAthena API is healthy.
        
        Returns:
            Health status
        """
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
