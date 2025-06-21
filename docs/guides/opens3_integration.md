# OpenAthena Integration with OpenS3

This guide provides detailed instructions for integrating OpenAthena with OpenS3, allowing you to run SQL analytics on data stored in your OpenS3 buckets.

## Overview

OpenAthena and OpenS3 are designed to work seamlessly together:

- **OpenS3** serves as your data lake storage system
- **OpenAthena** provides SQL analytics capabilities on that data

The current integration uses a Local File Proxy that downloads files from OpenS3 to a temporary directory before querying. This approach bridges compatibility gaps between DuckDB 1.2.2 and OpenS3's API.

## Prerequisites

- Running OpenS3 server
- OpenS3 access and secret keys
- OpenAthena installed and configured
- Data stored in OpenS3 buckets (preferably in Parquet or CSV format)

## Connection Configuration

### Local Development Considerations

When running both OpenAthena and OpenS3 locally, be aware of potential port conflicts:

- **OpenAthena** defaults to port 8000
- **OpenS3** typically runs on port 8001 (to avoid conflicts)

To run both services without conflicts:

```bash
# Start OpenS3 on port 8001
python -m open_s3.server --port 8001

# Start OpenAthena on default port 8000
python -m open_athena.main
```

### 1. Configure OpenS3 Credentials

Set the following environment variables to allow OpenAthena to authenticate with OpenS3:

```bash
# Windows CMD
set OPENS3_ACCESS_KEY=admin
set OPENS3_SECRET_KEY=password
set S3_ENDPOINT=http://localhost:8001

# Windows PowerShell
$env:OPENS3_ACCESS_KEY = "admin"
$env:OPENS3_SECRET_KEY = "password"
$env:S3_ENDPOINT = "http://localhost:8001"

# Linux/macOS
export OPENS3_ACCESS_KEY="admin"
export OPENS3_SECRET_KEY="password"
export S3_ENDPOINT="http://localhost:8001"
```

**IMPORTANT**: 
- Use `OPENS3_ACCESS_KEY` and `OPENS3_SECRET_KEY` for credentials (not AWS_* variables)
- Use `S3_ENDPOINT` for the OpenS3 server URL
- These variables must be set before starting the OpenAthena server
- When using Docker, use `host.docker.internal:8001` instead of `localhost:8001`

### 2. Create a Catalog File

Create or update the catalog.yml file that points to your OpenS3 buckets. For each table definition, you can use one of these formats:

```yaml
# catalog.yml
# Method 1: Using bucket, prefix, and format (handled by metadata discovery)
world_pop_csv_meta:
  bucket: world-pop
  prefix: ""
  format: csv

# Method 2: Using direct S3 path with wildcard (processed by proxy)
world_pop_csv:
  query: >-
    SELECT * FROM read_csv_auto('s3://world-pop/*.csv')

# Method 3: Using direct HTTP URL to specific file (processed by proxy)
world_pop_csv_http:
  query: >-
    SELECT * FROM read_csv_auto('http://localhost:8001/buckets/world-pop/objects/WorldPopulation2023.csv')
```

> **Note**: The Local File Proxy will automatically convert S3 and HTTP paths to local file paths during catalog loading and handle path escaping as needed.

### Windows Path Handling

When running OpenAthena on Windows with usernames containing apostrophes (e.g., `S'Bussiso`), special SQL escaping is required. The Local File Proxy handles this automatically, but if you're writing custom queries, follow these rules:

1. Double any apostrophes in paths: `S'Bussiso` becomes `S''Bussiso`
2. Double any backslashes in Windows paths: `\` becomes `\\`

Example of proper Windows path escaping in catalog.yml:

```yaml
custom_csv_query:
  query: >-
    SELECT * FROM read_csv_auto('C:\\Users\\S''Bussiso\\Desktop\\data.csv')
```

If writing queries directly in SQL:

```sql
SELECT * FROM read_csv_auto('C:\\Users\\S''Bussiso\\Desktop\\data.csv');
```

### 3. Start OpenAthena

Use the provided startup script which sets proper environment variables:

```bash
# Windows PowerShell
.\start-openathena.ps1

# Linux/macOS
sh ./start-openathena.sh
```

Or manually with environment variables:

```bash
# Set environment variables first
python -m open_athena.main
```

## Troubleshooting OpenS3 Integration

### Common Issues

#### Empty Query Results

**Symptoms**: Querying OpenS3-backed tables returns no data or empty results.

**Solutions**:
- Verify OpenS3 is running and accessible via `curl http://localhost:8001/`
- Check environment variables are set correctly (`S3_ENDPOINT`, `OPENS3_ACCESS_KEY`, `OPENS3_SECRET_KEY`)
- Ensure the buckets and files specified in your catalog actually exist in OpenS3
- Enable proxy debugging with `export DEBUG_PROXY=true`
- Check OpenAthena logs for credential or endpoint errors

#### SQL Syntax Errors with Windows Paths

**Symptoms**: SQL queries fail with syntax errors when paths contain apostrophes.

**Solutions**:
- Ensure apostrophes in paths are doubled in SQL: `'C:\Users\S''Bussiso\data.csv'`
- Make sure backslashes are doubled in Windows paths: `C:\\Users\\...`
- Use the Local File Proxy which handles this escaping automatically
- Verify catalog entries use the correct function names (`read_parquet` not `read_parquet_auto`)

#### Wildcard Patterns Not Matching Files

**Symptoms**: Wildcard patterns like `*.csv` don't return all expected files.

**Solutions**:
- Check if files are at the bucket root vs. in subdirectories
- Verify the wildcards are correctly formatted (e.g., `s3://bucket/*.csv`)
- Enable proxy debugging to see what files are being matched
- Ensure file extensions match exactly (case-sensitive)

