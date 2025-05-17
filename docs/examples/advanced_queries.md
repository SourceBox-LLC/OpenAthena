# OpenAthena Advanced Query Examples

This document provides examples of advanced SQL queries and techniques you can use with OpenAthena for sophisticated data analysis of your OpenS3 data.

## Prerequisites

- OpenAthena server running
- Catalog configured with tables pointing to OpenS3 data
- Familiarity with basic SQL concepts
- Some experience with advanced SQL features

## Advanced Aggregation and Analysis

### Percentiles and Distributions

Calculate percentiles to understand distributions:

```sql
SELECT 
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount) as percentile_25,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) as percentile_75,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount) as percentile_95,
  AVG(amount) as mean,
  STDDEV(amount) as standard_deviation
FROM sales_data
```

### Cohort Analysis

Track how different cohorts of customers behave over time:

```sql
WITH first_purchase AS (
  SELECT 
    customer_id,
    date_trunc('month', MIN(order_date)) as cohort_month
  FROM sales_data
  GROUP BY customer_id
),
cohort_data AS (
  SELECT
    fp.cohort_month,
    DATE_DIFF('month', fp.cohort_month, date_trunc('month', s.order_date)) as month_number,
    COUNT(DISTINCT s.customer_id) as active_customers,
    SUM(s.amount) as revenue
  FROM sales_data s
  JOIN first_purchase fp ON s.customer_id = fp.customer_id
  GROUP BY fp.cohort_month, month_number
  ORDER BY fp.cohort_month, month_number
)
SELECT * FROM cohort_data
```

### Rolling Time Windows

Calculate rolling metrics over time periods:

```sql
SELECT 
  order_date,
  amount,
  SUM(amount) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as rolling_7day_revenue,
  AVG(amount) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as rolling_30day_avg_order
FROM sales_data
ORDER BY order_date
```

## Complex Joins and Relations

### Self Joins

Join a table to itself to find relationships within the data:

```sql
-- Find products frequently purchased together
SELECT 
  a.product_id as product_a,
  b.product_id as product_b,
  COUNT(*) as purchase_together_count
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.product_id < b.product_id
GROUP BY product_a, product_b
ORDER BY purchase_together_count DESC
LIMIT 20
```

### Multiple Joins with Aggregation

Combine multiple tables with aggregations:

```sql
SELECT 
  c.category_name,
  r.region_name,
  EXTRACT(year FROM s.order_date) as year,
  EXTRACT(month FROM s.order_date) as month,
  COUNT(DISTINCT s.order_id) as order_count,
  SUM(s.amount) as total_sales
FROM sales_data s
JOIN customers cust ON s.customer_id = cust.id
JOIN regions r ON cust.region_id = r.id
JOIN products p ON s.product_id = p.id
JOIN categories c ON p.category_id = c.id
GROUP BY c.category_name, r.region_name, year, month
ORDER BY c.category_name, r.region_name, year, month
```

## Advanced Window Functions

### Moving Averages

Calculate sophisticated moving averages:

```sql
SELECT 
  order_date,
  daily_revenue,
  AVG(daily_revenue) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as ma_7day,
  AVG(daily_revenue) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
  ) as ma_14day,
  AVG(daily_revenue) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as ma_30day
FROM (
  SELECT 
    date_trunc('day', order_date) as order_date,
    SUM(amount) as daily_revenue
  FROM sales_data
  GROUP BY date_trunc('day', order_date)
) daily
ORDER BY order_date
```

### Ranking and Partitioning

Perform ranking operations within partitions:

```sql
SELECT 
  category_name,
  product_name,
  total_revenue,
  RANK() OVER (PARTITION BY category_name ORDER BY total_revenue DESC) as rank_in_category,
  total_revenue / SUM(total_revenue) OVER (PARTITION BY category_name) as pct_of_category_revenue
FROM (
  SELECT 
    c.category_name,
    p.product_name,
    SUM(s.amount) as total_revenue
  FROM sales_data s
  JOIN products p ON s.product_id = p.id
  JOIN categories c ON p.category_id = c.id
  GROUP BY c.category_name, p.product_name
) product_sales
ORDER BY category_name, rank_in_category
```

## Working with Complex Data Types

### JSON Processing

Extract and process nested JSON data:

```sql
SELECT 
  event_time,
  json_extract_string(event_data, '$.user_id') as user_id,
  json_extract_string(event_data, '$.event_name') as event_name,
  json_extract_string(event_data, '$.properties.page') as page,
  json_extract_string(event_data, '$.properties.source') as source
FROM events
WHERE json_extract_string(event_data, '$.event_name') = 'page_view'
LIMIT 100
```

### Array Operations

Work with array data types:

```sql
SELECT 
  order_id,
  product_ids,
  array_length(product_ids) as num_products,
  array_contains(product_ids, 'PROD-123') as has_product_123
FROM (
  SELECT 
    order_id,
    list(product_id) as product_ids
  FROM order_items
  GROUP BY order_id
) order_products
WHERE array_length(product_ids) > 3
```

