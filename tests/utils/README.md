# OpenAthena Testing Utilities

This directory contains shared utility functions and helpers for OpenAthena tests.

## Available Utilities

### S3 Helpers (`s3_helpers.py`)

Utilities for testing OpenAthena's integration with S3/OpenS3:

- `get_s3_credentials()`: Retrieves S3 credentials from environment variables
- `list_buckets()`: Lists all buckets in an S3/OpenS3 server
- `find_csv_in_bucket()`: Searches for CSV files in a specific bucket
- `download_file()`: Downloads a file from S3/OpenS3 to a temporary location
- `create_safe_path()`: Creates a path that's safe for DuckDB to use
- `cleanup_temp_file()`: Safely deletes temporary files

## Best Practices

When writing tests for OpenAthena, follow these guidelines:

1. **Use shared utilities**: Avoid duplicating code by using the shared utilities in this directory.

2. **Clean up temporary resources**: Always clean up temporary files and resources, even if tests fail.

3. **Handle path issues**: When working with file paths, use `create_safe_path()` to ensure compatibility with DuckDB.

4. **Skip tests appropriately**: Use `pytest.mark.skipif` to skip tests that require external resources (like OpenS3) when those resources aren't available.

5. **Handle credentials safely**: Use the `get_s3_credentials()` function to retrieve credentials from environment variables rather than hardcoding them.

## Testing with OpenS3

For tests that require an OpenS3 server:

1. Set the following environment variables:
   ```
   OPENS3_ENDPOINT=http://localhost:8001
   OPENS3_ACCESS_KEY=admin
   OPENS3_SECRET_KEY=password
   ```

2. Make sure your OpenS3 server has at least one bucket with some test data (preferably CSV or Parquet files).

3. Use the `@pytest.mark.skipif` decorator to skip tests when OpenS3 isn't configured, for example:
   ```python
   @pytest.mark.skipif(
       not os.environ.get("OPENS3_ENDPOINT"),
       reason="OpenS3 endpoint not configured"
   )
   def test_that_needs_opens3():
       # Test code here
   ```

This ensures that tests can be run both with and without an OpenS3 server available.
