# OpenAthena Server

OpenAthena is a lightweight, DuckDB-powered analytics engine designed to work seamlessly with OpenS3. It provides SQL query capabilities over data stored in OpenS3 buckets, enabling powerful analytics directly on your OpenS3 data lake.

[![GitHub license](https://img.shields.io/github/license/SourceBox-LLC/OpenAthena-server)](https://github.com/SourceBox-LLC/OpenAthena-server/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/powered%20by-DuckDB%201.2.2-yellow)](https://duckdb.org/)

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

## Installation & Setup

### Prerequisites

- Python 3.8 or later
- pip (Python package manager)
- git (for cloning the repository)
- OpenS3 server (running separately)

### Option 1: Local Development Installation

#### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/SourceBox-LLC/OpenAthena-server.git
cd OpenAthena-server
```

#### Step 2: Create and Activate a Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

#### Step 4: Configure OpenS3 Credentials

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

> **IMPORTANT**: Do NOT use AWS_* environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) as they may conflict with OpenS3 integration.

#### Step 5: Start OpenAthena Server

```bash
# Start the server manually
python -m open_athena.main

# Or use the provided startup script
# Windows PowerShell
.\start-openathena.ps1

# Linux/macOS
sh ./start-openathena.sh
```

The server will start on http://localhost:8000 by default. The OpenS3 file proxy will initialize automatically and handle OpenS3 file downloads when needed.

### Option 2: Using Docker

#### Step 1: Clone the Repository

```bash
git clone https://github.com/SourceBox-LLC/OpenAthena-server.git
cd OpenAthena-server
```

#### Step 2: Build the Docker Image

```bash
# Build the Docker image
docker build -t openathena .
```

#### Step 3: Run the Container

```bash
# Run with catalog.yml from the current directory
# Linux/macOS
docker run -p 8000:8000 -v $(pwd)/catalog.yml:/app/catalog.yml \
  -e OPENS3_ACCESS_KEY="admin" \
  -e OPENS3_SECRET_KEY="password" \
  -e S3_ENDPOINT="http://host.docker.internal:8001" \
  openathena

# Windows PowerShell
docker run -p 8000:8000 -v ${PWD}/catalog.yml:/app/catalog.yml `
  -e OPENS3_ACCESS_KEY="admin" `
  -e OPENS3_SECRET_KEY="password" `
  -e S3_ENDPOINT="http://host.docker.internal:8001" `
  openathena
```

> **Note**: When running OpenS3 on your host machine, use `host.docker.internal` instead of `localhost` in the S3_ENDPOINT to access the host machine from inside the Docker container.

### Option 3: Using Docker Compose

#### Step 1: Configure Docker Compose

Create or edit the `docker-compose.yml` file:

```yaml
version: '3'

services:
  openathena:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENS3_ACCESS_KEY=admin
      - OPENS3_SECRET_KEY=password
      - S3_ENDPOINT=http://opens3:8001
    volumes:
      - ./catalog.yml:/app/catalog.yml
    depends_on:
      - opens3

  opens3:
    image: opens3:latest
    ports:
      - "8001:8001"
    environment:
      - OPENS3_ACCESS_KEY=admin
      - OPENS3_SECRET_KEY=password
```

#### Step 2: Start the Services

```bash
# Start both OpenAthena and OpenS3
docker-compose up -d
```

#### Step 3: Verify Services are Running

```bash
# Check that containers are running
docker-compose ps

# Check OpenAthena logs
docker-compose logs openathena
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

OpenAthena uses a YAML-based catalog to define tables that can be queried. There are several ways to configure tables in the catalog:

### Standard OpenS3 Tables

```yaml
# catalog.yml - Standard bucket/prefix/format approach
sales_data:
  bucket: analytics
  prefix: sales/2025/
  format: parquet

web_logs:
  bucket: logs
  prefix: apache/
  format: json

customer_data:
  bucket: customers
  prefix: ""
  format: csv
```

### Direct SQL Query Tables

```yaml
# Direct SQL query definition approach
parquet_table:
  query: >-
    SELECT * FROM read_parquet('path/to/local/file.parquet')

csv_table:
  query: >-
    SELECT * FROM read_csv_auto('path/to/local/file.csv')
```

### HTTP/S3 Path Tables with Local File Proxy

```yaml
# Using HTTP paths to OpenS3 objects
opens3_csv_table:
  query: >-
    SELECT * FROM read_csv_auto('http://localhost:8001/buckets/test-bucket/objects/file.csv')

# Using S3 paths with wildcards
opens3_wildcard_parquet:
  query: >-
    SELECT * FROM read_parquet('s3://my-bucket/*.parquet')
```

### Windows Path Handling

When running on Windows with usernames containing apostrophes (e.g., `S'Bussiso`), special handling is required:

```yaml
# Windows paths with apostrophes must be properly escaped
sql_escape_example:
  query: >-
    -- Apostrophes in file paths must be doubled for SQL escaping
    -- Backslashes must be doubled as well
    SELECT * FROM read_csv_auto('C:\\Users\\S''Bussiso\\path\\to\\file.csv')
```

For more information, see the [Catalog Configuration Guide](./docs/guides/catalog_configuration.md).

## OpenS3 Integration

OpenAthena is designed to work seamlessly with OpenS3 for data analytics. This integration uses a Local File Proxy to bridge compatibility between DuckDB and OpenS3.

### Local File Proxy

The Local File Proxy handles:

- Downloading files from OpenS3 to a local temporary directory before querying
- Expanding wildcard patterns (e.g., `*.csv`, `*.parquet`) to match multiple files
- Converting between S3/HTTP URLs and local file paths
- Properly escaping Windows paths with apostrophes in SQL queries

### Required Environment Variables

```bash
# Required for OpenS3 access
export S3_ENDPOINT="http://localhost:8001"         # OpenS3 server endpoint
export OPENS3_ACCESS_KEY="admin"                  # OpenS3 access key
export OPENS3_SECRET_KEY="password"               # OpenS3 secret key
```

> **Important**: OpenS3 must be running for OpenAthena to successfully discover and query data from S3 buckets.

For more details on the OpenS3 integration, see the [OpenS3 Integration Guide](./docs/guides/opens3_integration.md) and [Local File Proxy documentation](./docs/local_file_proxy.md).

## Components

- **DuckDB Integration**: `database.py` manages the embedded DuckDB instance
- **Catalog Management**: `catalog.py` handles data source definitions
- **API Server**: `api.py` provides REST endpoints for query execution
- **Configuration**: `config.py` manages settings and environment variables
- **Command-line Interface**: `cli.py` for command-line query execution
- **Local File Proxy**: `opens3_file_proxy.py` handles OpenS3 file downloads
- **OpenS3 Authentication**: `s3_auth_middleware.py` manages OpenS3 credentials

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

### Quick Smoke Test

To verify OpenAthena is working correctly:

```bash
# Check server health
curl http://localhost:8000/health

# List available tables
curl http://localhost:8000/tables

# Run a simple test query
curl -X POST http://localhost:8000/sql --data "SELECT 'Hello from OpenAthena' AS greeting"
```

### Testing with Dummy Tables

You can test OpenAthena without an OpenS3 server using dummy tables:

```yaml
# In catalog.yml
test_connection:
  type: "dummy"
```

Then start OpenAthena with the dummy data flag:

```bash
# Linux/macOS
export OPENATHENA_USE_DUMMY_DATA=true
python -m open_athena.main

# Windows PowerShell
$env:OPENATHENA_USE_DUMMY_DATA = "true"
python -m open_athena.main
```

### Testing OpenS3 Integration

Use the included test script to verify OpenS3 connection and data access:

```bash
python -m open_athena.tests.test_opens3_integration
```

This will test:
- OpenS3 credential configuration
- Bucket and object discovery
- File downloading via the Local File Proxy
- SQL query execution on OpenS3-backed data

### Automated Testing

For developers and CI/CD pipelines:

```bash
# Install testing dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest

# Generate coverage report
python -m pytest --cov=open_athena

# Run specific test file
python -m pytest open_athena/tests/test_catalog.py
```

### Health Monitoring

Use the built-in health check endpoints:

```bash
# Check server health via API
curl http://localhost:8000/health

# Run health check script
python tests/health/run_healthcheck.py --url http://localhost:8000
```

The Docker image includes automated health checks that verify server functionality.

## Troubleshooting

### Common Issues

#### OpenAthena Won't Start

**Symptoms:** Server fails to start, errors about missing modules or permissions.

**Solutions:**
- Verify Python version is 3.8+ with `python --version`
- Confirm virtual environment is activated
- Check dependencies are installed with `pip list`
- Ensure port 8000 is not in use by another application

#### Empty Query Results

**Symptoms:** Queries to OpenS3-backed tables return no data or empty results.

**Solutions:**
- Verify OpenS3 is running and accessible
- Check environment variables are correctly set (S3_ENDPOINT, OPENS3_ACCESS_KEY, OPENS3_SECRET_KEY)
- Ensure buckets and files actually exist in OpenS3
- Enable proxy debugging with `export DEBUG_PROXY=true`

#### SQL Syntax Errors

**Symptoms:** Queries fail with syntax errors, especially with Windows paths containing apostrophes.

**Solutions:**
- Double apostrophes in SQL paths: `'C:\Users\S''Bussiso\file.csv'`
- Double backslashes in Windows paths: `C:\\Users\\...`
- Verify catalog entries use the correct function names (`read_parquet` not `read_parquet_auto`)

#### Wildcard Patterns Not Matching

**Symptoms:** S3 wildcard patterns like `*.csv` don't return expected files.

**Solutions:**
- Check if files are at bucket root vs. in subdirectories
- Verify wildcards are correctly formatted (e.g., `s3://bucket/*.csv`)
- Enable proxy debugging to see matched files

### Logging and Debugging

```bash
# Enable verbose application logging
export OPENATHENA_LOG_LEVEL=DEBUG

# Enable Local File Proxy debugging
export DEBUG_PROXY=true

# View logs in realtime
python -m open_athena.main 2>&1 | tee openathena.log
```

## Documentation

See the `docs/` directory for detailed documentation on:
- [OpenS3 Integration](./docs/guides/opens3_integration.md)
- [Local File Proxy](./docs/local_file_proxy.md)
- [Catalog Configuration](./docs/guides/catalog_configuration.md)
- [Environment Configuration](./docs/guides/configuration.md)
- [Installation Guide](./docs/guides/installation.md)
- [API Reference](./docs/api/README.md)

## Contributing

Contributions are welcome! Here's how you can help improve OpenAthena:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and commit: `git commit -m 'Add amazing feature'`
4. Push to your branch: `git push origin feature/amazing-feature`
5. Open a pull request

Please ensure your code follows our coding standards and includes appropriate tests.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/OpenAthena-server.git
cd OpenAthena-server

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Install dependencies including development tools
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests to verify your setup
python -m pytest
```

## Version History

- **1.2.2** - Improved OpenS3 integration with Local File Proxy
- **1.2.1** - Added Windows path handling for apostrophes
- **1.2.0** - Added wildcard pattern matching support
- **1.1.0** - Added OpenS3 integration
- **1.0.0** - Initial release

## License

OpenAthena is released under the MIT License.

## Acknowledgments

- [DuckDB](https://duckdb.org/) - The embedded database that powers OpenAthena
- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used for the API
- [OpenS3](https://github.com/SourceBox-LLC/OpenS3) - The S3-compatible storage server
