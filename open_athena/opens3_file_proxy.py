"""
OpenS3 File Proxy for OpenAthena

This module provides a proxy layer between OpenAthena and OpenS3 to work around
HTTP compatibility issues between DuckDB 1.2.2 and OpenS3.

It downloads files from OpenS3 to a local cache directory and provides utilities
to convert OpenS3 URLs to local file paths.
"""

import os
import tempfile
import time
import logging
import requests
import shutil
from urllib.parse import urlparse
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CACHE_DIR = os.path.join(tempfile.gettempdir(), "openathena_opens3_cache")
CACHE_EXPIRATION_SECONDS = 3600  # 1 hour cache expiration
OPENS3_URL = "http://localhost:8001"
OPENS3_USERNAME = "admin"
OPENS3_PASSWORD = "password"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


class OpenS3FileProxy:
    """
    Proxy class to download and cache files from OpenS3 for local access by DuckDB.
    """

    def __init__(self, 
                 opens3_url: str = None, 
                 username: str = None, 
                 password: str = None,
                 cache_dir: str = None,
                 cache_expiration: int = None):
        """
        Initialize the OpenS3 file proxy.
        
        Args:
            opens3_url: The base URL of the OpenS3 server
            username: OpenS3 username for authentication
            password: OpenS3 password for authentication
            cache_dir: Directory to store cached files
            cache_expiration: Cache expiration time in seconds
        """
        # Use parameters or environment variables or defaults
        self.opens3_url = opens3_url or os.environ.get("OPENS3_ENDPOINT", OPENS3_URL)
        self.username = username or os.environ.get("OPENS3_ACCESS_KEY", OPENS3_USERNAME)
        self.password = password or os.environ.get("OPENS3_SECRET_KEY", OPENS3_PASSWORD)
        self.cache_dir = cache_dir or os.environ.get("OPENATHENA_CACHE_DIR", CACHE_DIR)
        self.cache_expiration = cache_expiration or int(os.environ.get("OPENATHENA_CACHE_EXPIRATION", CACHE_EXPIRATION_SECONDS))
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create a cache metadata file to track last access time
        self.cache_metadata_path = os.path.join(self.cache_dir, "cache_metadata.json")
        self._load_cache_metadata()
        
        logger.info(f"OpenS3FileProxy initialized with cache at {self.cache_dir}")

    def _load_cache_metadata(self):
        """Load cache metadata from JSON file."""
        if os.path.exists(self.cache_metadata_path):
            try:
                with open(self.cache_metadata_path, 'r') as f:
                    self.cache_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}. Creating new metadata.")
                self.cache_metadata = {"files": {}}
        else:
            self.cache_metadata = {"files": {}}
    
    def _save_cache_metadata(self):
        """Save cache metadata to JSON file."""
        try:
            with open(self.cache_metadata_path, 'w') as f:
                json.dump(self.cache_metadata, f)
        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")

    def clean_expired_cache(self):
        """Remove expired files from cache."""
        now = time.time()
        removed_count = 0
        
        for cached_path, metadata in list(self.cache_metadata["files"].items()):
            if now - metadata["last_access"] > self.cache_expiration:
                full_path = os.path.join(self.cache_dir, cached_path)
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                    del self.cache_metadata["files"][cached_path]
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove expired cache file {full_path}: {e}")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} expired cache files")
            self._save_cache_metadata()

    def list_buckets(self) -> List[str]:
        """
        List all buckets in OpenS3.
        
        Returns:
            A list of bucket names
        """
        url = f"{self.opens3_url}/buckets"
        response = requests.get(url, auth=(self.username, self.password))
        
        if response.status_code == 200:
            data = response.json()
            buckets = [bucket["name"] for bucket in data]
            return buckets
        else:
            logger.error(f"Failed to list buckets: {response.status_code}")
            return []

    def list_objects(self, bucket: str) -> List[Dict]:
        """
        List objects in a bucket.
        
        Args:
            bucket: The bucket name
            
        Returns:
            A list of object metadata dictionaries with standardized fields
        """
        url = f"{self.opens3_url}/buckets/{bucket}/objects"
        try:
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle the case where objects are in an 'objects' key
                if isinstance(result, dict) and 'objects' in result:
                    objects = result['objects']
                else:
                    objects = result
                
                logger.info(f"Found {len(objects)} objects in bucket {bucket}")
                
                # Standardize object structure to always have 'name' field (copy from 'key')
                standardized_objects = []
                for obj in objects:
                    if isinstance(obj, dict):
                        # Make a copy to avoid modifying the original
                        std_obj = obj.copy()
                        # Ensure 'name' exists, copy from 'key' if needed
                        if 'name' not in std_obj and 'key' in std_obj:
                            std_obj['name'] = std_obj['key']
                        standardized_objects.append(std_obj)
                    else:
                        # Handle case where object is just a string
                        standardized_objects.append({'name': str(obj), 'key': str(obj)})
                
                return standardized_objects
            else:
                logger.error(f"Failed to list objects in bucket {bucket}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception listing objects in bucket {bucket}: {e}")
            return []

    def download_file(self, bucket: str, object_key: str) -> Optional[str]:
        """
        Download a file from OpenS3 and save it to local cache.
        
        Args:
            bucket: The bucket name
            object_key: The object key (file name)
            
        Returns:
            Local file path if successful, None otherwise
        """
        # Handle potential wildcard characters in the object key
        if '*' in object_key:
            logger.warning(f"Wildcard detected in direct file path: {object_key}")
            logger.warning("This should have been handled by convert_url_to_local_path.")  
            return None
            
        # Create cache structure that mirrors OpenS3 structure
        cache_relative_path = os.path.join(bucket, object_key.replace('/', os.path.sep))
        cache_full_path = os.path.join(self.cache_dir, cache_relative_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(cache_full_path), exist_ok=True)
        
        # Check if file exists in cache and is not expired
        if cache_relative_path in self.cache_metadata["files"]:
            metadata = self.cache_metadata["files"][cache_relative_path]
            if os.path.exists(cache_full_path) and time.time() - metadata["last_access"] < self.cache_expiration:
                # Update last access time
                self.cache_metadata["files"][cache_relative_path]["last_access"] = time.time()
                self._save_cache_metadata()
                logger.debug(f"Using cached file: {cache_full_path}")
                return cache_full_path
        
        # Download file from OpenS3
        url = f"{self.opens3_url}/buckets/{bucket}/objects/{object_key}"
        try:
            response = requests.get(url, auth=(self.username, self.password), stream=True)
            
            if response.status_code == 200:
                with open(cache_full_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                # Update cache metadata
                self.cache_metadata["files"][cache_relative_path] = {
                    "last_access": time.time(),
                    "size": os.path.getsize(cache_full_path),
                    "source_url": url
                }
                self._save_cache_metadata()
                
                logger.info(f"Downloaded {url} to {cache_full_path}")
                return cache_full_path
            else:
                logger.error(f"Failed to download {url}: {response.status_code}")
                
                # Try with alternate paths if this failed
                if '/' in object_key and object_key.split('/')[0] in ['csv', 'parquet']:
                    # Try downloading from the bucket root
                    alt_key = object_key.split('/')[-1]
                    logger.info(f"Trying alternate path: {bucket}/{alt_key}")
                    return self.download_file(bucket, alt_key)
                return None
        except Exception as e:
            logger.error(f"Exception downloading {url}: {e}")
            return None

    def convert_url_to_local_path(self, url: str) -> Optional[str]:
        """
        Convert an OpenS3 URL to a local file path.
        
        This handles various URL formats:
        - http://user:pass@host:port/buckets/bucket/objects/key
        - s3://bucket/key
        - http://user:pass@host:port/bucket/key
        
        Also handles wildcards (* and **) by listing and downloading the first matching file.
        
        Args:
            url: The OpenS3 URL
            
        Returns:
            Local file path if successful, None otherwise
        """
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Handle http(s):// URLs
        if parsed_url.scheme in ['http', 'https']:
            path_parts = parsed_url.path.strip('/').split('/')
            
            # Handle REST-style path: /buckets/bucket/objects/key
            if len(path_parts) >= 4 and path_parts[0] == 'buckets' and path_parts[2] == 'objects':
                bucket = path_parts[1]
                object_key = '/'.join(path_parts[3:])
            # Handle legacy style path: /bucket/key
            else:
                bucket = path_parts[0]
                object_key = '/'.join(path_parts[1:])
            
            # Check if path contains wildcards
            if '*' in object_key:
                # Get prefix before wildcard
                prefix = object_key.split('*')[0]
                extension = None
                
                # Special case handling for directory patterns like 'csv/*'
                if '/' in prefix:
                    folder = prefix.rstrip('/').split('/')[-1]
                    if folder in ['csv', 'parquet']:
                        extension = folder
                
                # List objects in bucket
                try:
                    objects = self.list_objects(bucket)
                    if not objects:
                        logger.error(f"No objects found in bucket {bucket}")
                        return None
                        
                    # Try to find any matching object
                    matching_objects = []
                    for obj in objects:
                        name = obj.get('name', obj.get('key', '')) if isinstance(obj, dict) else str(obj)
                        logger.debug(f"Checking object: {name} against prefix={prefix}, extension={extension}")
                        
                        # Special case for csv/* or parquet/* patterns - match by extension
                        if extension and name.lower().endswith('.' + extension):
                            matching_objects.append(name)
                            logger.info(f"Matched by extension: {name}")
                            continue
                            
                        # Standard prefix matching
                        if prefix:
                            # For http-style paths with directories
                            if prefix.endswith('/') and name.startswith(prefix):
                                matching_objects.append(name)
                                logger.info(f"Matched by directory prefix: {name}")
                            # For exact path prefix matches
                            elif name.startswith(prefix):
                                matching_objects.append(name)
                                logger.info(f"Matched by exact prefix: {name}")
                            # Otherwise add all files in bucket if prefix is empty or just a folder type
                            elif not prefix or prefix in ['csv', 'parquet']:
                                matching_objects.append(name)
                                logger.info(f"Added with empty/type prefix: {name}")
                        else:
                            # No prefix - match all
                            matching_objects.append(name)
                            logger.info(f"Matched all: {name}")
                    
                    if matching_objects:
                        # Download the first matching object
                        logger.info(f"Found {len(matching_objects)} matching files for {url}")
                        logger.debug(f"First match: {matching_objects[0]}")
                        return self.download_file(bucket, matching_objects[0])
                    else:
                        logger.error(f"No matching objects found for wildcard pattern {object_key} in bucket {bucket}")
                        return None
                except Exception as e:
                    logger.error(f"Error handling wildcard URL {url}: {e}")
                    return None
            else:
                # No wildcards, download directly
                return self.download_file(bucket, object_key)
            
        # Handle s3:// URLs
        elif parsed_url.scheme == 's3':
            bucket = parsed_url.netloc
            object_key = parsed_url.path.strip('/')
            
            # Check if path contains wildcards
            if '*' in object_key:
                # Extract file extension from wildcard pattern
                extension = None
                prefix = ''
                
                # Handle patterns like *.csv or *.parquet
                if object_key.startswith('*.'):
                    extension = object_key[2:]  # Extract extension (e.g., 'csv' from '*.csv')
                    prefix = ''  # No prefix in this case
                    logger.info(f"Detected wildcard pattern with extension: *.{extension}")
                # Handle patterns with directory prefix like dir/*.csv
                elif '*.' in object_key:
                    parts = object_key.split('*.')
                    prefix = parts[0]  # Directory prefix
                    extension = parts[1]  # Extension
                    logger.info(f"Detected wildcard pattern with prefix and extension: {prefix}*.{extension}")
                # Handle other wildcard patterns
                elif '*' in object_key:
                    prefix = object_key.split('*')[0]
                    logger.info(f"Detected wildcard pattern with prefix: {prefix}*")
                    
                    # Check if the prefix itself looks like a file format
                    if prefix in ['csv/', 'parquet/']:
                        extension = prefix.rstrip('/')
                
                logger.info(f"Handling wildcard S3 path: s3://{bucket}/{object_key} with prefix='{prefix}', extension='{extension}'")
                
                try:
                    # List objects in bucket
                    objects = self.list_objects(bucket)
                    if not objects:
                        logger.error(f"No objects found in bucket {bucket}")
                        return None
                    
                    logger.info(f"Found {len(objects)} total objects in bucket {bucket}")
                    
                    # Try to find any matching object
                    matching_objects = []
                    for obj in objects:
                        # Extract object name, handling different response formats
                        if isinstance(obj, dict):
                            name = obj.get('name', obj.get('key', ''))
                        else:
                            name = str(obj)
                            
                        logger.debug(f"Checking object: {name}")
                        
                        # Case 1: Match by extension (*.csv, *.parquet)
                        if extension and name.lower().endswith(f".{extension.lower()}"):
                            # If there's a prefix, ensure the file is in that directory
                            if not prefix or name.startswith(prefix):
                                matching_objects.append(name)
                                logger.info(f"✅ Matched by extension: {name}")
                                continue
                        
                        # Case 2: Match by prefix
                        if prefix and name.startswith(prefix):
                            matching_objects.append(name)
                            logger.info(f"✅ Matched by prefix: {name}")
                            continue
                        
                        # Case 3: If this is a simple wildcard with no prefix/extension,
                        # include all files in the bucket
                        if not prefix and not extension and object_key == '*':
                            matching_objects.append(name)
                            logger.info(f"✅ Matched all: {name}")
                            continue
                    
                    if matching_objects:
                        # Download the first matching object
                        logger.info(f"Found {len(matching_objects)} matching files for {url}")
                        logger.debug(f"First match: {matching_objects[0]}")
                        return self.download_file(bucket, matching_objects[0])
                    else:
                        logger.error(f"No matching objects found for wildcard pattern {object_key} in bucket {bucket}")
                        return None
                except Exception as e:
                    logger.error(f"Error handling wildcard S3 URL {url}: {e}")
                    return None
            else:
                # No wildcards, download directly
                return self.download_file(bucket, object_key)
            
        else:
            logger.error(f"Unsupported URL scheme: {url}")
            return None

    def update_catalog_query(self, query: str) -> str:
        """
        Update a catalog query to use local file paths instead of OpenS3 URLs.
        
        Args:
            query: The original catalog query
            
        Returns:
            Updated query with local file paths
        """
        # Look for URLs in the query
        # This is a simple approach; a more robust solution would use SQL parsing
        url_markers = ["'http://", "'s3://", "\"http://", "\"s3://"]
        
        for marker in url_markers:
            if marker in query:
                # Split by URL marker and process each part
                parts = query.split(marker)
                new_parts = [parts[0]]
                
                for i in range(1, len(parts)):
                    # Find the end of the URL (either ' or ")
                    quote_char = "'" if marker.startswith("'") else "\""
                    url_end = parts[i].find(quote_char)
                    
                    if url_end != -1:
                        url = marker[1:] + parts[i][:url_end]  # Extract URL without quotes
                        local_path = self.convert_url_to_local_path(url)
                        
                        if local_path:
                            # Replace URL with local path, properly escaping apostrophes for SQL
                            if quote_char == "'":
                                # For single quotes, double them for SQL escaping
                                escaped_path = local_path.replace("'", "''")
                                new_parts.append(f"{quote_char}{escaped_path}{quote_char}{parts[i][url_end+1:]}")
                            else:
                                # For double quotes, no special escaping needed
                                new_parts.append(f"{quote_char}{local_path}{quote_char}{parts[i][url_end+1:]}")
                            
                            # Log the path transformation for debugging
                            logger.info(f"Converted URL '{url}' to local path '{local_path}' (escaped for SQL)")
                        else:
                            # Keep original if conversion failed
                            new_parts.append(f"{marker[1:]}{parts[i]}")
                    else:
                        new_parts.append(f"{marker[1:]}{parts[i]}")
                
                query = ''.join(new_parts)
        
        return query
    
    def proxy_all_requests(self):
        """
        Clean up expired cache files and prepare for new requests.
        Should be called once during initialization.
        """
        self.clean_expired_cache()
        logger.info("OpenS3FileProxy is ready to proxy requests")


# Singleton instance for application-wide use
_proxy_instance = None

def get_proxy_instance(**kwargs) -> OpenS3FileProxy:
    """
    Get or create the singleton proxy instance.
    
    Args:
        **kwargs: Arguments to pass to OpenS3FileProxy constructor
        
    Returns:
        The OpenS3FileProxy instance
    """
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenS3FileProxy(**kwargs)
    return _proxy_instance


def initialize_proxy():
    """Initialize the proxy when the application starts."""
    proxy = get_proxy_instance()
    proxy.proxy_all_requests()
    return proxy


def download_all_catalog_files(catalog_data: Dict) -> Dict:
    """
    Process a catalog dictionary and download all referenced OpenS3 files.
    
    Args:
        catalog_data: The catalog data dictionary
        
    Returns:
        Updated catalog data with local file paths
    """
    proxy = get_proxy_instance()
    updated_catalog = {}
    
    for entry_name, entry_data in catalog_data.items():
        # Copy entry data
        updated_entry = dict(entry_data)
        
        # Update query if it exists
        if "query" in updated_entry:
            updated_entry["query"] = proxy.update_catalog_query(updated_entry["query"])
        
        updated_catalog[entry_name] = updated_entry
    
    return updated_catalog


if __name__ == "__main__":
    # Example usage
    proxy = OpenS3FileProxy()
    buckets = proxy.list_buckets()
    print(f"Available buckets: {buckets}")
    
    for bucket in buckets:
        objects = proxy.list_objects(bucket)
        print(f"Objects in {bucket}: {objects}")
        
        for obj in objects:
            local_path = proxy.download_file(bucket, obj["name"])
            print(f"Downloaded to {local_path}")
    
    print("Example catalog query update:")
    query = "SELECT * FROM read_csv_auto('http://admin:password@localhost:8001/buckets/test-analytics/objects/sample_data.csv')"
    updated_query = proxy.update_catalog_query(query)
    print(f"Original: {query}")
    print(f"Updated:  {updated_query}")
