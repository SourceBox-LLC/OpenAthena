# OpenAthena Server

OpenAthena is a lightweight, DuckDB-powered analytics engine designed to work seamlessly with OpenS3. It provides SQL query capabilities over data stored in OpenS3 buckets, enabling powerful analytics directly on your OpenS3 data lake.

## Architecture

The OpenAthena ecosystem consists of two main components:

1. **OpenAthena Server** (this repository): The analytics engine built on DuckDB that processes queries
2. **OpenAthena SDK**: The client library that applications use to communicate with the server

```
[Client Applications] → [OpenAthena-SDK] → [OpenAthena Server] → [OpenS3]
                                                              ↓
[Client Applications] ← [OpenAthena-SDK] ← [OpenAthena Server]
```

## Overview

OpenAthena combines DuckDB with OpenS3 to provide:
- **Fast SQL Analytics**: Query files in OpenS3 buckets (Parquet, CSV, JSON, etc.)
- **Catalog Management**: Simple YAML-based configuration for your data sources
- **REST API**: Endpoints for executing queries and retrieving results
- **Efficient Data Transfer**: Arrow-based streaming for optimal performance
- **Embeddable Engine**: Small footprint that can run alongside OpenS3
- **Local File Proxy**: Bridges compatibility gaps between DuckDB 1.2.2 and OpenS3's API

## Technical Details

- **Query Engine**: Powered by DuckDB, an embedded analytical database
- **OpenS3 Access**: Uses a Local File Proxy to download files from OpenS3 to a temporary directory before querying
- **Performance**: Leverages DuckDB's columnar format and Parquet push-down optimizations
- **Scalability**: Configurable memory limits and parallelism
- **Windows Support**: Special handling for Windows paths with apostrophes

## Quick Start

### Option 1: Direct Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your OpenS3 credentials through environment variables:
```bash
# Required for OpenS3 access via Local File Proxy
export OPENS3_ACCESS_KEY="your-opens3-access-key"  # Default is often "admin"
export OPENS3_SECRET_KEY="your-opens3-secret-key"  # Default is often "password"
export S3_ENDPOINT="http://your-opens3-server:8001"  # Adjust port as needed

# IMPORTANT: Do NOT use AWS_* environment variables as they may cause conflicts
# with OpenS3 integration
```

Or use the provided startup script which sets these variables automatically:
```bash
# Windows PowerShell
.\start-openathena.ps1

# Linux/macOS
sh ./start-openathena.sh
```

3. Start the server:
```bash
python -m open_athena.main
```

This will start both the SQL engine and API server. The OpenS3 file proxy will initialize automatically and handle OpenS3 file downloads when needed.

### Option 2: Using Docker

1. Build and run using Docker:
```bash
# Build the Docker image
docker build -t openathena .

# Run with your catalog configuration
docker run -p 8000:8000 -v $(pwd)/catalog.yml:/app/catalog.yml \
  -e OPENS3_ACCESS_KEY="your-opens3-access-key" \
  -e OPENS3_SECRET_KEY="your-opens3-secret-key" \
  -e S3_ENDPOINT="http://your-opens3-server:8001" \
  openathena
```

2. Or use Docker Compose for a complete environment:
```bash
# Edit environment variables in docker-compose.yml first
docker-compose up -d
```

### Running Queries

Execute a query using curl or the OpenAthena SDK:
```bash
# Using curl
curl -X POST http://localhost:8000/sql --data "SELECT * FROM sales_2025 LIMIT 10"

# Or using the OpenAthena SDK
pip install openathena-sdk
python -c "from openathena_sdk import AthenaClient; print(AthenaClient().execute_query('SELECT * FROM sales_2025 LIMIT 10').to_pandas())"
```

## Catalog Configuration

OpenAthena uses a simple YAML-based catalog to define tables:

```yaml
# catalog.yml
sales_2025:
  bucket: analytics
  prefix: 2025/
  format: parquet

web_logs:
  bucket: logs
  prefix: apache/
  format: json
```

Each table maps to a location in your OpenS3 buckets.

## Components

- **DuckDB Integration**: `database.py` manages the embedded DuckDB instance
- **Catalog Management**: `catalog.py` handles data source definitions
- **API Server**: `api.py` provides REST endpoints for query execution
- **Configuration**: `config.py` manages settings and environment variables
- **Command-line Interface**: `cli.py` for command-line query execution

