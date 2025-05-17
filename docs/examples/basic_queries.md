# OpenAthena Basic Query Examples

This document provides examples of basic SQL queries you can run with OpenAthena against your OpenS3 data.

## Prerequisites

- OpenAthena server running
- Catalog configured with tables pointing to OpenS3 data
- Basic understanding of SQL

## Example Setup

For these examples, we'll assume you have the following catalog configuration:

```yaml
# catalog.yml
sales_data:
  bucket: analytics
  prefix: sales/
  format: parquet

customers:
  bucket: data
  prefix: customers/
  format: parquet

web_logs:
  bucket: logs
  prefix: web/
  format: json
```

## Basic Queries

### Simple SELECT

Retrieve the first 10 rows from a table:

```sql
SELECT * FROM sales_data LIMIT 10
```

### SELECT with Column Selection

Select specific columns:

```sql
SELECT order_id, customer_id, amount 
FROM sales_data 
LIMIT 100
```

### Filtering with WHERE

Filter records based on conditions:

```sql
SELECT * 
FROM sales_data 
WHERE amount > 1000 
  AND order_date >= '2025-01-01'
```

### Sorting with ORDER BY

Sort the results:

```sql
SELECT * 
FROM sales_data 
ORDER BY amount DESC 
LIMIT 20
```

## Aggregation Queries

### COUNT, SUM, AVG

Calculate aggregate statistics:

```sql
SELECT 
  COUNT(*) as total_orders,
  SUM(amount) as total_revenue,
  AVG(amount) as average_order_value
FROM sales_data
```

### GROUP BY

Group data for aggregation:

```sql
SELECT 
  customer_id,
  COUNT(*) as order_count,
  SUM(amount) as total_spent
FROM sales_data
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 10
```

### Time-Based Aggregation

Group by time periods:

```sql
SELECT 
  date_trunc('month', order_date) as month,
  COUNT(*) as order_count,
  SUM(amount) as monthly_revenue
FROM sales_data
GROUP BY month
ORDER BY month
```

## Joining Tables

Join data from multiple tables:

```sql
SELECT 
  s.order_id,
  s.amount,
  c.name as customer_name,
  c.email
FROM sales_data s
JOIN customers c ON s.customer_id = c.id
WHERE s.amount > 500
LIMIT 20
```

## Window Functions

Use window functions for advanced analysis:

```sql
SELECT 
  order_id,
  order_date,
  amount,
  SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date) as customer_running_total
FROM sales_data
LIMIT 100
```

## Filtering JSON Data

Query JSON-formatted data:

```sql
SELECT 
  request_time,
  url_path,
  status_code
FROM web_logs
WHERE status_code >= 400
  AND url_path LIKE '/api/%'
LIMIT 50
```

## Date and Time Functions

Utilize built-in date/time functions:

```sql
SELECT 
  order_id,
  order_date,
  extract('year' from order_date) as year,
  extract('month' from order_date) as month,
  extract('day' from order_date) as day
FROM sales_data
LIMIT 10
```

## String Operations

Perform string manipulations:

```sql
SELECT 
  product_name,
  UPPER(product_name) as upper_name,
  LOWER(product_name) as lower_name,
  LENGTH(product_name) as name_length
FROM sales_data
LIMIT 10
```

## Using Subqueries

Embed queries within queries:

```sql
SELECT customer_id, name, total_spent
FROM customers
JOIN (
  SELECT 
    customer_id, 
    SUM(amount) as total_spent
  FROM sales_data
  GROUP BY customer_id
) sales ON customers.id = sales.customer_id
WHERE total_spent > 10000
ORDER BY total_spent DESC
```

## Common Table Expressions (CTEs)

Use CTEs for more readable queries:

```sql
WITH monthly_sales AS (
  SELECT 
    date_trunc('month', order_date) as month,
    SUM(amount) as revenue
  FROM sales_data
  GROUP BY month
)
SELECT 
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
  revenue - LAG(revenue) OVER (ORDER BY month) as month_over_month_change
FROM monthly_sales
ORDER BY month
```

## Executing Queries

You can execute these queries using:

### HTTP Request

```bash
# Windows PowerShell
$query = "SELECT * FROM sales_data LIMIT 10"
Invoke-WebRequest -Uri "http://localhost:8000/sql" -Method POST -Body $query -ContentType "text/plain"

# Linux/macOS
curl -X POST "http://localhost:8000/sql" -d "SELECT * FROM sales_data LIMIT 10"
```

### OpenAthena CLI

```bash
# Windows
.\query.ps1 -Query "SELECT * FROM sales_data LIMIT 10"

# Linux/macOS
./query.sh "SELECT * FROM sales_data LIMIT 10"
```

### Python with OpenAthena SDK

```python
from openathena_sdk import AthenaClient

client = AthenaClient()
result = client.execute_query("SELECT * FROM sales_data LIMIT 10")
df = result.to_pandas()
print(df)
```

## Next Steps

- [Advanced Queries](./advanced_queries.md)
- [Performance Optimization](../guides/performance.md)
- [Troubleshooting Queries](../guides/troubleshooting.md)
