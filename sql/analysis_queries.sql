-- ============================================================
-- SuperStore Sales Analytics — Business SQL Queries
-- ============================================================
-- 15+ analytical queries demonstrating key SQL skills:
--   GROUP BY, JOIN, CASE WHEN, CTEs, Subqueries,
--   Window Functions, Ranking, Aggregations, Date Analysis
-- ============================================================


-- ============================================================
-- Query 1: Monthly Sales and Profit
-- Skill: GROUP BY, ORDER BY, Aggregation
-- Purpose: Track revenue and profitability trends over time
-- ============================================================
SELECT
    order_month,
    ROUND(SUM(sales), 2)       AS total_sales,
    ROUND(SUM(profit), 2)      AS total_profit,
    COUNT(DISTINCT order_id)   AS total_orders,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY order_month
ORDER BY order_month;


-- ============================================================
-- Query 2: Sales and Profit by Market
-- Skill: GROUP BY, Aggregation, Formatting
-- Purpose: Compare performance across global markets
-- ============================================================
SELECT
    market,
    ROUND(SUM(sales), 2)       AS total_sales,
    ROUND(SUM(profit), 2)      AS total_profit,
    COUNT(DISTINCT order_id)   AS total_orders,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY market
ORDER BY total_sales DESC;


-- ============================================================
-- Query 3: Profit by Category and Sub-Category
-- Skill: Multi-level GROUP BY, Aggregation
-- Purpose: Identify the most and least profitable product lines
-- ============================================================
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)   AS total_sales,
    ROUND(SUM(profit), 2)  AS total_profit,
    SUM(quantity)           AS total_quantity,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY category, sub_category
ORDER BY category, total_profit DESC;


-- ============================================================
-- Query 4: Top 10 Products by Revenue
-- Skill: GROUP BY, ORDER BY, LIMIT
-- Purpose: Identify best-selling products for inventory focus
-- ============================================================
SELECT
    product_name,
    category,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    SUM(quantity)          AS total_quantity
FROM orders
GROUP BY product_name, category
ORDER BY total_sales DESC
LIMIT 10;


-- ============================================================
-- Query 5: Top 10 Customers by Sales
-- Skill: GROUP BY, ORDER BY, LIMIT, COUNT DISTINCT
-- Purpose: Identify highest-value customers for relationship mgmt
-- ============================================================
SELECT
    customer_name,
    segment,
    ROUND(SUM(sales), 2)     AS total_sales,
    ROUND(SUM(profit), 2)    AS total_profit,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(AVG(sales), 2)     AS avg_order_line_value
FROM orders
GROUP BY customer_name, segment
ORDER BY total_sales DESC
LIMIT 10;


-- ============================================================
-- Query 6: Profit Margin by Region
-- Skill: Calculated fields, GROUP BY, HAVING
-- Purpose: Find regions with healthy vs. struggling margins
-- ============================================================
SELECT
    market,
    region,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct,
    CASE
        WHEN SUM(profit) / NULLIF(SUM(sales), 0) * 100 > 15 THEN 'Strong'
        WHEN SUM(profit) / NULLIF(SUM(sales), 0) * 100 > 5  THEN 'Moderate'
        WHEN SUM(profit) / NULLIF(SUM(sales), 0) * 100 > 0  THEN 'Weak'
        ELSE 'Loss-Making'
    END AS margin_tier
FROM orders
GROUP BY market, region
ORDER BY profit_margin_pct DESC;


-- ============================================================
-- Query 7: Products Generating Negative Profit (Losses)
-- Skill: HAVING, WHERE, Aggregation on negative values
-- Purpose: Flag products that consistently lose money
-- ============================================================
SELECT
    product_name,
    category,
    sub_category,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_loss,
    SUM(quantity)          AS total_quantity,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM orders
GROUP BY product_name, category, sub_category
HAVING SUM(profit) < 0
ORDER BY total_loss ASC
LIMIT 15;