## Advanced Table Operations

### Dynamic Pivot Tables

Create dynamic pivot tables:

```sql
-- This requires preparing a dynamic SQL query
-- Here's a simplified version for specific months
SELECT 
  category_name,
  SUM(CASE WHEN month = 1 THEN revenue ELSE 0 END) as jan,
  SUM(CASE WHEN month = 2 THEN revenue ELSE 0 END) as feb,
  SUM(CASE WHEN month = 3 THEN revenue ELSE 0 END) as mar,
  SUM(CASE WHEN month = 4 THEN revenue ELSE 0 END) as apr,
  SUM(CASE WHEN month = 5 THEN revenue ELSE 0 END) as may,
  SUM(CASE WHEN month = 6 THEN revenue ELSE 0 END) as jun
FROM (
  SELECT 
    c.category_name,
    EXTRACT(month FROM s.order_date) as month,
    SUM(s.amount) as revenue
  FROM sales_data s
  JOIN products p ON s.product_id = p.id
  JOIN categories c ON p.category_id = c.id
  WHERE EXTRACT(year FROM s.order_date) = 2025
  GROUP BY c.category_name, month
) monthly_sales
GROUP BY category_name
```

### Recursive CTEs

Use recursive queries for hierarchical data:

```sql
WITH RECURSIVE category_tree AS (
  -- Base case: top-level categories
  SELECT id, name, parent_id, 0 as level, name as path
  FROM categories
  WHERE parent_id IS NULL
  
  UNION ALL
  
  -- Recursive case: child categories
  SELECT 
    c.id, 
    c.name, 
    c.parent_id, 
    ct.level + 1, 
    ct.path || ' > ' || c.name
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree
ORDER BY path
```

## Time Series Analysis

### Year-over-Year Comparison

Compare metrics across different time periods:

```sql
WITH monthly_sales AS (
  SELECT 
    date_trunc('month', order_date) as month,
    EXTRACT(year FROM order_date) as year,
    EXTRACT(month FROM order_date) as month_num,
    SUM(amount) as revenue
  FROM sales_data
  GROUP BY date_trunc('month', order_date), year, month_num
)
SELECT 
  curr.month,
  curr.revenue as current_year_revenue,
  prev.revenue as previous_year_revenue,
  (curr.revenue - prev.revenue) / prev.revenue * 100 as yoy_growth_pct
FROM monthly_sales curr
LEFT JOIN monthly_sales prev ON 
  curr.month_num = prev.month_num AND
  curr.year = prev.year + 1
WHERE curr.year = 2025
ORDER BY curr.month
```

### Detecting Anomalies

Identify outliers in time series data:

```sql
WITH daily_metrics AS (
  SELECT 
    date_trunc('day', event_time) as day,
    COUNT(*) as event_count
  FROM events
  GROUP BY day
),
stats AS (
  SELECT 
    AVG(event_count) as avg_count,
    STDDEV(event_count) as stddev_count
  FROM daily_metrics
)
SELECT 
  dm.day,
  dm.event_count,
  (dm.event_count - stats.avg_count) / stats.stddev_count as z_score
FROM daily_metrics dm, stats
WHERE ABS((dm.event_count - stats.avg_count) / stats.stddev_count) > 3
ORDER BY ABS((dm.event_count - stats.avg_count) / stats.stddev_count) DESC
```

## Performance Tips for Complex Queries

1. **Filter Early**: Apply filters as early as possible in your query to reduce data processing
2. **Use Appropriate JOINs**: Choose the right join type (INNER, LEFT, etc.) based on your needs
3. **Optimize Aggregations**: Pre-aggregate data in subqueries when possible
4. **Limit Columns**: Select only the columns you need rather than using SELECT *
5. **Use CTEs for Readability**: Common Table Expressions make complex queries more readable and maintainable
6. **Consider Query Structure**: Sometimes splitting a complex query into multiple steps is more efficient
7. **Leverage Partitioning**: Take advantage of partitioned data in OpenS3 by using partition filters

## Executing Complex Queries

Due to their complexity, it's recommended to:

1. Save these queries in SQL files
2. Use the OpenAthena CLI for execution:
   ```bash
   # Windows
   .\query.ps1 -File "path/to/complex_query.sql"
   
   # Linux/macOS
   ./query.sh -f "path/to/complex_query.sql"
   ```

3. For programmatic access, use the OpenAthena SDK with appropriate timeout settings:
   ```python
   from openathena_sdk import AthenaClient
   
   client = AthenaClient()
   with open("complex_query.sql", "r") as f:
       query = f.read()
   
   result = client.execute_query(query, timeout=120)  # Extended timeout
   df = result.to_pandas()
   ```

## Next Steps

- [Performance Optimization](../guides/performance.md)
- [Troubleshooting Complex Queries](../guides/troubleshooting.md)
- [Query Best Practices](../guides/query_best_practices.md)
