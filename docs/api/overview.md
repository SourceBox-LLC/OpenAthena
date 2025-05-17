# OpenAthena API Reference

This document provides a comprehensive reference for the OpenAthena REST API endpoints.

## API Overview

OpenAthena provides a REST API that allows you to:

- Execute SQL queries against data in OpenS3
- List available tables
- Manage catalog entries
- Check server health status

## Base URL

All API endpoints are relative to the base URL of your OpenAthena server:

```
http://localhost:8000
```

Replace `localhost:8000` with the host and port where your OpenAthena server is running.

## Authentication

Currently, OpenAthena uses basic authentication based on the OpenS3 credentials configuration. No additional authentication is required for the API, but the server must be properly configured with OpenS3 credentials to access data.

## Response Format

Most API responses are returned in JSON format. However, query results can be returned in multiple formats based on the `Accept` header:

- `application/json`: Returns results in JSON format
- `application/csv`: Returns results in CSV format
- `application/vnd.apache.arrow.file`: Returns results in Apache Arrow format

## API Endpoints Reference

### Health Check

#### GET /health

Check if the OpenAthena server is running and healthy.

**Request:**
```bash
# Using curl
curl -X GET "http://localhost:8000/health"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Tables

#### GET /tables

List all available tables in the OpenAthena catalog.

**Request:**
```bash
# Using curl
curl -X GET "http://localhost:8000/tables"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/tables" -Method GET
```

**Response:**
```json
{
  "tables": [
    "sales_data",
    "customer_data",
    "web_logs"
  ]
}
```

### SQL Execution

#### POST /sql

Execute a SQL query against the configured data sources.

**Request:**
```bash
# Using curl
curl -X POST "http://localhost:8000/sql" \
  -H "Content-Type: text/plain" \
  -H "Accept: application/json" \
  -d "SELECT * FROM sales_data LIMIT 10"

# Using PowerShell
$query = "SELECT * FROM sales_data LIMIT 10"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain" -Headers @{"Accept"="application/json"}
```

**Response (JSON format):**
```json
{
  "data": [
    {"id": 1, "product_name": "Laptop", "amount": 1299.99},
    {"id": 2, "product_name": "Monitor", "amount": 399.99},
    ...
  ],
  "schema": {
    "fields": [
      {"name": "id", "type": "int32"},
      {"name": "product_name", "type": "string"},
      {"name": "amount", "type": "float64"}
    ]
  },
  "row_count": 10,
  "execution_time_ms": 152
}
```

**Request (CSV format):**
```bash
# Using curl
curl -X POST "http://localhost:8000/sql" \
  -H "Content-Type: text/plain" \
  -H "Accept: application/csv" \
  -d "SELECT * FROM sales_data LIMIT 10"

# Using PowerShell
$query = "SELECT * FROM sales_data LIMIT 10"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain" -Headers @{"Accept"="application/csv"}
```

**Response (CSV format):**
```
id,product_name,amount
1,Laptop,1299.99
2,Monitor,399.99
...
```

**Request (Arrow format):**
```bash
# Using curl
curl -X POST "http://localhost:8000/sql" \
  -H "Content-Type: text/plain" \
  -H "Accept: application/vnd.apache.arrow.file" \
  -d "SELECT * FROM sales_data LIMIT 10" \
  --output result.arrow

# Using PowerShell
$query = "SELECT * FROM sales_data LIMIT 10"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain" -Headers @{"Accept"="application/vnd.apache.arrow.file"} -OutFile "result.arrow"
```

**Response (Arrow format):**
Binary file in Apache Arrow format.

### Catalog Management

#### GET /catalog

Get the current catalog configuration.

**Request:**
```bash
# Using curl
curl -X GET "http://localhost:8000/catalog"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog" -Method GET
```

**Response:**
```json
{
  "catalog": {
    "sales_data": {
      "bucket": "analytics",
      "prefix": "sales/",
      "format": "parquet"
    },
    "customer_data": {
      "bucket": "customers",
      "prefix": "",
      "format": "parquet"
    }
  }
}
```

#### POST /catalog/reload

Reload the catalog from the catalog file.

**Request:**
```bash
# Using curl
curl -X POST "http://localhost:8000/catalog/reload"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog/reload" -Method POST
```

**Response:**
```json
{
  "status": "success",
  "message": "Catalog reloaded successfully",
  "tables": ["sales_data", "customer_data"]
}
```

#### POST /catalog/tables

Add a new table to the catalog (does not persist to catalog file).

**Request:**
```bash
# Using curl
curl -X POST "http://localhost:8000/catalog/tables?table_name=new_table&bucket=analytics&prefix=new/&file_format=parquet"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog/tables?table_name=new_table&bucket=analytics&prefix=new/&file_format=parquet" -Method POST
```

**Parameters:**
- `table_name`: Name of the table to create
- `bucket`: OpenS3 bucket name
- `prefix`: Prefix (folder path) within the bucket
- `file_format`: Format of the files (parquet, csv, json)

**Response:**
```json
{
  "status": "success",
  "message": "Table new_table added to catalog",
  "table": {
    "name": "new_table",
    "bucket": "analytics",
    "prefix": "new/",
    "format": "parquet"
  }
}
```

#### DELETE /catalog/tables/{table_name}

Remove a table from the catalog (does not persist to catalog file).

**Request:**
```bash
# Using curl
curl -X DELETE "http://localhost:8000/catalog/tables/new_table"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog/tables/new_table" -Method DELETE
```

**Response:**
```json
{
  "status": "success",
  "message": "Table new_table removed from catalog"
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid
- `404 Not Found`: The requested resource was not found
- `500 Internal Server Error`: An error occurred on the server

Error responses include a JSON body with additional information:

```json
{
  "error": "Error executing SQL query",
  "detail": "Table 'non_existent_table' does not exist",
  "status_code": 400
}
```

## Rate Limiting

OpenAthena currently does not implement rate limiting, but production deployments should consider adding a rate limiting layer.

## Versioning

The API is versioned through the base URL. The current version is implicitly v1.

## SDK Support

For programmatic access, consider using the OpenAthena SDK, which provides a convenient wrapper around these API endpoints.

## Further Reading

- [OpenAthena SDK Documentation](../../OpenAthena-SDK/README.md)
- [Example Queries](../examples/basic_queries.md)
- [Advanced API Usage](./advanced_usage.md)