## Using with OpenAthena SDK

For the best experience, use the OpenAthena SDK to interact with the server:

```python
from openathena_sdk import AthenaClient

# Connect to OpenAthena server
client = AthenaClient(endpoint="http://localhost:8000")

# Execute a query
result = client.execute_query("SELECT * FROM sales_2025 LIMIT 10")

# Convert to Pandas DataFrame
df = result.to_pandas()
print(df)
```

See the [OpenAthena SDK repository](https://github.com/SourceBox-LLC/OpenAthena-SDK) for more information.

## Deployment Options

- **Standalone Server**: Run as a service on any machine
- **Alongside OpenS3**: Deploy on the same system as your OpenS3 server
- **Docker Container**: Package and deploy in containerized environments

### Docker Support

OpenAthena includes Docker support for easy deployment and testing:

```bash
# Build and run with Docker
docker build -t openathena .
docker run -p 8000:8000 -v $(pwd)/catalog.yml:/app/catalog.yml openathena
```

Or use Docker Compose for a more complete setup:

```bash
# Start both OpenAthena and OpenS3 (if available)
docker-compose up -d
```

### Testing with Dummy Tables

OpenAthena can be tested without an OpenS3 instance using dummy tables. This approach allows development and testing of OpenAthena without requiring an actual OpenS3 connection.

#### Option 1: Using Docker Compose (Recommended)

1. Ensure you have a test catalog with dummy table definitions:

```yaml
# test_catalog.yml
test_table:
  type: "dummy"
```

2. Make sure your docker-compose.yml includes the dummy data environment variable:

```yaml
services:
  openathena:
    # other configuration...
    environment:
      - OPENATHENA_CATALOG_PATH=/app/test_catalog.yml
      - OPENATHENA_USE_DUMMY_DATA=true
    volumes:
      - ./test_catalog.yml:/app/test_catalog.yml
```

3. Start the service:

```bash
# Using bash
docker-compose up -d

# Using PowerShell
docker-compose up -d
```

#### Option 2: Using Docker Run Command

If you prefer to use Docker directly:

```bash
# Using bash
docker run -p 8000:8000 \
  -v $(pwd)/test_catalog.yml:/app/test_catalog.yml \
  -e OPENATHENA_CATALOG_PATH=/app/test_catalog.yml \
  -e OPENATHENA_USE_DUMMY_DATA=true \
  openathena

# Using PowerShell
docker run -p 8000:8000 `
  -v "$(Get-Location)\test_catalog.yml:/app/test_catalog.yml" `
  -e OPENATHENA_CATALOG_PATH=/app/test_catalog.yml `
  -e OPENATHENA_USE_DUMMY_DATA=true `
  openathena
```

#### Testing the API

Once the service is running, you can interact with it:

1. Check available tables:
```bash
# Using curl
curl -X GET http://localhost:8000/tables

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/tables" -Method GET | Select-Object -ExpandProperty Content
```

2. Execute SQL queries:
```bash
# Using curl
curl -X POST http://localhost:8000/sql --data "SELECT * FROM test_table"

# Using PowerShell
$query = "SELECT * FROM test_table"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain" | Select-Object -ExpandProperty Content
```

The dummy tables come with pre-populated sample data that allows you to test the full functionality of OpenAthena without connecting to an actual OpenS3 instance.

## Testing and Health Checks

OpenAthena includes a comprehensive test suite and health check utilities to ensure reliability:

### Automated Testing

```bash
# Install testing dependencies
pip install pytest httpx pytest-cov

# Run all tests
python -m pytest

# Generate coverage report
python -m pytest --cov=open_athena
```

### Health Monitoring

Use the built-in health check tool to monitor OpenAthena instances:

```bash
# Basic health check
python tests/health/run_healthcheck.py

# Advanced options
python tests/health/run_healthcheck.py --format json --url http://your-server:8000
```

The Docker image includes health checks that automatically monitor container health status.

## Documentation

See the `docs/` directory for detailed documentation on:
- API reference
- SQL capabilities and limitations
- Performance tuning
- Advanced configuration
- Testing and monitoring

## License

MIT
