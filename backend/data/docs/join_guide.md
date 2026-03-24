# Join Guide

Approved join patterns, anti-patterns, and best practices for the AnalystOS e-commerce schema.

---

## Schema Relationship Map

```
customers ──1:N──▶ orders ──1:N──▶ order_items ◀──N:1── products
    │
    └──1:N──▶ sessions

marketing_spend (standalone — no FK to other tables)
```

---

## Approved Join Patterns

### orders → customers

Join orders to customer attributes (segment, region).

```sql
SELECT c.region, COUNT(o.order_id) AS order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.region;
```

- **Key:** `orders.customer_id = customers.customer_id`
- **Cardinality:** Many orders to one customer.
- **When to use:** Any time you need customer attributes alongside order data.

### order_items → orders

Join line items to their parent order for date, status, and channel.

```sql
SELECT o.order_date, SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY o.order_date;
```

- **Key:** `order_items.order_id = orders.order_id`
- **Cardinality:** Many items to one order.
- **When to use:** Revenue calculations, order-level aggregations.

### order_items → products

Join line items to product catalog for category, subcategory, and COGS.

```sql
SELECT p.category, SUM(oi.quantity) AS units_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category;
```

- **Key:** `order_items.product_id = products.product_id`
- **Cardinality:** Many items to one product.
- **When to use:** Category breakdowns, gross margin calculations.

### Full revenue chain: order_items → orders → customers

The canonical three-table join for revenue by customer attributes.

```sql
SELECT c.segment,
       SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY c.segment;
```

- **Always join through `orders`** — never join `order_items` directly to `customers`.

### Full margin chain: order_items → orders → products

```sql
SELECT p.category,
       SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue,
       SUM(oi.quantity * p.cost) AS cogs
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category;
```

### sessions → customers

Join sessions to customer attributes for behavioral segmentation.

```sql
SELECT c.segment,
       ROUND(100.0 * SUM(CASE WHEN s.converted THEN 1 ELSE 0 END) / COUNT(*), 2) AS conv_rate
FROM sessions s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.segment;
```

- **Key:** `sessions.customer_id = customers.customer_id`
- **Cardinality:** Many sessions to one customer.

---

## Anti-Patterns

### 1. Direct order_items → customers join (missing orders)

```sql
-- BAD: no join path exists between order_items and customers
SELECT c.region, SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN customers c ON oi.??? = c.customer_id  -- no FK!
GROUP BY c.region;
```

There is no `customer_id` on `order_items`. You **must** go through `orders`.

### 2. Cartesian join between unrelated tables

```sql
-- BAD: marketing_spend has no FK to orders
SELECT o.order_id, ms.amount
FROM orders o, marketing_spend ms
WHERE o.channel = ms.channel;
```

This creates a many-to-many explosion — every order in a channel matches every spend row in that channel. If you must correlate spend with orders, aggregate each side independently first, then join the aggregates:

```sql
WITH daily_revenue AS (
  SELECT order_date, channel, COUNT(*) AS orders
  FROM orders WHERE status = 'completed'
  GROUP BY order_date, channel
),
daily_spend AS (
  SELECT spend_date, channel, SUM(amount) AS spend
  FROM marketing_spend
  GROUP BY spend_date, channel
)
SELECT r.order_date, r.channel, r.orders, s.spend
FROM daily_revenue r
LEFT JOIN daily_spend s
  ON r.order_date = s.spend_date AND r.channel = s.channel;
```

### 3. Missing status filter on orders

```sql
-- BAD: includes cancelled and refunded orders in revenue
SELECT SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id;
```

Always add `WHERE o.status = 'completed'` for financial metrics.

### 4. Using products.price instead of order_items.unit_price

```sql
-- BAD: products.price is the current price, not the price at purchase
SELECT SUM(oi.quantity * p.price) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id;
```

Use `order_items.unit_price` for historical accuracy.

---

## Best Practices

1. **Always qualify column references** with table aliases when joining two or more tables. Ambiguous column names cause runtime errors and confusion.

2. **Filter early.** Apply `WHERE` conditions on the driving table before joining to reduce intermediate result sizes.

3. **Use explicit JOIN syntax.** Write `JOIN ... ON` instead of comma-separated `FROM` with `WHERE` conditions. Explicit syntax makes join intent clear and prevents accidental cross joins.

4. **Prefer LEFT JOIN when null-tolerance is needed.** For example, use `LEFT JOIN` from `customers` to `orders` when computing metrics that should include customers with zero orders (e.g., lifetime value distributions).

5. **Aggregate before joining unrelated granularities.** When combining `marketing_spend` (daily channel-level) with `orders` (per-order), aggregate each to the same grain first, then join.

6. **Use DATE_TRUNC for time grouping.** Prefer `DATE_TRUNC('month', order_date)` over `EXTRACT(YEAR FROM ...) || '-' || EXTRACT(MONTH FROM ...)` for clean, sortable time buckets.

7. **COUNT(DISTINCT ...) for unique entity counts.** When counting customers across order_items, use `COUNT(DISTINCT o.customer_id)` to avoid inflating counts by the number of line items.
