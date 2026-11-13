-- =====================================================================
-- 01. Monthly Sales Performance & Growth Trends
-- =====================================================================
-- Business Questions:
-- 1. What are the monthly trends in order volume, unique customers, and sales?
-- 2. What is the breakdown between item product revenue and freight revenue?
-- 3. What is the Month-over-Month (MoM) revenue growth rate using LAG()?
-- 4. What is the cumulative running total of revenue over time?
--
-- SQL Concepts Demonstrated:
-- - Common Table Expressions (CTEs) to pre-aggregate items and prevent fan-out
-- - Aggregate functions: COUNT(DISTINCT), SUM(), AVG(), COALESCE()
-- - Window Functions: LAG() for MoM growth, SUM() OVER (...) for running total
-- - CASE expressions to handle the first baseline month gracefully
-- =====================================================================

WITH order_item_totals AS (
    -- Pre-aggregate order items to order grain to prevent Cartesian fan-out
    SELECT
        order_id,
        ROUND(SUM(price), 2) AS item_revenue,
        ROUND(SUM(freight_value), 2) AS freight_revenue,
        ROUND(SUM(total_item_value), 2) AS total_order_value,
        COUNT(order_item_id) AS total_items_count
    FROM fact_order_items
    GROUP BY order_id
),
monthly_metrics AS (
    -- Aggregate orders and pre-aggregated items by year-month
    SELECT
        o.order_purchase_year_month AS year_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
        COALESCE(SUM(i.total_items_count), 0) AS total_items_sold,
        ROUND(COALESCE(SUM(i.item_revenue), 0), 2) AS total_item_revenue,
        ROUND(COALESCE(SUM(i.freight_revenue), 0), 2) AS total_freight_revenue,
        ROUND(COALESCE(SUM(i.total_order_value), 0), 2) AS total_gross_revenue,
        ROUND(COALESCE(SUM(i.item_revenue), 0) * 1.0 / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS avg_order_value
    FROM fact_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_item_totals i ON o.order_id = i.order_id
    GROUP BY o.order_purchase_year_month
)
SELECT
    year_month,
    total_orders,
    unique_customers,
    total_items_sold,
    total_item_revenue,
    total_freight_revenue,
    total_gross_revenue,
    avg_order_value,
    -- Month-over-Month revenue comparison using LAG() window function
    LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) AS prev_month_gross_revenue,
    CASE 
        WHEN LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) IS NULL THEN NULL
        WHEN LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) = 0 THEN NULL
        ELSE ROUND(
            ((total_gross_revenue - LAG(total_gross_revenue, 1) OVER (ORDER BY year_month)) * 100.0) 
            / LAG(total_gross_revenue, 1) OVER (ORDER BY year_month), 
            2
        )
    END AS mom_revenue_growth_pct,
    -- Cumulative running total of gross revenue across all historical months
    ROUND(
        SUM(total_gross_revenue) OVER (
            ORDER BY year_month 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS cumulative_running_revenue
FROM monthly_metrics
ORDER BY year_month;
