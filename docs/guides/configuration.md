# OpenAthena Configuration Guide

This guide explains how to configure OpenAthena for optimal performance and integration with OpenS3.

## Configuration Methods

OpenAthena can be configured using:
1. Environment variables
2. Configuration file
3. Command-line arguments

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENATHENA_HOST` | Host to bind the server to | `0.0.0.0` | `127.0.0.1` |
| `OPENATHENA_PORT` | Port to run the server on | `8000` | `9000` |
| `OPENATHENA_CATALOG_PATH` | Path to catalog YAML file | `catalog.yml` | `/path/to/catalog.yml` |
| `OPENATHENA_DB_PATH` | Path to DuckDB database file (optional) | `None` (in-memory) | `openathena.duckdb` |
| `OPENATHENA_THREADS` | Number of threads for DuckDB | `4` | `8` |
| `OPENATHENA_MEMORY_LIMIT` | Memory limit for DuckDB | `4GB` | `8GB` |
| `OPENATHENA_ENABLE_CACHING` | Enable result caching | `true` | `false` |

### OpenS3 Integration and Local File Proxy

| Variable | Description | Required | Example |
|----------|-------------|----------|----------|
| `S3_ENDPOINT` | OpenS3 server endpoint | Yes | `http://localhost:8001` |
| `OPENS3_ACCESS_KEY` | OpenS3 access key | Yes | `admin` |
| `OPENS3_SECRET_KEY` | OpenS3 secret key | Yes | `password` |
| `DEBUG_PROXY` | Enable verbose logging for Local File Proxy | No | `true` |

> **IMPORTANT**: Do NOT use AWS_* environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.) as they may conflict with the OpenS3 integration.

## Configuration File

You can also use a YAML configuration file. Create a file named `config.yml`:

```yaml
database:
  path: openathena.duckdb  # optional
  catalog_path: catalog.yml
  threads: 4
  memory_limit: 4GB
  enable_caching: true

api:
  host: 0.0.0.0
  port: 8000

s3:
  endpoint: http://localhost:8001
  access_key: admin
  secret_key: password
```

Then specify this file when starting the server:

```bash
python -m open_athena.main --config config.yml
```

## Docker Environment Configuration

When using Docker, you can configure OpenAthena by setting environment variables in your `docker-compose.yml` file:

```yaml
services:
  openathena:
    image: openathena
    environment:
      - OPENATHENA_HOST=0.0.0.0
      - OPENATHENA_PORT=8000
      - OPENATHENA_CATALOG_PATH=/app/catalog.yml
      - OPENATHENA_THREADS=4
      - OPENATHENA_MEMORY_LIMIT=4GB
      - S3_ENDPOINT=http://opens3:8001
      - OPENS3_ACCESS_KEY=admin
      - OPENS3_SECRET_KEY=password
```

## Startup Scripts

OpenAthena includes startup scripts for Windows and Linux/macOS that set all required environment variables:

### Windows PowerShell (start-openathena.ps1)

```powershell
# start-openathena.ps1

# OpenS3 connection
$env:OPENS3_ACCESS_KEY = "admin"
$env:OPENS3_SECRET_KEY = "password"
$env:S3_ENDPOINT = "http://localhost:8001"

# OpenAthena configuration
$env:OPENATHENA_PORT = "8000"
$env:OPENATHENA_CATALOG_PATH = "./catalog.yml"
$env:OPENATHENA_THREADS = "4"
$env:OPENATHENA_MEMORY_LIMIT = "4GB"

# Start OpenAthena server
python -m open_athena.main
```

### Linux/macOS (start-openathena.sh)

```bash
#!/bin/bash
# start-openathena.sh

# OpenS3 connection
export OPENS3_ACCESS_KEY="admin"
export OPENS3_SECRET_KEY="password"
export S3_ENDPOINT="http://localhost:8001"

# OpenAthena configuration
export OPENATHENA_PORT=8000
export OPENATHENA_CATALOG_PATH="./catalog.yml"
export OPENATHENA_THREADS=4
export OPENATHENA_MEMORY_LIMIT="4GB"

# Start OpenAthena server
python -m open_athena.main
```

To use these scripts:

```bash
# Windows
.\start-openathena.ps1

# Linux/macOS
chmod +x ./start-openathena.sh
./start-openathena.sh
```

## Performance Tuning

### Memory Management

Set the memory limit based on your available resources:

```bash
export OPENATHENA_MEMORY_LIMIT=8GB
```

For machines with limited memory, reduce this value to prevent excessive memory usage.

### Thread Configuration

Optimize for your CPU's core count:

```bash
export OPENATHENA_THREADS=8  # For an 8-core machine
```

## Local File Proxy Configuration

The Local File Proxy provides compatibility between OpenAthena and OpenS3 by downloading files to a temporary directory before querying:

```bash
# Enable debug output from the Local File Proxy
export DEBUG_PROXY=true

# Specify a custom temporary directory for downloads (optional)
export OPENATHENA_TEMP_DIR="/path/to/temp"
```

See the [Local File Proxy documentation](../local_file_proxy.md) for more details on how it works and how to troubleshoot common issues.

### Caching

Enable caching for frequently accessed data:

```bash
export OPENATHENA_ENABLE_CACHING=true
```

## Security Considerations

- Store credentials securely
- Use environment variables instead of hardcoding in files
- Consider using a secrets manager for production deployments
- Set appropriate file permissions for catalog files

## Next Steps

- [Create a Catalog](./catalog_configuration.md)
- [Integration with OpenS3](./opens3_integration.md)

## Troubleshooting

If your configuration isn't taking effect:

1. Check if variables are being overridden
2. Verify the spelling of environment variables
3. Check that config file path is correct
4. Look for error messages in the logs
