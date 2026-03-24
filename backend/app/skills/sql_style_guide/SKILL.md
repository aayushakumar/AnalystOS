---
name: sql-style-guide
version: "1.0"
description: SQL style conventions, approved patterns, and anti-patterns for query generation
activation_conditions: [sql_builder, validator]
tags: [sql, style, patterns]
---

# SQL Style Guide

Follow these conventions for every SQL query you generate. The target engine is **DuckDB**.

---

## Approved Patterns

### Explicit JOINs

Always use explicit `JOIN … ON` syntax. Never use comma-separated tables with join conditions in `WHERE`.

```sql
-- GOOD
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id;

-- BAD (implicit join)
SELECT o.order_id, c.name
FROM orders o, customers c
WHERE c.customer_id = o.customer_id;
```

### CTEs for Readability

Break complex logic into named CTEs. Each CTE should do one logical thing.

```sql
WITH daily_revenue AS (
    SELECT date_trunc('day', o.order_date) AS day, SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY 1
),
rolling_avg AS (
    SELECT day, revenue, AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS avg_7d
    FROM daily_revenue
)
SELECT * FROM rolling_avg ORDER BY day;
```

### date_trunc for Time Grouping

Always use `date_trunc('period', column)` for temporal aggregation—never `EXTRACT` or string formatting for grouping.

```sql
-- GOOD
SELECT date_trunc('month', order_date) AS month, COUNT(*) AS orders
FROM orders
GROUP BY 1;

-- BAD
SELECT EXTRACT(YEAR FROM order_date) || '-' || EXTRACT(MONTH FROM order_date) AS month, COUNT(*)
FROM orders
GROUP BY 1;
```

### COALESCE for NULLs

When a value might be NULL and a default makes sense, use `COALESCE`.

```sql
SELECT product_id, COALESCE(discount, 0) AS discount
FROM order_items;
```

### Qualify All Column References

When more than one table is in scope, **always** prefix columns with the table alias.

```sql
SELECT o.order_id, oi.product_id
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id;
```

---

## Anti-Patterns — Never Do These

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| `SELECT *` | Returns unnecessary columns, breaks downstream parsing | List columns explicitly |
| Implicit joins (comma syntax) | Hard to read, easy to produce accidental cartesian joins | Use explicit `JOIN … ON` |
| Missing `WHERE` on date range | Full-table scans and meaningless aggregates | Always scope to a date range unless the user explicitly asks for all-time |
| `HAVING` without `GROUP BY` | Syntax error or misleading semantics | Only use `HAVING` to filter grouped results |
| `ORDER BY` column number in CTEs | Fragile if columns change | Use column names or aliases |
| Nested subqueries > 2 levels | Unreadable, hard to debug | Refactor into CTEs |
| `UNION` without `UNION ALL` | Silently deduplicates, hides data issues | Default to `UNION ALL`; use `UNION` only when dedup is intentional |

---

## DuckDB-Specific Tips

### Date Functions

```sql
-- Truncate to month
date_trunc('month', order_date)

-- Extract parts
EXTRACT(DOW FROM order_date)       -- day of week (0=Sunday)
EXTRACT(EPOCH FROM some_timestamp) -- unix timestamp

-- Format for display
strftime(order_date, '%Y-%m-%d')

-- Date arithmetic
order_date + INTERVAL '30 days'
CURRENT_DATE - INTERVAL '7 days'
```

### Type Casting

```sql
-- Use :: syntax for casts
column_name::FLOAT
column_name::DATE
column_name::VARCHAR
```

### FILTER Clause

DuckDB supports the SQL standard `FILTER` clause—prefer it over `CASE WHEN` inside aggregates.

```sql
-- GOOD (DuckDB)
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders
FROM orders;

-- LESS GOOD
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders
FROM orders;
```

---

## Query Templates

### Aggregation (single metric, grouped)

```sql
SELECT
    <dimension>,
    <aggregate_function>(<measure>) AS <metric_alias>
FROM <table> <alias>
[JOIN <table> <alias> ON …]
WHERE <date_column> BETWEEN :start AND :end
GROUP BY 1
ORDER BY 1;
```

### Period Comparison

```sql
WITH current_period AS (
    SELECT <aggregate> AS value
    FROM <table>
    WHERE <date_column> BETWEEN :current_start AND :current_end
),
previous_period AS (
    SELECT <aggregate> AS value
    FROM <table>
    WHERE <date_column> BETWEEN :prev_start AND :prev_end
)
SELECT
    c.value AS current_value,
    p.value AS previous_value,
    (c.value - p.value) / p.value AS pct_change
FROM current_period c, previous_period p;
```

### Time-Series

```sql
SELECT
    date_trunc(:granularity, <date_column>) AS period,
    <aggregate_function>(<measure>) AS <metric_alias>
FROM <table> <alias>
[JOIN <table> <alias> ON …]
WHERE <date_column> BETWEEN :start AND :end
GROUP BY 1
ORDER BY 1;
```

### Top-N

```sql
SELECT <dimension>, <aggregate> AS value
FROM <table>
WHERE <date_column> BETWEEN :start AND :end
GROUP BY 1
ORDER BY value DESC
LIMIT :n;
```