## Testing the Integration

To verify the integration is working:

1. **Ensure OpenS3 is running** with test data:
   
   ```bash
   # Check OpenS3 is running on port 8001 with test data in buckets
   curl http://localhost:8001/buckets
   ```

2. **Validate your catalog configuration**:
   
   Make sure your catalog.yml includes entries for your OpenS3 buckets.

3. **Start OpenAthena with correct environment variables**:
   
   Use the startup script or set variables manually.

4. **Run test queries in the OpenAthena GUI**:

   ```sql
   -- Basic test query
   SELECT * FROM world_pop_csv LIMIT 5;
   
   -- More complex query
   SELECT 
     Country, 
     Population2023, 
     "Density(P/Km²)" 
   FROM world_pop_csv 
   WHERE Population2023 > 100000000 
   ORDER BY Population2023 DESC;
   ```

5. **Troubleshoot if needed**:
   
   Check OpenAthena logs for any errors about proxy downloads or file access.
   
   ```bash
   # Windows PowerShell
   Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body "SELECT * FROM test_bucket LIMIT 10" -ContentType "text/plain"
   
   # Linux/macOS
   curl -X POST "http://localhost:8000/sql" -d "SELECT * FROM test_bucket LIMIT 10"
   ```

## Advanced Integration Features

### Using Presigned URLs

For scenarios where OpenAthena and OpenS3 are in different networks, you can use presigned URLs:

1. Generate a presigned URL from OpenS3
2. Use it directly in your SQL query:

```sql
SELECT * FROM read_parquet('https://your-opens3-server/presigned-url-to-file.parquet')
```

### Handling Different File Formats

OpenAthena supports multiple file formats from OpenS3:

- **Parquet Files**:
  ```sql
  SELECT * FROM read_parquet('s3://bucket/path/file.parquet')
  ```

- **CSV Files**:
  ```sql
  SELECT * FROM read_csv('s3://bucket/path/file.csv')
  ```

- **JSON Files**:
  ```sql
  SELECT * FROM read_json('s3://bucket/path/file.json')
  ```

### Working with Partitioned Data

For data organized in partitions:

```sql
SELECT * 
FROM 's3://analytics/sales/year=2025/month=05/*.parquet'
WHERE amount > 1000
```

## Docker Compose Setup

For a complete integrated environment, use the provided docker-compose.yml:

```bash
docker-compose up -d
```

This will start both OpenAthena and OpenS3 containers configured to work together.

### Testing Without OpenS3 Using Dummy Tables

If you don't have access to an OpenS3 instance or want to test OpenAthena functionality independently, you can use dummy tables:

1. Create a test catalog file with dummy table definitions:

```yaml
# test_catalog.yml
test_table:
  type: "dummy"
  # This is a dummy table that doesn't need OpenS3
```

2. Update your docker-compose.yml to use the test catalog:

```yaml
services:
  openathena:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENATHENA_HOST=0.0.0.0
      - OPENATHENA_PORT=8000
      - OPENATHENA_CATALOG_PATH=/app/test_catalog.yml
      - OPENATHENA_ENABLE_CACHING=true
      - OPENATHENA_THREADS=4
      - OPENATHENA_MEMORY_LIMIT=4GB
      # For local testing with dummy tables
      - OPENATHENA_USE_DUMMY_DATA=true
    volumes:
      - ./test_catalog.yml:/app/test_catalog.yml
```

3. Start the container:

```bash
docker-compose up -d
```

4. Test the dummy table:

```bash
# Windows PowerShell
$query = "SELECT * FROM test_table"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain"

# Linux/macOS
curl -X POST "http://localhost:8000/sql" -d "SELECT * FROM test_table"
```

This approach allows you to test and develop OpenAthena functionality without requiring an OpenS3 instance.

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your OpenS3 access and secret keys
   - Check that the OpenS3 endpoint is correct and accessible

2. **Bucket Not Found**:
   - Confirm the bucket exists in your OpenS3 instance
   - Check for typos in bucket names (case sensitive)

3. **Cannot Read Files**:
   - Verify the file format matches what's defined in the catalog
   - Check if the files in OpenS3 are accessible with the provided credentials

### Diagnostic Steps

1. **Test OpenS3 Connection**:
   ```bash
   # Windows PowerShell
   Invoke-WebRequest -Uri "$env:OPENS3_ENDPOINT/health" -Method GET
   
   # Linux/macOS
   curl -X GET "$OPENS3_ENDPOINT/health"
   ```

2. **List Buckets in OpenS3**:
   ```bash
   # Windows PowerShell
   Invoke-WebRequest -Uri "$env:OPENS3_ENDPOINT" -Method GET -Headers @{"Authorization"="AWS4-HMAC-SHA256 Credential=$env:OPENS3_ACCESS_KEY"}
   
   # Linux/macOS
   curl -X GET "$OPENS3_ENDPOINT" -H "Authorization: AWS4-HMAC-SHA256 Credential=$OPENS3_ACCESS_KEY"
   ```

3. **Enable Debug Logging**:
   Set `OPENATHENA_LOG_LEVEL=DEBUG` to see more detailed connection information

## Performance Considerations

- **Use Parquet Format**: For optimal performance, store data in Parquet format
- **Use Partitioning**: Organize data with logical partitions (e.g., by date)
- **Location Proximity**: Deploy OpenAthena close to OpenS3 to minimize latency
- **Connection Pooling**: OpenAthena maintains connection pools to optimize performance

## Next Steps

- [Advanced Queries](../examples/advanced_queries.md)
- [Performance Optimization](./performance.md)
- [Monitoring](./monitoring.md)
