import os
import duckdb
import sys

print("🦆 Setting up DuckDB connection...")

# Create a new connection
conn = duckdb.connect(database=":memory:")

# Configure S3 credentials if provided
if len(sys.argv) >= 3:
    s3_access_key = sys.argv[1]
    s3_secret_key = sys.argv[2]
    print(f"⚙️ Configuring S3 with provided credentials...")
    conn.execute("SET s3_region='us-east-1'")
    conn.execute(f"SET s3_access_key_id='{s3_access_key}'")
    conn.execute(f"SET s3_secret_access_key='{s3_secret_key}'")
    conn.execute("SET s3_url_style='path'")
    conn.execute("SET s3_use_ssl=true")
    conn.execute("SET s3_allow_errors=true")

# Test connection
try:
    print("Testing local file access...")
    # Build the path
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "test_data", "local_test.csv"
    )
    # Escape single quotes and backslashes for SQL
    safe_path = csv_path.replace("'", "''").replace("\\", "\\\\")
    # Use the safe path in the SQL query
    sql = f"SELECT * FROM read_csv_auto('{safe_path}')"
    result = conn.sql(sql).fetchdf()
    print(f"✅ Local file access successful, found {len(result)} rows")
    print(result)
except Exception as e:
    print(f"❌ Error with local file access: {e}")

# Test S3 access if credentials were provided
if len(sys.argv) >= 3:
    try:
        print("Testing S3 configuration...")
        config_result = conn.sql(
            "SELECT current_setting('s3_access_key_id') as access_key"
        ).fetchdf()
        print(f"✅ S3 configuration verified: {config_result['access_key'][0][:4]}***")

        # Try listing a bucket if specified
        if len(sys.argv) >= 4:
            bucket = sys.argv[3]
            try:
                print(f"Testing S3 bucket access for '{bucket}'...")
                conn.sql(f"SELECT * FROM s3_list('{bucket}')").fetchdf()
                print(f"✅ S3 bucket '{bucket}' access successful")
            except Exception as e:
                print(f"❌ Error accessing S3 bucket '{bucket}': {e}")
    except Exception as e:
        print(f"❌ Error with S3 configuration: {e}")
