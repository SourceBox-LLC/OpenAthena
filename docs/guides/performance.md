# OpenAthena Performance Optimization Guide

This guide provides best practices and recommendations for optimizing the performance of OpenAthena when working with data in OpenS3.

## Key Performance Factors

OpenAthena's performance is influenced by several factors:

1. **Data storage format and organization**
2. **Query complexity and optimization**
3. **Server resource allocation**
4. **Network connectivity to OpenS3**
5. **Client-side configuration**

## Data Storage Optimization

### File Formats

Different file formats have significant performance implications:

| Format | Read Performance | Compression | Predicate Pushdown | Recommendation |
|--------|------------------|-------------|-------------------|----------------|
| Parquet | Excellent | Good | Yes | **Recommended** for analytics workloads |
| ORC | Very Good | Good | Yes | Good alternative to Parquet |
| CSV | Poor | Poor | Limited | Use only for simple/small datasets |
| JSON | Poor | Poor | Limited | Use only when flexibility is required |

#### Why Parquet?

Parquet is recommended because it:
- Stores data in a columnar format (only reads columns needed)
- Supports compression at column level
- Includes metadata for efficient filtering
- Supports predicate pushdown (filtering happens before data transfer)

### Data Partitioning

Properly partitioning data in OpenS3 can dramatically improve query performance:

```
s3://bucket/
  ├── table_name/
  │   ├── year=2024/
  │   │   ├── month=01/
  │   │   │   ├── day=01/
  │   │   │   │   ├── data_file_1.parquet
  │   │   │   │   └── data_file_2.parquet
  │   │   │   └── day=02/
  │   │   └── month=02/
  │   └── year=2025/
```

Benefits of partitioning:
- Allows OpenAthena to skip irrelevant partitions
- Reduces data scanned for filtered queries
- Improves parallel processing potential

#### Partitioning Best Practices

1. **Choose partition keys wisely**:
   - Use columns frequently used in WHERE clauses
   - Favor high-cardinality fields (date, region) over low-cardinality ones (boolean flags)
   - Avoid over-partitioning (aim for files at least 100MB in size)

2. **Use Hive-style partitioning**:
   - Format: `key=value` in path components
   - Enables automatic partition pruning

3. **Balance partition size**:
   - Too many small partitions: high overhead
   - Too few large partitions: less filtering benefit

### File Size Optimization

Optimal file sizes balance query parallelism with overhead:

- **Target size**: 100MB - 1GB per file
- **Too small**: High overhead for listing and opening files
- **Too large**: Reduced parallelism and memory pressure

## Query Optimization

### Filter Pushdown

Take advantage of predicate pushdown by filtering early:

```sql
-- Good: Pushes filter to storage layer
SELECT * FROM sales_data 
WHERE order_date BETWEEN '2025-01-01' AND '2025-01-31'
  AND customer_region = 'WEST'
  
-- Avoid: Forces full scan then filters
SELECT * FROM sales_data 
WHERE EXTRACT(MONTH FROM order_date) = 1
  AND EXTRACT(YEAR FROM order_date) = 2025
  AND UPPER(customer_region) = 'WEST'
```

### Column Pruning

Select only needed columns to reduce I/O:

```sql
-- Good: Only reads required columns
SELECT order_id, customer_id, amount 
FROM sales_data

-- Avoid: Reads all columns
SELECT * FROM sales_data
```

### Join Optimization

Optimize joins for better performance:

1. **Join Order Matters**:
   - Join smaller tables first
   - Filter tables before joining

2. **Reduce Join Data Size**:
   - Apply filters before joins
   - Project only necessary columns

```sql
-- Good: Filter first, then join
SELECT c.name, o.order_date, o.amount
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'
  AND o.amount > 100

-- Less efficient: Join first, then filter
SELECT c.name, o.order_date, o.amount
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2025-01-01'
  AND o.amount > 100
```

### Aggregation Optimization

Optimize aggregation queries:

```sql
-- Good: Pre-aggregate in subquery
SELECT customer_region, SUM(daily_total) as region_total
FROM (
  SELECT customer_region, order_date, SUM(amount) as daily_total
  FROM sales_data
  GROUP BY customer_region, order_date
) daily
GROUP BY customer_region

-- Less efficient: Single large aggregation
SELECT customer_region, SUM(amount) as region_total
FROM sales_data
GROUP BY customer_region
```

## Server Resource Configuration

### Memory Allocation

Adjust memory limits based on your workload:

