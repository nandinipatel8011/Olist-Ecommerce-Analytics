-- =====================================================================
-- 02. Product Category Performance & Pareto (80/20) Analysis
-- =====================================================================
-- Business Questions:
-- 1. Which product categories generate the highest total merchandise value?
-- 2. How many units and distinct orders are placed per category?
-- 3. What is the average item sales price per category?
-- 4. Which categories form the vital 80% of revenue (Pareto Principle)?
--
-- SQL Concepts Demonstrated:
-- - INNER JOIN between fact_order_items and dim_products
-- - Aggregations: SUM(), COUNT(), COUNT(DISTINCT), AVG(), ROUND()
-- - Window Functions: DENSE_RANK() for ranking without gaps
-- - Cumulative Window Functions: SUM() OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING...)
-- - Window Ratio: SUM(...) OVER () as the grand total denominator
-- =====================================================================

WITH category_totals AS (
    SELECT
        COALESCE(p.product_category_name_english, 'unknown') AS category_name,
        COUNT(i.order_item_id) AS total_units_sold,
        COUNT(DISTINCT i.order_id) AS total_distinct_orders,
        ROUND(SUM(i.price), 2) AS total_item_revenue,
        ROUND(SUM(i.freight_value), 2) AS total_freight_value,
        ROUND(SUM(i.total_item_value), 2) AS total_gross_value,
        ROUND(AVG(i.price), 2) AS avg_unit_price
    FROM fact_order_items i
    JOIN dim_products p ON i.product_id = p.product_id
    GROUP BY COALESCE(p.product_category_name_english, 'unknown')
)
SELECT
    DENSE_RANK() OVER (ORDER BY total_item_revenue DESC) AS revenue_rank,
    category_name,
    total_units_sold,
    total_distinct_orders,
    total_item_revenue,
    total_freight_value,
    total_gross_value,
    avg_unit_price,
    -- Share of marketplace item revenue
    ROUND(
        (total_item_revenue * 100.0) / SUM(total_item_revenue) OVER (),
        2
    ) AS pct_of_total_revenue,
    -- Cumulative revenue percentage for Pareto analysis
    ROUND(
        SUM(total_item_revenue) OVER (
            ORDER BY total_item_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / SUM(total_item_revenue) OVER (),
        2
    ) AS cumulative_revenue_pct,
    -- Pareto 80/20 Classification
    CASE 
        WHEN SUM(total_item_revenue) OVER (
            ORDER BY total_item_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / SUM(total_item_revenue) OVER () <= 80.0 THEN 'Core 80% (A)'
        ELSE 'Long Tail (B/C)'
    END AS pareto_class
FROM category_totals
ORDER BY revenue_rank;
