-- =====================================================================
-- 05. Payment Method Channels & Installment Financing Analysis
-- =====================================================================
-- Business Questions:
-- 1. Which payment channels process the highest transaction volume and value?
-- 2. How prevalent is installment financing across payment methods?
-- 3. What is the average order ticket size for credit cards vs bank slips (boleto)?
-- 4. How many customer orders use multiple split payment tenders?
--
-- SQL Concepts Demonstrated:
-- - Aggregations on fact_order_payments: COUNT(*), COUNT(DISTINCT), SUM(), AVG()
-- - Distinguishing between transaction count and unique order count
-- - Window function for total market share: SUM(...) OVER ()
-- - Subquery / CTE to detect split payment orders
-- =====================================================================

WITH payment_summary AS (
    SELECT
        payment_type,
        COUNT(*) AS total_payment_transactions,
        COUNT(DISTINCT order_id) AS distinct_orders_count,
        ROUND(SUM(payment_value), 2) AS total_payment_value,
        ROUND(AVG(payment_value), 2) AS avg_transaction_value,
        ROUND(AVG(payment_installments), 2) AS avg_installments,
        MAX(payment_installments) AS max_installments,
        SUM(is_installment) AS installment_transactions_count
    FROM fact_order_payments
    GROUP BY payment_type
)
SELECT
    payment_type,
    total_payment_transactions,
    distinct_orders_count,
    total_payment_value,
    -- Market share of total financial transaction value
    ROUND(
        (total_payment_value * 100.0) / SUM(total_payment_value) OVER (),
        2
    ) AS pct_of_total_payment_value,
    avg_transaction_value,
    ROUND((total_payment_value * 1.0) / distinct_orders_count, 2) AS avg_value_per_order,
    avg_installments,
    max_installments,
    installment_transactions_count,
    ROUND((installment_transactions_count * 100.0) / total_payment_transactions, 2) AS installment_share_pct
FROM payment_summary
ORDER BY total_payment_value DESC;
