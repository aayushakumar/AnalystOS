---
name: metric-definitions
version: "1.0"
description: Canonical metric definitions for the e-commerce analytics domain
activation_conditions: [planner, sql_builder, analyst]
tags: [metrics, sql, definitions]
---

# Metric Definitions

Use these **canonical definitions** whenever computing metrics. Never invent alternative formulas—if a user asks for one of these metrics by name, use the definition below exactly.

---

## Revenue

**Definition:** Total revenue from completed orders, net of line-item discounts.

```sql
SELECT SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Forgetting `WHERE o.status = 'completed'` inflates revenue with cancelled/pending orders.
- Applying discount at the order level instead of the line-item level.

**Counterexample (wrong):**
```sql
-- WRONG: includes non-completed orders and ignores discount
SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi;
```

---

## AOV (Average Order Value)

**Definition:** Revenue divided by the number of distinct completed orders.

```sql
SELECT
    SUM(oi.quantity * oi.unit_price - oi.discount)
        / COUNT(DISTINCT o.order_id) AS aov
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Using `COUNT(*)` on order_items instead of `COUNT(DISTINCT o.order_id)` — one order has many items.
- Mixing in non-completed orders skews the average downward.

**Counterexample (wrong):**
```sql
-- WRONG: counts line items, not orders
SELECT SUM(oi.quantity * oi.unit_price) / COUNT(*) FROM order_items oi;
```

---

## Conversion Rate

**Definition:** Share of sessions that resulted in a conversion.

```sql
SELECT
    COUNT(DISTINCT CASE WHEN s.converted = true THEN s.session_id END)::FLOAT
        / COUNT(DISTINCT s.session_id) AS conversion_rate
FROM sessions s;
```

**Pitfalls:**
- Counting page-views instead of distinct sessions.
- Not filtering to the relevant date range—overall conversion rate is rarely useful.

**Counterexample (wrong):**
```sql
-- WRONG: counts rows instead of distinct sessions
SELECT SUM(CASE WHEN converted THEN 1 ELSE 0 END)::FLOAT / COUNT(*) FROM sessions;
```

---

## Repeat Purchase Rate

**Definition:** Fraction of purchasing customers who made more than one order.

```sql
WITH customer_orders AS (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    COUNT(*) FILTER (WHERE order_count > 1)::FLOAT
        / COUNT(*) AS repeat_purchase_rate
FROM customer_orders;
```

**Pitfalls:**
- Including customers with zero orders in the denominator.
- Using total orders instead of distinct order IDs (duplicates from joins).

**Counterexample (wrong):**
```sql
-- WRONG: denominator includes all customers, not just purchasers
SELECT COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END)::FLOAT
    / (SELECT COUNT(*) FROM customers);
```

---

## Churn Rate

**Definition:** Customers with no order in the last 90 days divided by all previously active customers.

```sql
WITH last_order AS (
    SELECT customer_id, MAX(order_date) AS last_order_date
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    COUNT(*) FILTER (WHERE last_order_date < CURRENT_DATE - INTERVAL '90 days')::FLOAT
        / COUNT(*) AS churn_rate
FROM last_order;
```

**Pitfalls:**
- Using a fixed calendar date instead of a rolling 90-day window.
- Not restricting to completed orders—cancelled orders shouldn't count as activity.

**Counterexample (wrong):**
```sql
-- WRONG: arbitrary cutoff and includes all order statuses
SELECT COUNT(*) FILTER (WHERE last_order_date < '2024-01-01')::FLOAT
    / (SELECT COUNT(*) FROM customers);
```

---

## Gross Margin

**Definition:** Revenue minus cost of goods sold, expressed as a fraction of revenue.

```sql
SELECT
    (SUM(oi.quantity * oi.unit_price - oi.discount)
     - SUM(p.cost * oi.quantity))
        / SUM(oi.quantity * oi.unit_price - oi.discount) AS gross_margin
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Forgetting to multiply `p.cost` by quantity.
- Including shipping costs in COGS without explicit instruction.

**Counterexample (wrong):**
```sql
-- WRONG: subtracts unit cost without multiplying by quantity
SELECT (SUM(oi.unit_price) - SUM(p.cost)) / SUM(oi.unit_price) FROM order_items oi
JOIN products p ON p.product_id = oi.product_id;
```

---

## ARPU (Average Revenue Per User)

**Definition:** Total revenue divided by the count of distinct customers who placed at least one completed order.

```sql
SELECT
    SUM(oi.quantity * oi.unit_price - oi.discount)
        / COUNT(DISTINCT o.customer_id) AS arpu
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'completed';
```

**Pitfalls:**
- Dividing by *all* registered customers instead of purchasing customers.
- Double-counting customers across time periods when computing period-level ARPU.

---

## CAC (Customer Acquisition Cost)

**Definition:** Total marketing spend divided by the number of newly acquired customers in the same period.

```sql
SELECT
    SUM(ms.amount)
        / COUNT(DISTINCT c.customer_id) AS cac
FROM marketing_spend ms
JOIN customers c
    ON c.first_order_date BETWEEN ms.period_start AND ms.period_end;
```

**Pitfalls:**
- Attributing spend to *all* customers instead of only new acquisitions.
- Misaligning the spend period with the acquisition window.

**Counterexample (wrong):**
```sql
-- WRONG: divides by all customers, not new ones
SELECT SUM(amount) / (SELECT COUNT(*) FROM customers) FROM marketing_spend;
```

---

## MoM Growth (Month-over-Month Revenue Growth)

**Definition:** Percentage change in revenue from the previous calendar month.

```sql
WITH monthly AS (
    SELECT
        date_trunc('month', o.order_date) AS month,
        SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY 1
)
SELECT
    month,
    revenue,
    (revenue - LAG(revenue) OVER (ORDER BY month))
        / LAG(revenue) OVER (ORDER BY month) AS mom_growth
FROM monthly
ORDER BY month;
```

**Pitfalls:**
- Comparing incomplete months (current month vs. full prior month).
- Using `date_part` instead of `date_trunc`, which doesn't group correctly across years.

**Counterexample (wrong):**
```sql
-- WRONG: compares by month number, breaks across year boundaries
SELECT EXTRACT(MONTH FROM order_date) AS m, SUM(total) FROM orders GROUP BY m;
```
