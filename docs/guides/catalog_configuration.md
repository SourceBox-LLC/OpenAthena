# OpenAthena Catalog Configuration

The catalog is a central component of OpenAthena that defines the tables and data sources available for querying. This guide explains how to configure and manage your OpenAthena catalog for both local files and OpenS3 data sources.

## Catalog Basics

An OpenAthena catalog is a YAML file that maps table names to data locations in OpenS3. Each entry defines:

- A table name that will be used in SQL queries
- The OpenS3 bucket where data is stored
- The prefix (folder path) within the bucket
- The file format of the data

## Catalog File Structure

There are several ways to configure tables in the catalog:

### 1. Standard OpenS3 Tables

```yaml
# Basic catalog.yml example using bucket/prefix pattern
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

### 2. Direct SQL Query Tables

```yaml
# Direct SQL query definition examples
parquet_table:
  query: >-
    SELECT * FROM read_parquet('path/to/local/file.parquet')

csv_table:
  query: >-
    SELECT * FROM read_csv_auto('path/to/local/file.csv')
```

### 3. HTTP/S3 Path Tables (with Local File Proxy)

```yaml
# OpenS3 HTTP path examples
opens3_csv_table:
  query: >-
    SELECT * FROM read_csv_auto('http://localhost:8001/buckets/test-bucket/objects/file.csv')

# S3 path with wildcard example
opens3_wildcard_parquet:
  query: >-
    SELECT * FROM read_parquet('s3://my-bucket/*.parquet')
```

### 4. Windows Path Handling

When running OpenAthena on Windows with usernames containing apostrophes (e.g., `S'Bussiso`), special SQL escaping is required:

```yaml
# Windows paths with apostrophes must be properly escaped
windows_path_example:
  query: >-
    SELECT * FROM read_csv_auto('C:\\Users\\S''Bussiso\\Desktop\\data.csv')
```

**Important rules for Windows paths:**
- Double any apostrophes: `S'Bussiso` becomes `S''Bussiso`
- Double any backslashes: `\` becomes `\\`

## Supported Data Formats

OpenAthena supports the following data formats through DuckDB:

- **Parquet**: Optimized columnar format (recommended for performance)
  - Use `read_parquet()` function in queries, NOT `read_parquet_auto()` 
  - Example: `SELECT * FROM read_parquet('s3://bucket/*.parquet')`
- **CSV**: Comma-separated values
  - Use `read_csv_auto()` for automatic schema detection
  - Example: `SELECT * FROM read_csv_auto('s3://bucket/*.csv')`
- **JSON**: JavaScript Object Notation
  - Use `read_json_auto()` for automatic schema detection
  - Example: `SELECT * FROM read_json_auto('s3://bucket/*.json')`
- **ORC**: Optimized Row Columnar format
- **Avro**: Apache Avro format
- **Dummy**: Special format for testing without OpenS3

For best performance, we recommend using Parquet files.

### Dummy Tables for Testing

OpenAthena provides a special table type called "dummy" that can be used for testing without needing access to OpenS3. These tables contain generated test data and are ideal for development and testing:

```yaml
# Example dummy table in catalog.yml
test_table:
  type: "dummy"
  # This will create a simple test table with sample data
```

When OpenAthena encounters a dummy table, it creates a view with predefined data:

```sql
-- The dummy table will contain this data
SELECT 1 as id, 'test' as name, 100.0 as value
UNION ALL
SELECT 2 as id, 'test2' as name, 200.0 as value
UNION ALL
SELECT 3 as id, 'test3' as name, 300.0 as value
```

To use dummy tables, set the environment variable `OPENATHENA_USE_DUMMY_DATA=true` when starting OpenAthena.

## Catalog Management

### Loading the Catalog

OpenAthena loads the catalog from a YAML file specified by the environment variable `OPENATHENA_CATALOG_PATH`. If not provided, it searches for `catalog.yml` in the current working directory.

```bash
# Set custom catalog path (Linux/macOS)
export OPENATHENA_CATALOG_PATH=/path/to/your/custom-catalog.yml

# Set custom catalog path (Windows CMD)
set OPENATHENA_CATALOG_PATH=C:\path\to\custom-catalog.yml

