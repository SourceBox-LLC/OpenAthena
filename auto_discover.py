#!/usr/bin/env python3
"""
OpenAthena - OpenS3 Auto Discovery Tool

This script automatically discovers buckets and content in an OpenS3 server
and generates a catalog.yml file for OpenAthena.

It provides both S3 protocol and HTTP direct access methods for each object
and attempts to reload the OpenAthena catalog after updating.
"""

import csv
import io
import os
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests
import yaml
from requests.auth import HTTPBasicAuth

# Try to import DuckDB, but continue if it's not available
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print(
        "\u26a0 DuckDB not available, will use basic CSV parsing for schema detection"
    )


def reload_openathena_catalog(host="localhost", port=8000):
    """
    Trigger a catalog reload in OpenAthena via its API
    """
    print(f"🔄 Attempting to reload OpenAthena catalog via API")

    try:
        # Try different potential reload endpoints
        endpoints = [
            f"http://{host}:{port}/maintenance/reload-catalog",  # Standard endpoint
            f"http://{host}:{port}/api/reload-catalog",  # Alternative API path
            f"http://{host}:{port}/catalog/reload",  # Another common pattern
        ]

        for endpoint in endpoints:
            try:
                print(f"  🔍 Trying endpoint: {endpoint}")
                response = requests.post(endpoint)

                if response.status_code == 200:
                    print(f"  ✅ Successfully reloaded catalog via {endpoint}")
                    return True
                else:
                    print(
                        f"  ⚠️ Failed with status {response.status_code}: {response.text}"
                    )
            except Exception as e:
                print(f"  ⚠️ Error with endpoint {endpoint}: {str(e)}")

        print("❌ All catalog reload endpoints failed")
        return False
    except Exception as e:
        print(f"❌ Error reloading catalog: {str(e)}")
        return False