-- ============================================================
-- Query 8: Month-over-Month Sales Growth using LAG()
-- Skill: Window function — LAG()
-- Purpose: Measure momentum in sales performance
-- ============================================================
SELECT
    order_month,
    total_sales,
    prev_month_sales,
    ROUND(
        (total_sales - prev_month_sales) / NULLIF(prev_month_sales, 0) * 100, 2
    ) AS growth_pct
FROM (
    SELECT
        order_month,
        ROUND(SUM(sales), 2) AS total_sales,
        LAG(ROUND(SUM(sales), 2)) OVER (ORDER BY order_month) AS prev_month_sales
    FROM orders
    GROUP BY order_month
) sub
ORDER BY order_month;


-- ============================================================
-- Query 9: Ranking Markets by Profitability
-- Skill: Window function — RANK(), DENSE_RANK()
-- Purpose: Compare markets by profitability with rankings
-- ============================================================
SELECT
    market,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct,
    RANK() OVER (ORDER BY SUM(profit) DESC)                AS profit_rank,
    DENSE_RANK() OVER (ORDER BY SUM(sales) DESC)           AS sales_rank
FROM orders
GROUP BY market;


-- ============================================================
-- Query 10: Discount Impact on Profitability
-- Skill: CASE WHEN, GROUP BY, Aggregation
-- Purpose: Quantify how discount levels affect profit margins
-- ============================================================
SELECT
    CASE
        WHEN discount = 0            THEN '0% (No Discount)'
        WHEN discount > 0   AND discount <= 0.10 THEN '1-10%'
        WHEN discount > 0.10 AND discount <= 0.20 THEN '11-20%'
        WHEN discount > 0.20 AND discount <= 0.30 THEN '21-30%'
        WHEN discount > 0.30 AND discount <= 0.50 THEN '31-50%'
        ELSE '50%+'
    END AS discount_band,
    COUNT(*) AS order_lines,
    ROUND(SUM(sales), 2)  AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(profit), 2) AS avg_profit_per_line,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY discount_band
ORDER BY
    CASE discount_band
        WHEN '0% (No Discount)' THEN 1
        WHEN '1-10%' THEN 2
        WHEN '11-20%' THEN 3
        WHEN '21-30%' THEN 4
        WHEN '31-50%' THEN 5
        ELSE 6
    END;


-- ============================================================
-- Query 11: Customer Sales Contribution (Pareto Analysis)
-- Skill: Window function — SUM() OVER, Subquery
-- Purpose: Show how top customers contribute to total revenue
-- ============================================================
SELECT
    customer_name,
    total_sales,
    cumulative_sales,
    ROUND(cumulative_sales / grand_total * 100, 2) AS cumulative_pct
