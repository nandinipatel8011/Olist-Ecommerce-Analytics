-- =====================================================================
-- 04. Regional Geography & Logistics Cost Analysis
-- =====================================================================
-- Business Questions:
-- 1. Which Brazilian states dominate marketplace demand and revenue?
-- 2. How does average freight cost vary between coastal and inland states?
-- 3. What is the relationship between geographic location and delivery duration?
-- 4. How many customer postal codes have unmatched GPS coordinates?
--
-- SQL Concepts Demonstrated:
-- - CTE pre-aggregation of order items to prevent duplicate counting
-- - LEFT JOIN to dim_geolocation preserving all records regardless of coordinate coverage
-- - Handling NULL coordinates gracefully without dropping customer transactions
-- - Aggregate metrics: SUM(), AVG(), COUNT(DISTINCT), DENSE_RANK()
-- =====================================================================

WITH order_item_summary AS (
    -- Pre-aggregate line items to order grain
    SELECT
        order_id,
        ROUND(SUM(price), 2) AS item_revenue,
        ROUND(SUM(freight_value), 2) AS freight_revenue,
        ROUND(SUM(total_item_value), 2) AS gross_revenue
    FROM fact_order_items
    GROUP BY order_id
),
state_metrics AS (
    SELECT
        c.customer_state,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
        ROUND(SUM(i.item_revenue), 2) AS total_item_revenue,
        ROUND(SUM(i.freight_revenue), 2) AS total_freight_revenue,
        ROUND(SUM(i.gross_revenue), 2) AS total_gross_revenue,
        ROUND(AVG(i.freight_revenue), 2) AS avg_freight_per_order,
        ROUND(AVG(o.delivery_duration_days), 2) AS avg_delivery_duration_days,
        ROUND(AVG(o.is_delayed) * 100.0, 2) AS late_delivery_rate_pct,
        COUNT(DISTINCT g.geolocation_zip_code_prefix) AS distinct_matched_zip_prefixes,
        -- Document postal prefixes present in customer records but absent from geolocation
        COUNT(DISTINCT CASE WHEN g.geolocation_zip_code_prefix IS NULL THEN c.customer_zip_code_prefix END) AS unmatched_zip_prefixes
    FROM fact_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_item_summary i ON o.order_id = i.order_id
    LEFT JOIN dim_geolocation g ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
    GROUP BY c.customer_state
)
SELECT
    DENSE_RANK() OVER (ORDER BY total_gross_revenue DESC) AS state_revenue_rank,
    customer_state,
    total_orders,
    unique_customers,
    total_item_revenue,
    total_freight_revenue,
    total_gross_revenue,
    ROUND((total_gross_revenue * 100.0) / SUM(total_gross_revenue) OVER (), 2) AS revenue_share_pct,
    avg_freight_per_order,
    avg_delivery_duration_days,
    late_delivery_rate_pct,
    distinct_matched_zip_prefixes,
    unmatched_zip_prefixes
FROM state_metrics
ORDER BY state_revenue_rank;
