-- =====================================================================
-- 03. Customer RFM Segmentation & Repeat Purchase Behavior
-- =====================================================================
-- Business Questions:
-- 1. What is the distribution of customer purchase frequency and recency?
-- 2. How many real-world customers (customer_unique_id) are repeat buyers?
-- 3. How do customer segments break down across RFM (Recency, Frequency, Monetary)?
-- 4. Which customer segment generates the largest share of marketplace revenue?
--
-- Population & Reconciliation Notes:
-- - The entire population of 96,096 distinct real-world buyers (customer_unique_id)
--   is accounted for using a LEFT JOIN on fact_order_items.
-- - 676 customers placed orders that were canceled or unavailable before items were
--   assigned (zero line items in fact_order_items). They are categorized under
--   'Unfulfilled / Canceled' (0.00 BRL monetary spend).
-- - Monetary value is defined as total item sales price (excluding freight).
-- - Frequency is computed using COUNT(DISTINCT o.order_id) to reflect distinct orders.
-- - Recency is calculated relative to baseline date '2018-10-18' (1 day post dataset max).
-- =====================================================================

WITH customer_order_summary AS (
    -- Pre-aggregate to customer_unique_id grain using LEFT JOIN to retain 100% of customers
    SELECT
        c.customer_unique_id,
        MAX(o.order_purchase_timestamp) AS last_purchase_timestamp,
        COUNT(DISTINCT o.order_id) AS order_frequency,
        ROUND(COALESCE(SUM(i.price), 0.0), 2) AS total_monetary_spend,
        ROUND(COALESCE(AVG(i.price), 0.0), 2) AS avg_item_spend
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_id = o.customer_id
    LEFT JOIN fact_order_items i ON o.order_id = i.order_id
    GROUP BY c.customer_unique_id
),
rfm_raw AS (
    -- Calculate Recency in days relative to baseline reference date '2018-10-18'
    SELECT
        customer_unique_id,
        CAST(julianday('2018-10-18') - julianday(last_purchase_timestamp) AS INTEGER) AS recency_days,
        order_frequency,
        total_monetary_spend
    FROM customer_order_summary
),
rfm_scored AS (
    -- Assign R, F, M scores
    -- Recency: fewer days = more recent = higher score (NTILE 5 descending)
    -- Monetary: NTILE 5 ascending for purchasing cohort; 0 for zero-spend cohort
    -- Frequency: ~97% order once, so discrete scoring reflects true repeat tiers
    SELECT
        customer_unique_id,
        recency_days,
        order_frequency,
        total_monetary_spend,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE 
            WHEN total_monetary_spend = 0.0 THEN 0
            WHEN order_frequency = 1 THEN 1
            WHEN order_frequency = 2 THEN 3
            WHEN order_frequency = 3 THEN 4
            ELSE 5
        END AS f_score,
        CASE
            WHEN total_monetary_spend = 0.0 THEN 0
            ELSE NTILE(5) OVER (
                PARTITION BY (CASE WHEN total_monetary_spend > 0 THEN 1 ELSE 0 END) 
                ORDER BY total_monetary_spend ASC
            )
        END AS m_score
    FROM rfm_raw
),
rfm_segmented AS (
    -- Strategic behavioral customer segments across all 96,096 distinct customers
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
            WHEN total_monetary_spend = 0.0 THEN 'Unfulfilled / Canceled'
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
SELECT
    customer_segment,
    COUNT(*) AS total_customers,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM rfm_segmented), 2) AS customer_share_pct,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(order_frequency), 2) AS avg_orders_per_customer,
    ROUND(SUM(total_monetary_spend), 2) AS total_segment_revenue,
    ROUND(
        SUM(total_monetary_spend) * 100.0 / NULLIF((SELECT SUM(total_monetary_spend) FROM rfm_segmented), 0),
        2
    ) AS revenue_share_pct,
    ROUND(AVG(total_monetary_spend), 2) AS avg_spend_per_customer
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY total_segment_revenue DESC;
