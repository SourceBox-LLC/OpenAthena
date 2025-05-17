# OpenAthena Troubleshooting Guide

This guide addresses common issues you might encounter when using OpenAthena and provides solutions to resolve them.

## Connection Issues

### Cannot Connect to OpenAthena Server

**Symptoms:**
- "Connection refused" errors
- Unable to reach OpenAthena API endpoints

**Possible Causes and Solutions:**

1. **OpenAthena server not running**
   - Start the server: `python -m open_athena.api`
   - Check logs for startup errors

2. **Incorrect host/port**
   - Verify the host and port in your request
   - Default is `http://localhost:8000`
   - Check if port 8000 is already in use by another application

3. **Firewall blocking connections**
   - Check firewall settings
   - Ensure the port is open if connecting from a different machine

4. **Docker container issues**
   - Verify container is running: `docker ps`
   - Check container logs: `docker logs openathena`
   - Ensure ports are correctly mapped in your `docker run` command or `docker-compose.yml`

## OpenS3 Integration Issues

### Cannot Connect to OpenS3

**Symptoms:**
- Error messages about S3 connection failures
- "Access denied" or "403 Forbidden" errors

**Possible Causes and Solutions:**

1. **Incorrect OpenS3 credentials**
   - Verify `OPENS3_ACCESS_KEY` and `OPENS3_SECRET_KEY` environment variables
   - Check if credentials have been rotated
   - Ensure credentials have appropriate permissions

2. **Incorrect OpenS3 endpoint**
   - Verify `OPENS3_ENDPOINT` environment variable (e.g., `http://localhost:9000`)
   - Ensure OpenS3 server is running and accessible

3. **Network connectivity**
   - Check if OpenS3 is reachable from the OpenAthena server
   - Try running a simple connection test: 
     ```bash
     curl -v $OPENS3_ENDPOINT
     ```

4. **HTTPS/SSL issues**
   - If using HTTPS, ensure proper certificates are configured
   - Try with HTTP if testing locally

### Bucket or Object Not Found

**Symptoms:**
- Errors mentioning "Bucket not found" or "Object does not exist"
- Empty query results despite expecting data

**Possible Causes and Solutions:**

1. **Catalog configuration errors**
   - Verify bucket names in `catalog.yml` (they are case-sensitive)
   - Check prefix paths for typos
   - Ensure the bucket exists in your OpenS3 instance

2. **Missing data**
   - Verify files exist at the specified location in OpenS3
   - Check that file formats match what's defined in the catalog

3. **Permission issues**
   - Ensure OpenS3 user has access to the bucket and objects

## Query Execution Issues

### SQL Query Errors

**Symptoms:**
- SQL syntax errors
- "Table not found" errors
- Type mismatch errors

**Possible Causes and Solutions:**

1. **Table not defined in catalog**
   - Verify table exists in catalog.yml
   - Check spelling matches exactly
   - Reload catalog if changes were made: `curl -X POST "http://localhost:8000/catalog/reload"`

2. **SQL syntax errors**
   - Check query syntax
   - Test simple queries first to isolate issues
   - Use SQL linting tools to validate syntax

3. **Data type mismatches**
   - Ensure your query accounts for the correct data types
   - Use appropriate casting if needed: `CAST(field AS type)`

### Query Performance Issues

**Symptoms:**
- Queries take a long time to execute
- Timeouts or connection drops during large queries

**Possible Causes and Solutions:**

1. **Inefficient queries**
   - Add appropriate filters to reduce data scanned
   - Use LIMIT clause during development
   - Optimize JOINs and subqueries

2. **Resource constraints**
   - Increase memory allocation for OpenAthena
   - Increase number of threads: `export OPENATHENA_THREADS=8`
   - Consider scaling up hardware resources

3. **Large datasets**
   - Consider partitioning data in OpenS3
   - Use file formats that support predicate pushdown (Parquet, ORC)
   - Split complex queries into multiple steps

## Data Format Issues

### CSV Parsing Errors

**Symptoms:**
- Errors about CSV parsing or unexpected delimiters
- Columns not aligning correctly

**Possible Causes and Solutions:**

1. **Non-standard CSV format**
   - Check CSV delimiter (comma, tab, semicolon)
   - Verify if headers are present
   - Check for quote characters around fields

2. **Character encoding issues**
   - Ensure CSV files use UTF-8 encoding
   - Handle special characters appropriately

