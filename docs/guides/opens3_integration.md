# OpenAthena Integration with OpenS3

This guide provides detailed instructions for integrating OpenAthena with OpenS3, allowing you to run SQL analytics on data stored in your OpenS3 buckets.

## Overview

OpenAthena and OpenS3 are designed to work seamlessly together:

- **OpenS3** serves as your data lake storage system
- **OpenAthena** provides SQL analytics capabilities on that data

The integration leverages DuckDB's httpfs extension to read data directly from OpenS3 using the S3 protocol.

## Prerequisites

- Running OpenS3 server
- OpenS3 access and secret keys
- OpenAthena installed and configured
- Data stored in OpenS3 buckets (preferably in Parquet format)

## Connection Configuration

### 1. Configure OpenS3 Credentials

Set the following environment variables to allow OpenAthena to authenticate with OpenS3:

```bash
# Windows PowerShell
$env:OPENS3_ENDPOINT = "http://localhost:9000"
$env:OPENS3_ACCESS_KEY = "your-access-key"
$env:OPENS3_SECRET_KEY = "your-secret-key"

# Linux/macOS
export OPENS3_ENDPOINT="http://localhost:9000"
export OPENS3_ACCESS_KEY="your-access-key"
export OPENS3_SECRET_KEY="your-secret-key"
```

### 2. Create a Catalog File

Create a catalog.yml file that points to your OpenS3 buckets:

```yaml
# catalog.yml
sales_data:
  bucket: analytics
  prefix: sales/
  format: parquet

customer_data:
  bucket: customers
  prefix: ""
  format: parquet
```

### 3. Start OpenAthena

```bash
python -m open_athena.api
```

## Testing the Integration

To verify the integration is working:

1. **Create a test bucket in OpenS3** (if you don't already have data):
   
   Use the OpenS3 web interface or API to create a bucket and upload test files.

2. **Add the bucket to your catalog**:
   
   ```yaml
   test_bucket:
     bucket: test
     prefix: ""
     format: parquet
   ```

3. **Run a test query**:
   
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
