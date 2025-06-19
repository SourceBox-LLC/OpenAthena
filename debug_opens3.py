import requests
import json
import os

# OpenS3 connection details (same as in our proxy)
OPENS3_URL = "http://localhost:8001"
USERNAME = "admin"
PASSWORD = "password"

def list_buckets():
    """List all buckets in OpenS3."""
    url = f"{OPENS3_URL}/buckets"
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    
    if response.status_code == 200:
        result = response.json()
        # Handle the case where buckets are in a 'buckets' key
        if isinstance(result, dict) and 'buckets' in result:
            buckets = result['buckets']
        else:
            buckets = result
        
        print(f"Found {len(buckets)} buckets:")
        print(json.dumps(buckets, indent=2))
        return buckets
    else:
        print(f"Failed to list buckets: {response.status_code}")
        return []

def list_objects(bucket):
    """List objects in the specified bucket."""
    url = f"{OPENS3_URL}/buckets/{bucket}/objects"
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    
    if response.status_code == 200:
        result = response.json()
        
        # Handle the case where objects are in an 'objects' key
        if isinstance(result, dict) and 'objects' in result:
            objects = result['objects']
        else:
            objects = result
            
        print(f"\nFound {len(objects)} objects in bucket '{bucket}':")
        print(json.dumps(objects, indent=2))
        
        # Print the structure of the first object to see what fields we need to match
        if objects and len(objects) > 0:
            print("\nObject structure:")
            first_obj = objects[0]
            print(f"Type: {type(first_obj)}")
            if isinstance(first_obj, dict):
                print("Keys:", list(first_obj.keys()))
            return objects
    else:
        print(f"Failed to list objects in bucket '{bucket}': {response.status_code}")
    return []

def test_wildcard_matching(bucket, objects, wildcard="*.csv"):
    """Test our wildcard matching logic with actual objects."""
    print(f"\nTesting wildcard matching for '{wildcard}' in bucket '{bucket}':")
    
    # Extract extension from wildcard
    extension = None
    if wildcard.startswith("*."):
        extension = wildcard[2:]  # e.g., 'csv' from '*.csv'
    
    print(f"Looking for files with extension: {extension}")
    
    matching = []
    for obj in objects:
        # Check how objects are structured
        if isinstance(obj, dict):
            name = obj.get('name', obj.get('key', '')) 
        else:
            name = str(obj)
            
        # Check if matches extension
        if name.lower().endswith(f".{extension.lower()}"):
            matching.append(name)
            print(f"✓ Matched: {name}")
    
    print(f"Found {len(matching)} matching objects for wildcard '{wildcard}'")
    return matching

if __name__ == "__main__":
    print("OpenS3 Debug Tool")
    print("================")
    
    # List buckets
    buckets = list_buckets()
    
    # For each bucket, list objects and test wildcard matching
    for bucket_info in buckets:
        if isinstance(bucket_info, dict):
            bucket_name = bucket_info.get('name', '')
        else:
            bucket_name = str(bucket_info)
            
        if bucket_name:
            print(f"\n====== Bucket: {bucket_name} ======")
            objects = list_objects(bucket_name)
            
            # Test CSV matching
            test_wildcard_matching(bucket_name, objects, "*.csv")
            
            # Test Parquet matching
            test_wildcard_matching(bucket_name, objects, "*.parquet")