3. **Fix using format options**
   ```sql
   SELECT * FROM read_csv('s3://bucket/path/file.csv', 
     delim=',', header=true, quote='"')
   ```

### Parquet/JSON Format Issues

**Symptoms:**
- "Failed to open Parquet file" errors
- "Invalid JSON" or JSON parsing errors

**Possible Causes and Solutions:**

1. **Incompatible Parquet version**
   - Check Parquet file version compatibility
   - Try regenerating the files with a compatible writer

2. **Invalid JSON structure**
   - Validate JSON files for correct format
   - Ensure JSON files are properly formatted

3. **Schema evolution issues**
   - Handle schema changes properly
   - Consider more flexible options for evolving schemas

## Docker and Container Issues

### Docker Container Won't Start

**Symptoms:**
- Docker container exits immediately after starting
- Error messages in Docker logs

**Possible Causes and Solutions:**

1. **Missing environment variables**
   - Ensure all required environment variables are set
   - Check if catalog file is accessible

2. **Port conflicts**
   - Check if port 8000 is already in use
   - Change the mapped port in Docker run command or docker-compose.yml

3. **Volume mounting issues**
   - Verify paths in volume mounts
   - Ensure catalog.yml exists at the specified path

### Docker Compose Integration Issues

**Symptoms:**
- Services can't communicate with each other
- Network connectivity issues between containers

**Possible Causes and Solutions:**

1. **Network configuration**
   - Ensure services are on the same Docker network
   - Use service names for communication between containers

2. **Service dependency order**
   - Use `depends_on` in docker-compose.yml to ensure correct startup order
   - Add health checks to verify services are ready

3. **Container name conflicts**
   - Ensure container names are unique
   - Remove old containers if necessary

## Diagnostic Tools and Techniques

### Enabling Debug Logging

Increase log verbosity to get more detailed information:

```bash
# Enable debug logging
export OPENATHENA_LOG_LEVEL=DEBUG
python -m open_athena.api
```

### Testing Database Connection

Test DuckDB directly:

```python
import duckdb

con = duckdb.connect()
# Test creating a table
con.execute("CREATE TABLE test (id INTEGER, name VARCHAR)")
con.execute("INSERT INTO test VALUES (1, 'test')")
result = con.execute("SELECT * FROM test").fetchall()
print(result)
```

### Testing OpenS3 Connectivity

Use a simple script to verify OpenS3 connectivity:

```python
import requests
import os

endpoint = os.environ.get('OPENS3_ENDPOINT', 'http://localhost:9000')
access_key = os.environ.get('OPENS3_ACCESS_KEY')
secret_key = os.environ.get('OPENS3_SECRET_KEY')

# Try a simple health check
try:
    response = requests.get(f"{endpoint}/health")
    print(f"OpenS3 health check: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error connecting to OpenS3: {e}")
```

## Collecting Information for Support

If you need to report an issue, gather the following information:

1. **Version Information**
   - OpenAthena version
   - Python version
   - DuckDB version
   - Operating system

2. **Configuration**
   - Catalog file (with sensitive information redacted)
   - Environment variables (with credentials redacted)
   - Docker configuration if applicable

3. **Logs**
   - OpenAthena server logs
   - Error messages
   - Docker logs if using containers

4. **Query Information**
   - The SQL query that failed
   - Expected vs. actual results
   - Approximate data size

## Common Error Messages and Solutions

| Error Message | Possible Cause | Solution |
|---------------|----------------|----------|
| "Table 'X' does not exist" | Table not defined in catalog | Add table to catalog.yml and reload catalog |
| "Could not connect to S3" | OpenS3 connectivity issue | Check OpenS3 credentials and endpoint |
| "Memory limit exceeded" | Query requires more memory | Increase `OPENATHENA_MEMORY_LIMIT` setting |
| "File format not supported" | Trying to read unsupported format | Use supported format (Parquet, CSV, JSON) |
| "Syntax error in SQL" | Invalid SQL syntax | Check query syntax and correct errors |
| "Permission denied" | Lack of access to files | Check OpenS3 permissions |

## Next Steps

If you're still experiencing issues after trying these troubleshooting steps:

1. Check the [GitHub issues](https://github.com/SourceBox-LLC/OpenAthena/issues) for similar problems
2. Review the [OpenAthena documentation](../README.md) for updates
3. Contact support or file a new issue with detailed information about your problem
