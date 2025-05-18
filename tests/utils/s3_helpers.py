#!/usr/bin/env python3
"""
OpenAthena - S3/OpenS3 Testing Utilities

This module provides helper functions for testing S3/OpenS3 connectivity
and data access in OpenAthena tests.
"""

import os
import tempfile
import uuid
import requests
from requests.auth import HTTPBasicAuth
from typing import Tuple, List, Dict, Optional, Any


def get_s3_credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get S3/OpenS3 credentials from environment variables.
    
    Returns:
        Tuple of (endpoint, access_key, secret_key)
    """
    endpoint = os.environ.get("OPENS3_ENDPOINT") or os.environ.get("S3_ENDPOINT")
    access_key = os.environ.get("OPENS3_ACCESS_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("OPENS3_SECRET_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    return endpoint, access_key, secret_key


def list_buckets(endpoint: str, access_key: str, secret_key: str) -> List[str]:
    """
    List all buckets in the S3/OpenS3 server.
    
    Args:
        endpoint: S3/OpenS3 endpoint URL
        access_key: Access key ID
        secret_key: Secret access key
        
    Returns:
        List of bucket names
        
    Raises:
        Exception if the request fails
    """
    response = requests.get(
        f"{endpoint}/buckets",
        auth=HTTPBasicAuth(access_key, secret_key)
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to list buckets: {response.status_code} {response.text}")
    
    buckets = response.json().get('buckets', [])
    return [bucket['name'] for bucket in buckets]


def find_csv_in_bucket(endpoint: str, access_key: str, secret_key: str, bucket: str) -> Optional[Dict[str, Any]]:
    """
    Find a CSV file in a bucket.
    
    Args:
        endpoint: S3/OpenS3 endpoint URL
        access_key: Access key ID
        secret_key: Secret access key
        bucket: Bucket name
        
    Returns:
        Dict with file information or None if no CSV file is found
    """
    try:
        response = requests.get(
            f"{endpoint}/buckets/{bucket}/objects",
            auth=HTTPBasicAuth(access_key, secret_key)
        )
        
        if response.status_code != 200:
            return None
        
        objects = response.json().get('objects', [])
        for obj in objects:
            if obj['key'].lower().endswith('.csv'):
                return obj
        
        return None
    except Exception:
        return None


def download_file(endpoint: str, access_key: str, secret_key: str, 
                  bucket: str, file_key: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Download a file from S3/OpenS3 and store in a temporary location.
    
    Args:
        endpoint: S3/OpenS3 endpoint URL
        access_key: Access key ID
        secret_key: Secret access key
        bucket: Bucket name
        file_key: File key (path)
        
    Returns:
        Tuple of (file_content, temp_file_path) or (None, None) if download fails
    """
    try:
        response = requests.get(
            f"{endpoint}/buckets/{bucket}/objects/{file_key}",
            auth=HTTPBasicAuth(access_key, secret_key)
        )
        
        if response.status_code != 200:
            return None, None
            
        # Create a temporary file with a safe name
        temp_dir = tempfile.gettempdir()
        safe_filename = f"openathena_test_{uuid.uuid4().hex[:8]}.csv"
        temp_file = os.path.join(temp_dir, safe_filename)
        
        # Save the content
        with open(temp_file, "wb") as f:
            f.write(response.content)
            
        return response.content, temp_file
    except Exception:
        return None, None


def create_safe_path(file_path: str) -> str:
    """
    Create a path that is safe for DuckDB to use in SQL queries.
    Handles special characters like apostrophes that might cause SQL syntax errors.
    
    Args:
        file_path: Original file path
        
    Returns:
        Safe path for DuckDB
    """
    # Use forward slashes for consistency
    safe_path = file_path.replace('\\', '/')
    
    # Handle paths with special characters by using a temp file if needed
    if "'" in safe_path or "-" in safe_path or " " in safe_path:
        temp_dir = tempfile.gettempdir()
        safe_filename = f"openathena_test_{uuid.uuid4().hex[:8]}.csv"
        temp_file = os.path.join(temp_dir, safe_filename).replace('\\', '/')
        
        # Copy the file to a safe location if it exists
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, temp_file)
            return temp_file
    
    return safe_path


def cleanup_temp_file(file_path: Optional[str]) -> None:
    """
    Clean up a temporary file if it exists.
    
    Args:
        file_path: Path to temporary file
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass  # Ignore errors during cleanup
