# OpenAthena

OpenAthena is a lightweight, DuckDB-powered analytics engine designed to work seamlessly with OpenS3. It provides SQL query capabilities over data stored in OpenS3 buckets, similar to how AWS Athena works with S3.

## Overview

OpenAthena combines DuckDB with OpenS3 to provide:
- Fast SQL analytics over files in OpenS3 buckets (Parquet, CSV, JSON, etc.)
- Simple catalog management for your data sources
- REST API for executing queries and retrieving results
- Arrow-based data transfer for optimal performance

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your OpenS3 credentials in `config.py` or through environment variables.

3. Start the API server:
```bash
python open_athena/api.py
```

4. Execute a query:
```bash
curl -X POST http://localhost:8000/sql --data "SELECT * FROM sales_2025 LIMIT 10"
```

## Features

- **Data Catalog**: Simple YAML-based catalog configuration
- **Query Engine**: Powered by DuckDB with direct support for Parquet, CSV, JSON
- **S3 Integration**: Direct integration with OpenS3 via presigned URLs or API keys
- **Arrow Streaming**: Efficient data transfer using Apache Arrow
- **Performance Optimizations**: Caching and parallel query execution

## Documentation

See the `docs/` directory for detailed documentation.

## License

MIT
