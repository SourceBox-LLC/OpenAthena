# OpenAthena Installation Guide

This guide covers the detailed installation and setup of OpenAthena, a DuckDB-powered analytics engine designed to work seamlessly with OpenS3.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- git (for cloning the repository)
- Virtual environment (strongly recommended)
- OpenS3 server (required for S3 data access)

## Installation Methods

You can install OpenAthena using one of the following methods:

### Method 1: Local Development Installation

#### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/SourceBox-LLC/OpenAthena-server.git
cd OpenAthena-server
```

#### Step 2: Create and Activate a Virtual Environment

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
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

### Method 2: Docker Installation

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

#### Step 4: Testing with Dummy Tables (No OpenS3 Required)

```bash
# Create a test_catalog.yml file with dummy table definitions
echo "test_connection:\n  type: \"dummy\"" > test_catalog.yml

# Run OpenAthena with the test catalog
docker run -p 8000:8000 -v $(pwd)/test_catalog.yml:/app/catalog.yml \
  -e OPENATHENA_CATALOG_PATH=/app/catalog.yml \
  -e OPENATHENA_USE_DUMMY_DATA=true \
  openathena
```

#### Step 5: Container Health Monitoring

The Docker container includes built-in health checks that monitor:
- API responsiveness
- Table availability
- Query execution capability

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' <container_id>

# View detailed health check logs
docker inspect --format='{{json .State.Health}}' <container_id> | jq
```

The health check runs automatically every 30 seconds and will report the container as unhealthy if OpenAthena stops functioning properly.

### Method 3: Docker Compose Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/SourceBox-LLC/OpenAthena-server.git
cd OpenAthena-server
```

#### Step 2: Configure Docker Compose

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

#### Step 3: Start the Services

```bash
# Start both OpenAthena and OpenS3
docker-compose up -d
```

#### Step 4: Verify Services are Running

```bash
# Check that containers are running
docker-compose ps

# Check OpenAthena logs
docker-compose logs openathena
```

3. Testing with Docker Compose and dummy tables:
   ```bash
   # Create a test_catalog.yml file if it doesn't exist
   echo "test_table:\n  type: \"dummy\"" > test_catalog.yml
   
   # Modify docker-compose.yml to use test_catalog.yml
   # Change this line:
   # - OPENATHENA_CATALOG_PATH=/app/catalog.yml
   # To:
   # - OPENATHENA_CATALOG_PATH=/app/test_catalog.yml
   
   # And add this environment variable:
   # - OPENATHENA_USE_DUMMY_DATA=true
   
   # Then run:
   docker-compose up -d
   ```
   
   After the container starts, you can test it with:
   ```bash
   # On Windows PowerShell
   Invoke-WebRequest -Uri "http://localhost:8000/tables" -Method GET
   
   # Check if test_table exists in the response
   $query = "SELECT * FROM test_table"
   Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain"
   ```

4. Health Checks with Docker Compose:

   The OpenAthena container includes integrated health checks that run automatically:
   
   ```bash
   # Check container health status
   docker-compose ps
   
   # Get detailed health status
   docker inspect --format='{{.State.Health.Status}}' openathena-openathena-1
   ```
   
   You can also run the health check manually inside the container:
   
   ```bash
   docker-compose exec openathena python /app/tests/health/run_healthcheck.py
   ```
   
   The health check will validate that:
   - The API is responding correctly
   - Tables are available (including dummy tables)
   - SQL queries can be executed successfully

## Post-Installation

After installing OpenAthena, you need to:

1. Configure OpenS3 credentials (see [Configuration Guide](./configuration.md))
2. Create a catalog file (see [Catalog Configuration](./catalog_configuration.md))
3. Start the server

## Verifying the Installation

To verify that OpenAthena is installed correctly:

1. Start the OpenAthena server:
   ```bash
   python -m open_athena.api
   ```

2. Check the API is running:
   ```bash
   # On Windows PowerShell
   Invoke-WebRequest -Uri http://localhost:8000/ -Method GET

   # On macOS/Linux
   curl http://localhost:8000/
   ```

You should see a response with information about the OpenAthena API.

## OpenS3 Integration

OpenAthena is designed to work seamlessly with OpenS3. Follow these instructions to properly integrate with OpenS3:

### Setting Up OpenS3 Credentials

For OpenAthena to connect to OpenS3, you need to configure the following environment variables:

```bash
# Required for OpenS3 access
export S3_ENDPOINT="http://localhost:8001"         # OpenS3 server endpoint
export OPENS3_ACCESS_KEY="admin"                  # OpenS3 access key
export OPENS3_SECRET_KEY="password"               # OpenS3 secret key
```

> **Important Notes**:
> - OpenS3 must be running for OpenAthena to successfully discover and query data
> - Do NOT use AWS_* environment variables as they may conflict with OpenS3 integration
> - When using Docker, use `host.docker.internal` instead of `localhost` for S3_ENDPOINT

### Local File Proxy

OpenAthena uses a Local File Proxy to bridge compatibility between DuckDB and OpenS3. This proxy:

- Downloads files from OpenS3 to a local temporary directory before querying
- Expands wildcard patterns (e.g., `*.csv`, `*.parquet`) to match multiple files
- Handles proper escaping of Windows paths with apostrophes

The proxy is automatically enabled when OpenS3 environment variables are detected.

## Verifying Installation

### Quick Smoke Test

To verify OpenAthena is working correctly:

```bash
# Check the health endpoint
curl http://localhost:8000/health

# List available tables
curl http://localhost:8000/tables

# Run a simple test query
curl -X POST http://localhost:8000/sql --data "SELECT 'Hello from OpenAthena' AS greeting"
```

### API Documentation

Access the Swagger UI API documentation at:
```
http://localhost:8000/docs
```

### Configuration Options

OpenAthena can be configured using environment variables:

```bash
# Server configuration
export OPENATHENA_PORT=8000            # API server port
export OPENATHENA_HOST=0.0.0.0         # API server host
export OPENATHENA_LOG_LEVEL=INFO       # Logging level (DEBUG, INFO, WARNING, ERROR)

# Catalog management
export OPENATHENA_CATALOG_PATH=/path/to/catalog.yml  # Custom catalog path
export OPENATHENA_USE_DUMMY_DATA=false              # Enable/disable dummy data

# Debugging
export DEBUG_PROXY=true                # Enable local file proxy debugging
```

## Troubleshooting

### Common Issues

#### OpenAthena Won't Start

**Symptoms:** Server fails to start, errors about missing modules or permissions.

**Solutions:**
- Verify Python version is 3.7+ with `python --version`
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

### Logging and Debugging

```bash
# Enable verbose application logging
export OPENATHENA_LOG_LEVEL=DEBUG

# Enable Local File Proxy debugging
export DEBUG_PROXY=true

# View logs in realtime
python -m open_athena.main 2>&1 | tee openathena.log
```

## Next Steps

After successfully installing OpenAthena, you can:

1. [Configure your catalog](./catalog_configuration.md) to define tables and data sources
2. [Explore the API](../api/README.md) to understand available endpoints
3. [Set up OpenS3 integration](./opens3_integration.md) for advanced data lake analytics
4. [Review configuration options](./configuration.md) for customizing your installation

For more help, see the [Troubleshooting Guide](./troubleshooting.md).
