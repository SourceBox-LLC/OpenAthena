# OpenAthena Catalog Configuration

The catalog is a central component of OpenAthena that defines the tables and data sources available for querying. This guide explains how to configure and manage your OpenAthena catalog.

## Catalog Basics

An OpenAthena catalog is a YAML file that maps table names to data locations in OpenS3. Each entry defines:

- A table name that will be used in SQL queries
- The OpenS3 bucket where data is stored
- The prefix (folder path) within the bucket
- The file format of the data

## Catalog File Structure

```yaml
# Basic catalog.yml example
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

## Supported Data Formats

OpenAthena supports the following data formats through DuckDB:

- **Parquet**: Optimized columnar format (recommended for performance)
- **CSV**: Comma-separated values
- **JSON**: JavaScript Object Notation
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

## Catalog File Location

By default, OpenAthena looks for a file named `catalog.yml` in the current directory. You can specify a different location using the `OPENATHENA_CATALOG_PATH` environment variable:

```bash
export OPENATHENA_CATALOG_PATH=/path/to/your/catalog.yml
```

## Advanced Catalog Configuration

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

If your catalog doesn't work as expected:

1. Check that the buckets and prefixes exist in your OpenS3 instance
2. Verify OpenS3 credentials and connection settings
3. Make sure the file format matches the actual data files
4. Check OpenAthena logs for detailed error messages

## Next Steps

- [OpenS3 Integration](./opens3_integration.md)
- [Query Examples](../examples/basic_queries.md)
- [Performance Optimization](./performance.md)
