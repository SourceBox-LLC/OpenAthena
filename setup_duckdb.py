#!/usr/bin/env python3
import duckdb
import os

print("Configuring DuckDB for OpenS3 access...")

# Create connection
conn = duckdb.connect(':memory:')

# Install and load httpfs extension
conn.sql("INSTALL httpfs")
conn.sql("LOAD httpfs")

# Set S3 configuration
conn.sql("SET s3_region='us-east-1'")
conn.sql("SET s3_access_key_id='admin'")
conn.sql("SET s3_secret_access_key='password'")
conn.sql("SET s3_endpoint='localhost:8001'")
conn.sql("SET s3_url_style='path'")
conn.sql("SET s3_use_ssl=false")

print("âœ… DuckDB configured for OpenS3 access")

# Test connection
try:
    print("Testing local file access...")
    result = conn.sql(f"SELECT * FROM read_csv_auto('{os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_data', 'local_test.csv').replace("'", "''").replace('\\\\', '\\\\\\\\')}')").fetchdf()
    print(f"âœ… Local file access successful, found {len(result)} rows")
    print(result)
except Exception as e:
    print(f"âŒ Local file access failed: {e}")

print("Setup complete")
