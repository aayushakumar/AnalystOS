# Business Glossary

Canonical metric definitions for the AnalystOS e-commerce dataset. Every SQL-generating agent **must** use these definitions to ensure consistency.

---

## Revenue

**Definition:** Total net revenue from completed orders, calculated as `quantity × unit_price − discount` summed across all line items.

```sql
SELECT SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Always filter `orders.status = 'completed'`. Cancelled and refunded orders are not revenue.
- Use `order_items.unit_price` (price at purchase time), not `products.price` (current catalog price).
- Discount is per line item, not per order.

---

## Average Order Value (AOV)

**Definition:** Mean revenue per completed order.

```sql
SELECT SUM(oi.quantity * oi.unit_price - oi.discount)
       / COUNT(DISTINCT o.order_id) AS aov
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Denominator is `COUNT(DISTINCT order_id)`, not `COUNT(*)` of line items.
- Must be restricted to completed orders.

---

## Conversion Rate

**Definition:** Percentage of sessions that resulted in a purchase.

```sql
SELECT ROUND(100.0 * SUM(CASE WHEN converted THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS conversion_rate_pct
FROM sessions;
```

**Pitfalls:**
- This is session-level conversion, not customer-level.
- A customer with 10 sessions and 1 purchase has a 10% session conversion rate.
- Always specify the time window when reporting.

---

## Churn Rate

**Definition:** Percentage of previously-active customers with no completed order in the trailing 90 days.

```sql
SELECT ROUND(100.0 *
  SUM(CASE WHEN last_order < CURRENT_DATE - INTERVAL '90 days' THEN 1 ELSE 0 END)
  / COUNT(*), 2) AS churn_rate_pct
FROM (
  SELECT customer_id, MAX(order_date) AS last_order
  FROM orders
  WHERE status = 'completed'
  GROUP BY customer_id
);
```

**Pitfalls:**
- The 90-day window is a business convention — always disclose the window chosen.
- Only customers with at least one historical completed order are included.
- Adjust the interval for different reporting cadences.

---

## Retention Rate

**Definition:** Complement of churn rate: percentage of previously-active customers who **did** place a completed order in the trailing 90 days.

```sql
SELECT ROUND(100.0 *
  SUM(CASE WHEN last_order >= CURRENT_DATE - INTERVAL '90 days' THEN 1 ELSE 0 END)
  / COUNT(*), 2) AS retention_rate_pct
FROM (
  SELECT customer_id, MAX(order_date) AS last_order
  FROM orders
  WHERE status = 'completed'
  GROUP BY customer_id
);
```

**Pitfalls:**
- `retention_rate = 100 - churn_rate` by definition. Ensure consistency if reporting both.

---

## Repeat Purchase Rate

**Definition:** Percentage of customers with more than one completed order.

```sql
SELECT ROUND(100.0 *
  SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)
  / COUNT(*), 2) AS repeat_purchase_rate_pct
FROM (
  SELECT customer_id, COUNT(*) AS order_count
  FROM orders
  WHERE status = 'completed'
  GROUP BY customer_id
);
```

**Pitfalls:**
- Denominator includes all customers with at least one completed order, not all registered customers.
- Different from retention rate, which is time-bound.

---

## Gross Margin

**Definition:** Revenue minus cost of goods sold, expressed as a percentage of revenue.

```sql
SELECT ROUND(100.0 *
  (SUM(oi.quantity * oi.unit_price - oi.discount) - SUM(oi.quantity * p.cost))
  / NULLIF(SUM(oi.quantity * oi.unit_price - oi.discount), 0), 2) AS gross_margin_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Uses `products.cost` for COGS — assumes current cost represents historical cost.
- `NULLIF` prevents division-by-zero when revenue is 0.
- Discount reduces the revenue numerator, not the COGS.

---

## Average Revenue Per User (ARPU)

**Definition:** Total revenue divided by the number of distinct customers who made at least one completed order.

```sql
SELECT SUM(oi.quantity * oi.unit_price - oi.discount)
       / COUNT(DISTINCT o.customer_id) AS arpu
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Denominator is customers with completed orders, not total registered customers. Specify which definition you use.
- For total-base ARPU, LEFT JOIN from customers instead.

---

## Month-over-Month (MoM) Growth

**Definition:** Percentage change in a metric (typically revenue) from the previous calendar month.

```sql
WITH monthly AS (
  SELECT DATE_TRUNC('month', o.order_date) AS month,
         SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
  FROM order_items oi
  JOIN orders o ON oi.order_id = o.order_id
  WHERE o.status = 'completed'
  GROUP BY DATE_TRUNC('month', o.order_date)
)
SELECT month,
       revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 2) AS mom_growth_pct
FROM monthly
ORDER BY month;
```

**Pitfalls:**
- Partial months (current month) will show artificially low values. Filter to complete months or disclose.
- `NULLIF` in denominator handles the first month where LAG is NULL.

---

## Customer Acquisition Cost (CAC)

**Definition:** Total marketing spend divided by the number of new customers acquired in the same period.

```sql
SELECT ms.total_spend / NULLIF(nc.new_customers, 0) AS cac
FROM (
  SELECT SUM(amount) AS total_spend
  FROM marketing_spend
  WHERE spend_date BETWEEN '2024-01-01' AND '2024-12-31'
) ms,
(
  SELECT COUNT(*) AS new_customers
  FROM customers
  WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
) nc;
```

**Pitfalls:**
- `marketing_spend` has no direct FK to `customers`. This is an aggregate-level approximation.
- Time periods for spend and acquisition must match exactly.
- Does not attribute spend to specific channels unless grouped by channel.
- New customer counts come from `customers.created_at`, which may not equal the first-order date.