def discover_openS3_content(
    endpoint=None,
    access_key=None,
    secret_key=None,
    output_path=None,
    reload_catalog=True,
):
    """
    Discover all buckets and content in OpenS3 and generate catalog.yml
    """
    # Use environment variables if not provided
    endpoint = endpoint or os.environ.get("OPENS3_ENDPOINT", "http://localhost:8001")
    access_key = access_key or os.environ.get("OPENS3_ACCESS_KEY", "admin")
    secret_key = secret_key or os.environ.get("OPENS3_SECRET_KEY", "password")

    if output_path is None:
        output_path = os.environ.get("OPENATHENA_CATALOG_PATH", "catalog.yml")

    print(f"🔍 Discovering OpenS3 content at {endpoint}")
    print(f"🔑 Using credentials: {access_key} / {'*' * len(secret_key)}")

    # Initialize catalog structure
    catalog = {
        "test_connection": {"type": "dummy"},
        # Add a local_csv entry for testing
        "local_csv": {
            "type": "view",
            "query": "SELECT * FROM read_csv_auto('C:/Users/S''Bussiso/Desktop/Open Projects/test_data/local_test.csv')",
        },
    }

    # Get all buckets
    try:
        response = requests.get(
            f"{endpoint}/buckets", auth=HTTPBasicAuth(access_key, secret_key)
        )

        if response.status_code != 200:
            print(f"❌ Failed to list buckets: HTTP {response.status_code}")
            return False

        # Get the response data
        response_data = response.json()

        # Handle different API formats
        buckets = []
        if isinstance(response_data, dict) and "buckets" in response_data:
            # Format: {"buckets": [...]}
            buckets = response_data["buckets"]
        elif isinstance(response_data, list):
            # Format: [bucket1, bucket2, ...]
            buckets = response_data
        elif isinstance(response_data, dict):
            # Format: {bucket1: {...}, bucket2: {...}}
            # In this case, get all the top-level keys
            print("DEBUG: Treating dictionary keys as bucket names")
            buckets = list(response_data.keys())
            if "buckets" in buckets and len(buckets) == 1:
                # Special case - this might be a container with a buckets field
                print("DEBUG: Found single 'buckets' key, trying to look inside it")
                buckets_data = response_data["buckets"]
                if isinstance(buckets_data, list):
                    buckets = buckets_data

        print(f"✅ Found {len(buckets)} buckets")

        # Get each bucket from the list
        for bucket_item in buckets:
            # Extract bucket name based on format
            if isinstance(bucket_item, dict) and "name" in bucket_item:
                bucket_name = bucket_item["name"]
            elif isinstance(bucket_item, str):
                bucket_name = bucket_item
            else:
                print(f"⚠️ Skipping bucket with unknown format: {bucket_item}")
                continue

            print(f"\n📦 Analyzing bucket: {bucket_name}")

            # Get objects in bucket - try different endpoint formats
            endpoints_to_try = [
                f"{endpoint}/buckets/{bucket_name}/objects",  # Standard format
                f"{endpoint}/objects/{bucket_name}",  # Alternative format
                f"{endpoint}/api/buckets/{bucket_name}/objects",  # With API prefix
            ]

            objects = []
            success = False

            for obj_endpoint in endpoints_to_try:
                try:
                    print(f"  🔍 Trying to list objects at: {obj_endpoint}")
                    response = requests.get(
                        obj_endpoint, auth=HTTPBasicAuth(access_key, secret_key)
                    )

                    if response.status_code == 200:
                        # Successfully got objects
                        objects_data = response.json()

                        # Handle different API response formats
                        if isinstance(objects_data, list):
                            objects = objects_data
                        elif (
                            isinstance(objects_data, dict) and "objects" in objects_data
                        ):
                            objects = objects_data["objects"]
                        elif (
                            isinstance(objects_data, dict)
                            and "contents" in objects_data
                        ):
                            objects = objects_data["contents"]
                        else:
                            # Might be a dict with key/value pairs
                            print(
                                f"  DEBUG: Unknown objects format: {type(objects_data)}"
                            )
                            if isinstance(objects_data, dict):
                                # Try to get all files from dict keys
                                objects = [
                                    {"key": key, "size": "unknown"}
                                    for key in objects_data.keys()
                                ]

                        success = True
                        print(f"  ✅ Successfully retrieved objects list")
                        break
                except Exception as e:
                    print(f"  ⚠️ Error trying {obj_endpoint}: {str(e)}")
                    continue

            if not success:
                print(f"  ⚠️ Failed to list objects in bucket: {bucket_name}")
                continue

            if not objects:
                print(f"  ℹ️ Bucket is empty")
                continue

            print(f"  ✅ Found {len(objects)} objects")

            # Analyze file types and create appropriate table entries
            extensions = {}
            for obj in objects:
                # Skip metadata files
                if obj["key"].endswith(".metadata"):
                    continue

                ext = Path(obj["key"]).suffix.lower().lstrip(".")
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

            # Map extensions to DuckDB-compatible formats
            format_map = {
                "csv": "csv",
                "tsv": "csv",
                "parquet": "parquet",
                "json": "json",
                "jsonl": "json",
                "txt": "csv",  # Assuming simple text is CSV-like
            }

            # Create table entries for discovered formats
            for ext, count in extensions.items():
                if ext in format_map:
                    format_name = format_map[ext]
                    table_name = f"{bucket_name}_{ext}"

                    # Make table name SQL-safe
                    table_name = table_name.replace("-", "_").lower()

                    print(
                        f"  📋 Creating table definition: {table_name} ({count} {ext} files)"
                    )

                    # Create view that uses s3 protocol
                    catalog[table_name] = {
                        "type": "view",
                        "query": f"SELECT * FROM read_{format_name}_auto('s3://{bucket_name}/{ext}/*')",
                    }

                    # Create view that uses HTTP direct access for compatibility
                    # Extract host and port from endpoint
                    parsed_url = urllib.parse.urlparse(endpoint)
                    host_port = parsed_url.netloc

                    # Create an authenticated HTTP URL
                    http_url = f"http://{access_key}:{secret_key}@{host_port}/{bucket_name}/{ext}/*"

                    catalog[f"{table_name}_http"] = {
                        "type": "view",
                        "query": f"SELECT * FROM read_{format_name}_auto('{http_url}')",
                    }

                    # Also keep the original catalog format for compatibility
                    catalog[f"{table_name}_meta"] = {
                        "bucket": bucket_name,
                        "prefix": "",
                        "format": format_name,
                    }

                    # Try to detect schema by sampling a file
                    try:
                        # Find a sample file of this type
                        sample_files = [
                            obj
                            for obj in objects
                            if isinstance(obj, dict)
                            and "key" in obj
                            and obj["key"].lower().endswith(f".{ext}")
                            or isinstance(obj, str)
                            and obj.lower().endswith(f".{ext}")
                        ]

                        if sample_files:
                            # Get the key of the first sample file
                            if isinstance(sample_files[0], dict):
                                sample_file = sample_files[0]["key"]
                            else:
                                sample_file = sample_files[0]

                            # File formats that need special handling for schema detection
                            if ext.lower() in ["txt", "log"]:
                                # For text files, use a standard 'content' column
                                print(
                                    f"  📋 Using standard 'content' column for text file '{sample_file}'"
                                )
                                columns = [{"name": "content", "type": "VARCHAR"}]
                                # Add columns to catalog entry
                                catalog[table_name]["columns"] = columns
                                continue

                            print(
                                f"  📎 Sampling file '{sample_file}' to discover schema"
                            )

                            # Download the sample file
                            sample_url = f"{endpoint}/buckets/{bucket_name}/objects/{sample_file}"
                            try:
                                response = requests.get(
                                    sample_url,
                                    auth=HTTPBasicAuth(access_key, secret_key),
                                )

                                if response.status_code == 200:
                                    # Save content to temp file
                                    with tempfile.NamedTemporaryFile(
                                        delete=False, suffix=f".{ext}"
                                    ) as temp_file:
                                        temp_file.write(response.content)
                                        temp_path = temp_file.name

                                    # Schema detection approach depends on available libraries
                                    columns = []

                                    if ext.lower() in [".txt", ".log"]:
                                        # For text files, use a standard 'content' column
                                        print(
                                            f"  📋 Using standard 'content' column for text file '{sample_file}'"
                                        )
                                        columns = [
                                            {"name": "content", "type": "VARCHAR"}
                                        ]
                                    elif DUCKDB_AVAILABLE and format_name in [
                                        "csv",
                                        "parquet",
                                        "json",
                                    ]:
                                        try:
                                            print(
                                                f"  📊 Analyzing schema with DuckDB using in-memory approach"
                                            )
                                            conn = duckdb.connect(":memory:")

                                            # Create an in-memory virtual file to avoid path issues
                                            # This avoids problems with special characters in paths
                                            if format_name == "csv":
                                                # Register the data directly as a virtual table
                                                data_str = response.content.decode(
                                                    "utf-8", errors="replace"
                                                )
                                                conn.execute(
                                                    "CREATE TABLE temp_data AS SELECT * FROM read_csv_auto(?);",
                                                    [data_str],
                                                )
                                                query = "SELECT * FROM temp_data"
                                            elif (
                                                format_name == "parquet"
                                                or format_name == "json"
                                            ):
                                                # For binary formats, we still need a file but can use a simpler path
                                                # Create a file in the current directory with a safe name
                                                safe_temp_path = f"temp_sample_{bucket_name}_{ext}.{ext}"
                                                with open(safe_temp_path, "wb") as f:
                                                    f.write(response.content)

                                                if format_name == "parquet":
                                                    query = f"SELECT * FROM read_parquet('{safe_temp_path}');"
                                                else:  # json
                                                    query = f"SELECT * FROM read_json_auto('{safe_temp_path}');"
                                            else:
                                                # Fallback to CSV for unknown formats using in-memory approach
                                                data_str = response.content.decode(
                                                    "utf-8", errors="replace"
                                                )
                                                conn.execute(
                                                    "CREATE TABLE temp_data AS SELECT * FROM read_csv_auto(?);",
                                                    [data_str],
                                                )
                                                query = "SELECT * FROM temp_data"

                                            # Execute the query to get schema info
                                            result = conn.execute(query)
                                            column_info = result.description

                                            # Map DuckDB types to SQL types
                                            type_mapping = {
                                                "INTEGER": "INTEGER",
                                                "BIGINT": "BIGINT",
                                                "DOUBLE": "DOUBLE",
                                                "FLOAT": "FLOAT",
                                                "VARCHAR": "VARCHAR",
                                                "DATE": "DATE",
                                                "TIMESTAMP": "TIMESTAMP",
                                                "BOOLEAN": "BOOLEAN",
                                            }

                                            # Create columns list
                                            for col in column_info:
                                                col_name = col[0]
                                                col_type = str(col[1]).upper()

                                                # Map to standard SQL type
                                                mapped_type = "VARCHAR"  # Default type
                                                for (
                                                    db_type,
                                                    sql_type,
                                                ) in type_mapping.items():
                                                    if db_type in col_type:
                                                        mapped_type = sql_type
                                                        break

                                                columns.append(
                                                    {
                                                        "name": col_name,
                                                        "type": mapped_type,
                                                    }
                                                )

                                            # Close connection
                                            conn.close()

                                            # Clean up any safe temp files if they were created
                                            if (
                                                format_name == "parquet"
                                                or format_name == "json"
                                            ):
                                                try:
                                                    if os.path.exists(safe_temp_path):
                                                        os.remove(safe_temp_path)
                                                except Exception as cleanup_error:
                                                    print(
                                                        f"  ⚠️ Error cleaning up temporary file: {cleanup_error}"
                                                    )

                                            print(
                                                f"  ✅ Successfully detected {len(columns)} columns using DuckDB"
                                            )
                                        except Exception as duckdb_error:
                                            print(
                                                f"  ⚠️ DuckDB schema detection failed: {duckdb_error}"
                                            )
                                            # Will fall back to CSV parsing

                                    # Fallback to basic CSV parsing if DuckDB fails or isn't available
                                    if not columns and format_name in ["csv", "txt"]:
                                        try:
                                            print(
                                                f"  📊 Falling back to basic CSV parsing for schema detection"
                                            )
                                            # Decode content as string
                                            content_str = response.content.decode(
                                                "utf-8", errors="replace"
                                            )

                                            # Use CSV reader to parse the first few rows
                                            csv_file = io.StringIO(content_str)
                                            reader = csv.reader(csv_file)

                                            # Get headers from first row
                                            headers = next(reader, [])

                                            # Read a few rows to guess data types
                                            data_rows = []
                                            for _ in range(5):  # Sample 5 rows
                                                try:
                                                    row = next(reader, None)
                                                    if row:
                                                        data_rows.append(row)
                                                except StopIteration:
                                                    break

                                            # Function to guess SQL type from values
                                            def guess_type(values):
                                                # Remove empty values
                                                values = [
                                                    v for v in values if v.strip()
                                                ]
                                                if not values:
                                                    return "VARCHAR"

                                                # Try to convert to numbers
                                                try:
                                                    if all(v.isdigit() for v in values):
                                                        return "INTEGER"

                                                    # Try float conversion
                                                    if all(
                                                        v.replace(".", "", 1).isdigit()
                                                        for v in values
                                                        if v
                                                    ):
                                                        return "DOUBLE"
                                                except Exception:
                                                    pass

                                                # Fallback to string
                                                return "VARCHAR"

                                            # Create column definitions
                                            for i, header in enumerate(headers):
                                                # Get values for this column
                                                col_values = [
                                                    row[i]
                                                    for row in data_rows
                                                    if i < len(row)
                                                ]
                                                # Guess the type
                                                col_type = guess_type(col_values)

                                                # Add column definition
                                                columns.append(
                                                    {
                                                        "name": header
                                                        or f"column_{i+1}",
                                                        "type": col_type,
                                                    }
                                                )

                                            print(
                                                f"  ✅ Successfully detected {len(columns)} columns using CSV parser"
                                            )
                                        except Exception as csv_error:
                                            print(
                                                f"  ⚠️ CSV schema detection failed: {csv_error}"
                                            )

                                    # Add columns to catalog entry if we found any
                                    if columns:
                                        catalog[table_name]["columns"] = columns

                                    # Clean up the temp file
                                    try:
                                        os.unlink(temp_path)
                                    except Exception:
                                        pass
                                else:
                                    print(
                                        f"  ⚠️ Failed to download sample file: HTTP {response.status_code}"
                                    )
                            except Exception as download_error:
                                print(
                                    f"  ⚠️ Error downloading sample file: {download_error}"
                                )
                        else:
                            print(f"  ⚠️ No sample files found for schema detection")
                    except Exception as schema_error:
                        print(f"  ⚠️ Error during schema detection: {schema_error}")
                        # Continue without schema - table will still be created

        # Write catalog to file
        with open(output_path, "w") as file:
            yaml.dump(catalog, file, default_flow_style=False)

        print(f"✅ Catalog saved to {output_path}")

        # Also create a backup copy with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{output_path}.{timestamp}.bak"
        try:
            with open(backup_path, "w") as file:
                yaml.dump(catalog, file, default_flow_style=False)
            print(f"✅ Backup catalog saved to {backup_path}")
        except Exception as e:
            print(f"⚠️ Failed to create backup catalog: {e}")

        return True

    except Exception as e:
        print(f"❌ Error discovering OpenS3 content: {str(e)}")
        return False


