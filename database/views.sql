-- =====================================================================
-- Olist E-Commerce Analytical Reporting Views
-- =====================================================================
-- Project: E-Commerce Sales & Business Intelligence Analytics Platform
-- Author: Nandini Patel (GitHub: nandinipatel8011)
-- Description: Four standardized views for BI consumption and executive reporting.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. View: Monthly Sales Trends & MoM Growth
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS view_monthly_sales;
CREATE VIEW view_monthly_sales AS
WITH order_item_totals AS (
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
    LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue,
    CASE 
        WHEN LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) IS NULL THEN NULL
        WHEN LAG(total_gross_revenue, 1) OVER (ORDER BY year_month) = 0 THEN NULL
        ELSE ROUND(
            ((total_gross_revenue - LAG(total_gross_revenue, 1) OVER (ORDER BY year_month)) * 100.0) 
            / LAG(total_gross_revenue, 1) OVER (ORDER BY year_month), 
            2
        )
    END AS mom_revenue_growth_pct,
    ROUND(
        SUM(total_gross_revenue) OVER (
            ORDER BY year_month 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS cumulative_running_revenue
FROM monthly_metrics;

-- ---------------------------------------------------------------------
-- 2. View: Product Category Performance & Pareto Ranking
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS view_category_performance;
CREATE VIEW view_category_performance AS
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
    ROUND((total_item_revenue * 100.0) / SUM(total_item_revenue) OVER (), 2) AS pct_of_total_revenue,
    ROUND(
        SUM(total_item_revenue) OVER (
            ORDER BY total_item_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / SUM(total_item_revenue) OVER (),
        2
    ) AS cumulative_revenue_pct,
    CASE 
        WHEN SUM(total_item_revenue) OVER (
            ORDER BY total_item_revenue DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) * 100.0 / SUM(total_item_revenue) OVER () <= 80.0 THEN 'Core 80% (A)'
        ELSE 'Long Tail (B/C)'
    END AS pareto_class
FROM category_totals;

-- ---------------------------------------------------------------------
-- 3. View: Customer RFM Scoring & Segmentation
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS view_customer_rfm;
CREATE VIEW view_customer_rfm AS
WITH customer_order_summary AS (
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase_timestamp,
        COUNT(DISTINCT o.order_id) AS order_frequency,
        ROUND(SUM(i.price), 2) AS total_monetary_spend,
        ROUND(AVG(i.price), 2) AS avg_item_spend
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    JOIN fact_order_items i ON o.order_id = i.order_id
    GROUP BY c.customer_unique_id
),
rfm_raw AS (
    SELECT
        customer_unique_id,
        CAST(julianday('2018-10-18') - julianday(last_purchase_timestamp) AS INTEGER) AS recency_days,
        order_frequency,
        total_monetary_spend
    FROM customer_order_summary
),
rfm_scored AS (
    SELECT
        customer_unique_id,
        recency_days,
        order_frequency,
        total_monetary_spend,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE 
            WHEN order_frequency = 1 THEN 1
            WHEN order_frequency = 2 THEN 3
            WHEN order_frequency = 3 THEN 4
            ELSE 5
        END AS f_score,
        NTILE(5) OVER (ORDER BY total_monetary_spend ASC) AS m_score
    FROM rfm_raw
)
SELECT
    customer_unique_id,
    recency_days,
    order_frequency,
    total_monetary_spend,
    r_score,
    f_score,
    m_score,
    (r_score * 100 + f_score * 10 + m_score) AS rfm_code,
    CASE
        WHEN r_score >= 4 AND f_score >= 3 THEN 'Champions & Loyal'
        WHEN r_score >= 4 AND f_score = 1 THEN 'New & Promising'
        WHEN r_score = 3 AND f_score >= 3 THEN 'Potential Loyalists'
        WHEN r_score = 3 AND f_score = 1 THEN 'Needs Attention'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk Repeaters'
        WHEN r_score <= 2 AND f_score = 1 AND m_score >= 4 THEN 'Hibernating High-Spenders'
        ELSE 'Lost / Inactive'
    END AS customer_segment
FROM rfm_scored;

-- ---------------------------------------------------------------------
-- 4. View: Delivery Performance & Review Sentiment
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS view_delivery_performance;
CREATE VIEW view_delivery_performance AS
WITH order_review_summary AS (
    SELECT
        order_id,
        ROUND(AVG(review_score), 2) AS avg_order_review_score,
        COUNT(review_id) AS total_reviews_count
    FROM fact_order_reviews
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.delivery_duration_days,
    o.delivery_delay_days,
    o.is_delayed,
    o.is_delivered,
    r.avg_order_review_score,
    CASE
        WHEN o.order_delivered_customer_date IS NULL THEN 'Undelivered (In Transit / Canceled)'
        WHEN o.delivery_delay_days <= 0 THEN '0. Early / On-Time (<= 0d)'
        WHEN o.delivery_delay_days <= 3 THEN '1. Slightly Late (1-3d)'
        WHEN o.delivery_delay_days <= 7 THEN '2. Moderately Late (4-7d)'
        ELSE '3. Severely Late (> 7d)'
    END AS delivery_performance_bucket
FROM fact_orders o
LEFT JOIN order_review_summary r ON o.order_id = r.order_id;