```bash
export OPENATHENA_MEMORY_LIMIT=8GB  # Adjust based on available RAM
```

Guidelines:
- Set to 50-70% of available system RAM
- Reserve more for complex joins or aggregations
- Monitor swapping and OOM errors

### Thread Configuration

Configure threading to match your CPU resources:

```bash
export OPENATHENA_THREADS=8  # Set to number of available CPU cores
```

Guidelines:
- Start with number of physical cores
- For IO-bound workloads, you might increase slightly (1.5x cores)
- For memory-bound workloads, consider reducing

### Caching Settings

Enable and configure caching for frequently accessed data:

```bash
export OPENATHENA_ENABLE_CACHING=true
export OPENATHENA_CACHE_SIZE=2GB  # Adjust based on workload
```

Benefits:
- Reduces repeated reads from OpenS3
- Improves performance for repeated queries
- Speeds up complex queries on the same dataset

## Network Optimization

### Colocation

For best performance, deploy OpenAthena close to your OpenS3 instance:
- Same data center
- Same cloud region
- Same network zone

### Connection Pooling

OpenAthena uses connection pooling to OpenS3. Adjust pool settings for your workload:

```bash
export OPENATHENA_MAX_CONNECTIONS=20  # Default: 10
```

### Compression Settings

Enable compression for network transfers:

```bash
export OPENATHENA_NETWORK_COMPRESSION=true  # Default: true
```

## Docker and Containerization Performance

When running OpenAthena in Docker:

1. **Resource Allocation**:
   ```yaml
   # docker-compose.yml
   services:
     openathena:
       image: openathena
       deploy:
         resources:
           limits:
             cpus: '4'
             memory: 8G
       environment:
         - OPENATHENA_MEMORY_LIMIT=6GB
         - OPENATHENA_THREADS=4
   ```

2. **Volume Performance**:
   - Use bind mounts for catalog files
   - Consider named volumes for database files
   - Avoid excessive I/O in containers

3. **Network Configuration**:
   - Use host networking for local development
   - Use same Docker network for OpenAthena and OpenS3

## Monitoring and Profiling

### Query Profiling

Enable query profiling to identify bottlenecks:

```bash
export OPENATHENA_ENABLE_PROFILING=true
```

Query profile information will be included in query responses:

```json
{
  "data": [...],
  "profile": {
    "execution_time_ms": 1250,
    "scanning_time_ms": 850,
    "bytes_scanned": 1073741824,
    "files_scanned": 42
  }
}
```

### Resource Monitoring

Monitor system resources during query execution:

- CPU utilization
- Memory usage
- Disk I/O
- Network throughput

Tools for monitoring:
- Docker stats
- htop/top
- Prometheus + Grafana (for production)

## Performance Benchmarking

Benchmark your setup to establish baselines:

1. **Simple scan query**:
   ```sql
   SELECT COUNT(*) FROM large_table
   ```

2. **Filtered scan**:
   ```sql
   SELECT COUNT(*) FROM large_table WHERE date_column > '2025-01-01'
   ```

3. **Aggregation**:
   ```sql
   SELECT category, SUM(amount) FROM large_table GROUP BY category
   ```

4. **Join performance**:
   ```sql
   SELECT a.id, a.name, b.value
   FROM table_a a
   JOIN table_b b ON a.id = b.id
   LIMIT 1000
   ```

## Common Performance Pitfalls

1. **Reading too many small files**: Consolidate into larger files
2. **Inefficient file formats**: Use Parquet instead of CSV/JSON
3. **Missing partitioning**: Implement partitioning for large datasets
4. **Inefficient queries**: Optimize filter pushdown and column selection
5. **Insufficient memory**: Increase memory allocation
6. **Network bottlenecks**: Colocate OpenAthena with OpenS3

## Scaling Strategies

As your data grows, consider these scaling strategies:

1. **Vertical Scaling**:
   - Increase memory and CPU
   - Adjust memory limits and thread count
   - Upgrade to more powerful servers

2. **Distributed Processing**:
   - Consider running multiple OpenAthena instances
   - Split workloads between instances
   - Use load balancer for request distribution

3. **Query Splitting**:
   - Break complex queries into multiple steps
   - Use temporary tables for intermediate results
   - Consider MapReduce-style approach for very large datasets

## Next Steps

- [Advanced Query Techniques](../examples/advanced_queries.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [OpenS3 Integration Guide](./opens3_integration.md)