def main():
    """Main entrypoint"""
    print("🔍 OpenAthena - OpenS3 Auto Discovery Tool")

    # Get configuration from environment variables
    endpoint = os.environ.get("OPENS3_ENDPOINT", "http://localhost:8001")
    access_key = os.environ.get("OPENS3_ACCESS_KEY", "admin")
    secret_key = os.environ.get("OPENS3_SECRET_KEY", "password")
    output_path = os.environ.get("OPENATHENA_CATALOG_PATH", "catalog.yml")

    print(f"📝 Using the following configuration:")
    print(f"  OpenS3 Endpoint: {endpoint}")
    print(f"  Access Key: {access_key}")
    print(f"  Secret Key: {'*' * len(secret_key)}")
    print(f"  Output Path: {output_path}")

    # Run discovery
    success = discover_openS3_content(endpoint, access_key, secret_key, output_path)

    if success:
        print("✅ Catalog generated successfully")

        # Try to reload the OpenAthena catalog
        print("🔄 Attempting to reload OpenAthena catalog...")
        reload_success = reload_openathena_catalog()

        if reload_success:
            print("✅ OpenAthena catalog reloaded successfully")
        else:
            print(
                "⚠️ Failed to reload OpenAthena catalog. Manual reload may be required."
            )
            print(
                "💡 Tip: Try restarting the OpenAthena server or using the GUI reload button"
            )
    else:
        print("❌ Failed to generate catalog")
        sys.exit(1)


if __name__ == "__main__":
    main()
