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

### OpenS3 Credentials

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENS3_ENDPOINT` | OpenS3 server endpoint | `http://localhost:9000` |
| `OPENS3_ACCESS_KEY` | OpenS3 access key | `your-access-key` |
| `OPENS3_SECRET_KEY` | OpenS3 secret key | `your-secret-key` |
| `OPENS3_REGION` | OpenS3 region (if applicable) | `us-east-1` |

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
  endpoint: http://localhost:9000
  access_key: your-access-key
  secret_key: your-secret-key
  region: us-east-1
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
      - OPENS3_ENDPOINT=http://opens3:9000
      - OPENS3_ACCESS_KEY=your-access-key
      - OPENS3_SECRET_KEY=your-secret-key
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
