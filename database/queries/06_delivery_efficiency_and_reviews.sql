-- =====================================================================
-- 06. Delivery SLA Efficiency & Customer Review Sentiment Impact
-- =====================================================================
-- Business Questions:
-- 1. How does delivery timeliness correlate with customer satisfaction ratings?
-- 2. At what delay threshold does customer sentiment experience severe drops?
-- 3. How do 1-star dissatisfaction rates escalate when delivery is delayed?
-- 4. How are undelivered orders handled and how do their ratings compare?
--
-- SQL Concepts Demonstrated:
-- - Pre-aggregating reviews to order_id grain to avoid Cartesian fan-out
-- - Multi-tier CASE statement bucketing delivery delays into business tiers
-- - Conditional aggregation: COUNT(CASE WHEN ... THEN 1 END) for star counts
-- - Ratio calculations with NULLIF() to safeguard against division by zero
-- =====================================================================

WITH order_review_summary AS (
    -- Pre-aggregate review scores to order_id grain
    SELECT
        order_id,
        ROUND(AVG(review_score), 2) AS avg_order_review_score,
        COUNT(review_id) AS total_reviews_count
    FROM fact_order_reviews
    GROUP BY order_id
),
delivery_bucketed AS (
    -- Classify orders into delivery timeliness buckets
    SELECT
        o.order_id,
        o.order_status,
        o.delivery_duration_days,
        o.delivery_delay_days,
        r.avg_order_review_score,
        CASE
            WHEN o.order_delivered_customer_date IS NULL THEN 'Undelivered (In Transit / Canceled)'
            WHEN o.delivery_delay_days <= 0 THEN '0. Early / On-Time (<= 0d)'
            WHEN o.delivery_delay_days <= 3 THEN '1. Slightly Late (1-3d)'
            WHEN o.delivery_delay_days <= 7 THEN '2. Moderately Late (4-7d)'
            ELSE '3. Severely Late (> 7d)'
        END AS delivery_performance_bucket
    FROM fact_orders o
    LEFT JOIN order_review_summary r ON o.order_id = r.order_id
)
SELECT
    delivery_performance_bucket,
    COUNT(order_id) AS total_orders,
    ROUND(COUNT(order_id) * 100.0 / (SELECT COUNT(*) FROM fact_orders), 2) AS pct_of_total_orders,
    COUNT(CASE WHEN avg_order_review_score IS NOT NULL THEN 1 END) AS reviewed_orders_count,
    ROUND(AVG(avg_order_review_score), 2) AS avg_customer_review_score,
    ROUND(AVG(delivery_duration_days), 2) AS avg_delivery_duration_days,
    ROUND(AVG(delivery_delay_days), 2) AS avg_delivery_delay_days,
    COUNT(CASE WHEN avg_order_review_score = 5 THEN 1 END) AS five_star_reviews_count,
    COUNT(CASE WHEN avg_order_review_score = 1 THEN 1 END) AS one_star_reviews_count,
    ROUND(
        COUNT(CASE WHEN avg_order_review_score = 1 THEN 1 END) * 100.0 
        / NULLIF(COUNT(CASE WHEN avg_order_review_score IS NOT NULL THEN 1 END), 0), 
        2
    ) AS one_star_dissatisfaction_rate_pct
FROM delivery_bucketed
GROUP BY delivery_performance_bucket
ORDER BY delivery_performance_bucket;
