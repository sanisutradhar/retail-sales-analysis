-- Import data/processed/retail_lines.csv into PostgreSQL
-- as a table named retail_lines.
--
-- Expected columns:
-- invoice_no, stock_code, description, quantity,
-- unit_price, invoice_date, customer_id, country


-- 1. Monthly sales, orders, and identified customers.
WITH cleaned_sales AS (
    SELECT
        invoice_no,
        customer_id,
        invoice_date,
        quantity * unit_price AS line_revenue
    FROM retail_lines
    WHERE quantity > 0
      AND unit_price > 0
      AND invoice_no NOT LIKE 'C%'
      AND invoice_date IS NOT NULL
)
SELECT
    DATE_TRUNC('month', invoice_date)::date AS month,
    ROUND(SUM(line_revenue)::numeric, 2) AS revenue,
    COUNT(DISTINCT invoice_no) AS orders,
    COUNT(DISTINCT customer_id) AS identified_customers
FROM cleaned_sales
GROUP BY 1
ORDER BY 1;


-- 2. Top 20 products by revenue.
SELECT
    stock_code,
    MAX(description) AS description,
    ROUND(SUM(quantity * unit_price)::numeric, 2) AS revenue,
    SUM(quantity) AS units_sold
FROM retail_lines
WHERE quantity > 0
  AND unit_price > 0
  AND invoice_no NOT LIKE 'C%'
GROUP BY stock_code
ORDER BY revenue DESC
LIMIT 20;


-- 3. Repeat customers.
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT invoice_no) AS order_count
    FROM retail_lines
    WHERE customer_id IS NOT NULL
      AND quantity > 0
      AND unit_price > 0
      AND invoice_no NOT LIKE 'C%'
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS identified_customers,
    COUNT(*) FILTER (WHERE order_count >= 2) AS repeat_customers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE order_count >= 2)
        / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_customer_percentage
FROM customer_orders;


-- 4. Monthly customer activity by first-purchase cohort.
WITH customer_month AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', invoice_date)::date AS activity_month
    FROM retail_lines
    WHERE customer_id IS NOT NULL
      AND quantity > 0
      AND unit_price > 0
      AND invoice_no NOT LIKE 'C%'
      AND invoice_date IS NOT NULL
    GROUP BY customer_id, DATE_TRUNC('month', invoice_date)::date
),
customer_cohort AS (
    SELECT
        customer_id,
        activity_month,
        MIN(activity_month) OVER (
            PARTITION BY customer_id
        ) AS cohort_month
    FROM customer_month
)
SELECT
    cohort_month,
    activity_month,
    COUNT(DISTINCT customer_id) AS active_customers
FROM customer_cohort
GROUP BY cohort_month, activity_month
ORDER BY cohort_month, activity_month;