FROM (
    SELECT
        customer_name,
        ROUND(SUM(sales), 2) AS total_sales,
        SUM(ROUND(SUM(sales), 2)) OVER (
            ORDER BY SUM(sales) DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_sales,
        (SELECT SUM(sales) FROM orders) AS grand_total
    FROM orders
    GROUP BY customer_name
) sub
ORDER BY total_sales DESC
LIMIT 20;


-- ============================================================
-- Query 12: Sales and Profit by Shipping Mode
-- Skill: GROUP BY, AVG, multiple aggregations
-- Purpose: Evaluate shipping mode performance and cost
-- ============================================================
SELECT
    ship_mode,
    COUNT(DISTINCT order_id)       AS total_orders,
    ROUND(SUM(sales), 2)          AS total_sales,
    ROUND(SUM(profit), 2)         AS total_profit,
    ROUND(AVG(shipping_cost), 2)  AS avg_shipping_cost,
    ROUND(AVG(shipping_days), 1)  AS avg_shipping_days,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
FROM orders
GROUP BY ship_mode
ORDER BY total_sales DESC;


-- ============================================================
-- Query 13: Running Total of Sales by Month
-- Skill: Window function — SUM() OVER (cumulative)
-- Purpose: Show cumulative revenue growth over time
-- ============================================================
SELECT
    order_month,
    ROUND(monthly_sales, 2)  AS monthly_sales,
    ROUND(SUM(monthly_sales) OVER (
        ORDER BY order_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total_sales
FROM (
    SELECT
        order_month,
        SUM(sales) AS monthly_sales
    FROM orders
    GROUP BY order_month
) sub
ORDER BY order_month;


-- ============================================================
-- Query 14: Category Sales Contribution Percentage (CTE)
-- Skill: CTE (Common Table Expression)
-- Purpose: Show each category's share of total revenue
-- ============================================================
WITH category_sales AS (
    SELECT
        category,
        ROUND(SUM(sales), 2)  AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit
    FROM orders
    GROUP BY category
),
grand_total AS (
    SELECT SUM(total_sales) AS overall_sales
    FROM category_sales
)
SELECT
    cs.category,
    cs.total_sales,
    cs.total_profit,
    ROUND(cs.total_sales / gt.overall_sales * 100, 2) AS sales_pct,
    ROUND(cs.total_profit / NULLIF(cs.total_sales, 0) * 100, 2) AS profit_margin_pct
FROM category_sales cs
CROSS JOIN grand_total gt
ORDER BY cs.total_sales DESC;


-- ============================================================
-- Query 15: Regional Performance Comparison (CTE + CASE WHEN)
-- Skill: CTE, CASE WHEN, Aggregation, Classification
-- Purpose: Classify regions by multiple performance dimensions
-- ============================================================
WITH region_metrics AS (
    SELECT
        market,
        region,
        ROUND(SUM(sales), 2)  AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        COUNT(DISTINCT order_id) AS total_orders,
        ROUND(AVG(discount) * 100, 1) AS avg_discount_pct,
        ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct
    FROM orders
    GROUP BY market, region
)
SELECT
    market,
    region,
    total_sales,
    total_profit,
    total_orders,
    avg_discount_pct,
    profit_margin_pct,
    CASE
        WHEN profit_margin_pct > 12 AND total_sales > 200000 THEN '⭐ Star Performer'
        WHEN profit_margin_pct > 8  THEN '✅ Healthy'
        WHEN profit_margin_pct > 0  THEN '⚠️ Needs Attention'
        ELSE '🔴 Loss-Making'
    END AS performance_class
FROM region_metrics
ORDER BY total_sales DESC;


-- ============================================================
-- Query 16: Year-over-Year Growth by Market
-- Skill: Window function — LAG() with PARTITION BY
-- Purpose: Compare each market's annual growth trajectory
-- ============================================================
SELECT
    market,
    year,
    total_sales,
    prev_year_sales,
    ROUND(
        (total_sales - prev_year_sales) / NULLIF(prev_year_sales, 0) * 100, 2
    ) AS yoy_growth_pct
FROM (
    SELECT
        market,
        year,
        ROUND(SUM(sales), 2) AS total_sales,
        LAG(ROUND(SUM(sales), 2)) OVER (
            PARTITION BY market ORDER BY year
        ) AS prev_year_sales
    FROM orders
    GROUP BY market, year
) sub
ORDER BY market, year;


-- ============================================================
-- Query 17: Shipping Efficiency Analysis
-- Skill: CASE WHEN, GROUP BY, AVG
-- Purpose: Identify shipping delays and their impact on profit
-- ============================================================
SELECT
    CASE
        WHEN shipping_days <= 2  THEN '0-2 days (Fast)'
        WHEN shipping_days <= 5  THEN '3-5 days (Standard)'
        WHEN shipping_days <= 7  THEN '6-7 days (Slow)'
        ELSE '8+ days (Very Slow)'
    END AS shipping_speed,
    COUNT(*) AS order_lines,
    ROUND(AVG(sales), 2)          AS avg_sales,
    ROUND(AVG(profit), 2)         AS avg_profit,
    ROUND(AVG(shipping_cost), 2)  AS avg_shipping_cost,
    ROUND(AVG(discount) * 100, 1) AS avg_discount_pct
FROM orders
GROUP BY shipping_speed
ORDER BY
    CASE shipping_speed
        WHEN '0-2 days (Fast)' THEN 1
        WHEN '3-5 days (Standard)' THEN 2
        WHEN '6-7 days (Slow)' THEN 3
        ELSE 4
    END;
