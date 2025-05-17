# OpenAthena Server

OpenAthena is a lightweight, DuckDB-powered analytics engine designed to work seamlessly with OpenS3. It provides SQL query capabilities over data stored in OpenS3 buckets, similar to how AWS Athena works with S3 but running locally or on your private infrastructure.

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

## Technical Details

- **Query Engine**: Powered by DuckDB, an embedded analytical database
- **S3 Access**: Uses DuckDB's httpfs extension to read directly from OpenS3
- **Performance**: Leverages DuckDB's columnar format and Parquet push-down optimizations
- **Scalability**: Configurable memory limits and parallelism

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your OpenS3 credentials in `config.py` or through environment variables:
```bash
# Required for direct S3 access
export AWS_ACCESS_KEY_ID="your-opens3-access-key"
export AWS_SECRET_ACCESS_KEY="your-opens3-secret-key"
export S3_ENDPOINT="http://your-opens3-server:9000"
```

3. Start the API server:
```bash
python -m open_athena.api
```

4. Execute a query using curl or the OpenAthena SDK:
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

## Documentation

See the `docs/` directory for detailed documentation on:
- API reference
- SQL capabilities and limitations
- Performance tuning
- Advanced configuration

## License

MIT