# Set custom catalog path (Windows PowerShell)
$env:OPENATHENA_CATALOG_PATH = "C:\path\to\custom-catalog.yml"
```

### Auto-Discovery of OpenS3 Buckets

When OpenAthena starts or when the catalog is reloaded, it automatically discovers buckets and files in OpenS3 to generate catalog entries. This requires:

1. OpenS3 server running and accessible
2. Proper environment variables set (`S3_ENDPOINT`, `OPENS3_ACCESS_KEY`, `OPENS3_SECRET_KEY`)

The auto-discovery process:
- Scans all buckets in OpenS3
- Identifies file types (CSV, Parquet, etc.)
- Creates catalog entries for each data source found

## Advanced Catalog Configuration

### Wildcard Path Support

OpenAthena supports wildcard patterns for matching multiple files:

```yaml
all_csv_files:
  query: >-
    SELECT * FROM read_csv_auto('s3://my-bucket/*.csv')

all_parquet_by_date:
  query: >-
    SELECT * FROM read_parquet('s3://analytics/sales/2025/06/*.parquet')
```

The Local File Proxy will expand these wildcards by listing all matching objects in the bucket and downloading them for querying.

### Windows Path Handling

When running on Windows with usernames containing apostrophes (e.g., `S'Bussiso`), special handling is required:

```yaml
sql_escape_example:
  query: >-
    -- Note that apostrophes in file paths must be doubled for SQL escaping
    SELECT * FROM read_csv_auto('C:\Users\S''Bussiso\path\to\file.csv')
```

### Partitioning

For large datasets, you can take advantage of partitioning to improve query performance:

```yaml
sales_by_date:
  bucket: analytics
  prefix: sales/
  format: parquet
  # OpenAthena will use partition pruning when possible
  # For example with a query like: WHERE year=2025 AND month=05
```

### Custom Table Options

You can add additional options for specific tables:

```yaml
large_dataset:
  bucket: analytics
  prefix: large-data/
  format: parquet
  options:
    file_row_group_size: 100000
    max_threads: 8
```

## Creating and Managing Catalogs

### Manually Creating a Catalog

1. Create a new YAML file (e.g., `catalog.yml`)
2. Define your tables following the structure above
3. Save the file
4. Specify the path to your catalog when starting OpenAthena

### Using the API to Manage Catalogs

You can also use the OpenAthena API to manage catalog entries:

#### Adding a table

```bash
# Using curl
curl -X POST "http://localhost:8000/catalog/tables?table_name=new_table&bucket=data&prefix=new/&file_format=parquet"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog/tables?table_name=new_table&bucket=data&prefix=new/&file_format=parquet" -Method POST
```

#### Reloading the catalog

```bash
# Using curl
curl -X POST "http://localhost:8000/catalog/reload"

# Using PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/catalog/reload" -Method POST
```

## Testing Your Catalog

To verify your catalog configuration:

1. Start the OpenAthena server
2. List available tables:
   ```bash
   # Using curl
   curl -X GET "http://localhost:8000/tables"

   # Using PowerShell
   Invoke-WebRequest -Uri "http://localhost:8000/tables" -Method GET
   ```
3. Try a simple query:
   ```bash
   # Using curl
   curl -X POST "http://localhost:8000/sql" -d "SELECT * FROM your_table LIMIT 10"

   # Using PowerShell
   Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body "SELECT * FROM your_table LIMIT 10" -ContentType "text/plain"
   ```

## Best Practices

1. **Use descriptive table names** that clearly indicate the data they contain
2. **Organize data in OpenS3** using logical prefixes for easy browsing and partitioning
3. **Use Parquet format** where possible for best performance
4. **Keep catalogs modular** - create separate catalog files for different use cases or departments
5. **Document your catalogs** with comments to help other users understand the data structure

## Troubleshooting

### Common Issues

If a table in your catalog is not showing up or returning errors:

1. **Empty results or no data returned:**
   - Verify OpenS3 is running and accessible
   - Check that environment variables are correctly set (S3_ENDPOINT, OPENS3_ACCESS_KEY, OPENS3_SECRET_KEY)
   - Confirm the bucket and files exist in OpenS3

2. **SQL syntax errors:**
   - Check for apostrophes in Windows paths (must be doubled in SQL: `'` → `''`)
   - For direct SQL queries, ensure backslashes are properly escaped (doubled)
   - Verify function name is correct: use `read_parquet()` not `read_parquet_auto()`

3. **Wildcard pattern not matching files:**
   - Verify the pattern matches actual files in the bucket
   - Check if files are at the root (no prefix) instead of in subdirectories
   - Test the pattern directly using the OpenS3 API

4. **Windows path issues:**
   - Paths with apostrophes need special handling
   - Review the Local File Proxy documentation for details

5. **Other issues:**
   - Check OpenAthena logs for detailed error messages
   - Verify OpenS3 credentials and connection settings
   - Make sure the file format matches the actual data files

## Next Steps

- [OpenS3 Integration](./opens3_integration.md)
- [Query Examples](../examples/basic_queries.md)
- [Performance Optimization](./performance.md)
