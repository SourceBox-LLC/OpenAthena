# OpenAthena Installation Guide

This guide covers the installation and setup of OpenAthena, the DuckDB-powered analytics engine for OpenS3.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- OpenS3 server (optional but recommended for production use)

## Installation Methods

You can install OpenAthena using one of the following methods:

### Method 1: Direct Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SourceBox-LLC/OpenAthena.git
   cd OpenAthena
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install OpenAthena in development mode:
   ```bash
   pip install -e .
   ```

### Method 2: Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SourceBox-LLC/OpenAthena.git
   cd OpenAthena
   ```

2. Build and run using Docker:
   ```bash
   docker build -t openathena .
   docker run -p 8000:8000 -v $(pwd)/catalog.yml:/app/catalog.yml openathena
   ```

3. Testing with dummy tables (no OpenS3 required):
   ```bash
   # Create a test_catalog.yml file with dummy table definitions
   echo "test_table:\n  type: \"dummy\"" > test_catalog.yml
   
   # Run OpenAthena with the test catalog
   docker run -p 8000:8000 -v $(pwd)/test_catalog.yml:/app/catalog.yml \
     -e OPENATHENA_CATALOG_PATH=/app/catalog.yml \
     -e OPENATHENA_USE_DUMMY_DATA=true \
     openathena
   ```

### Method 3: Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/SourceBox-LLC/OpenAthena.git
   cd OpenAthena
   ```

2. Start using Docker Compose:
   ```bash
   docker-compose up -d
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

## Next Steps

- [Configure OpenAthena](./configuration.md)
- [Create a Catalog](./catalog_configuration.md)
- [Run Your First Query](../examples/basic_queries.md)
- [Connect to OpenS3](./opens3_integration.md)

## Troubleshooting

If you encounter issues during installation:

- Ensure Python version is 3.7+
- Check that all dependencies are installed
- Verify OpenS3 credentials if you're connecting to OpenS3
- Check the logs for detailed error messages

For more help, see the [Troubleshooting Guide](./troubleshooting.md).
