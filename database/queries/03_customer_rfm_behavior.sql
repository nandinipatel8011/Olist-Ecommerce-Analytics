-- =====================================================================
-- 03. Customer RFM Segmentation & Repeat Purchase Behavior
-- =====================================================================
-- Business Questions:
-- 1. What is the distribution of customer purchase frequency and recency?
-- 2. How many real-world customers (customer_unique_id) are repeat buyers?
-- 3. How do customer segments break down across RFM (Recency, Frequency, Monetary)?
-- 4. Which customer segment generates the largest share of marketplace revenue?
--
-- SQL Concepts Demonstrated:
-- - Grouping by natural customer identifier: customer_unique_id (NOT customer_id)
-- - Frequency computed via COUNT(DISTINCT o.order_id) to avoid item line duplication
-- - Julian day date arithmetic for recency: julianday('2018-10-18') - julianday(...)
-- - Window Functions: NTILE(5) for quintile distribution scoring
-- - Multi-tier CASE statement for business customer segmentation
-- =====================================================================

WITH customer_order_summary AS (
    -- Pre-aggregate to customer_unique_id grain
    -- Monetary is defined as total item sales revenue (excluding freight)
    -- Frequency is distinct orders placed
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
    -- Calculate Recency in days relative to baseline reference date '2018-10-18'
    -- (1 day after the latest purchase recorded in the Olist dataset)
    SELECT
        customer_unique_id,
        CAST(julianday('2018-10-18') - julianday(last_purchase_timestamp) AS INTEGER) AS recency_days,
        order_frequency,
        total_monetary_spend
    FROM customer_order_summary
),
rfm_scored AS (
    -- Assign R, F, M scores from 1 (worst) to 5 (best)
    -- Recency: fewer days = more recent = higher score (NTILE 5 descending)
    -- Monetary: higher spend = higher score (NTILE 5 ascending)
    -- Frequency: ~97% of buyers ordered once, so discrete scoring reflects true repeat behavior
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
),
rfm_segmented AS (
    -- Combine scores into strategic behavioral segments
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
    FROM rfm_scored
)
-- Aggregate summary by customer segment
SELECT
    customer_segment,
    COUNT(*) AS total_customers,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_segmented), 2) AS customer_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(order_frequency), 2) AS avg_orders_per_customer,
    ROUND(SUM(total_monetary_spend), 2) AS total_segment_revenue,
    ROUND(
        SUM(total_monetary_spend) * 100.0 / (SELECT SUM(total_monetary_spend) FROM rfm_segmented),
        2
    ) AS revenue_share_pct,
    ROUND(AVG(total_monetary_spend), 2) AS avg_spend_per_customer
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY total_segment_revenue DESC;
