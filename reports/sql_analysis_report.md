# Analytical SQL Querying & Views Report

**Project**: E-Commerce Sales & Business Intelligence Analytics Platform  
**Database**: `database/ecommerce.db` (SQLite 3)  
**Queries Executed**: 6 Production SQL Query Scripts (`database/queries/`)  
**Reporting Views Created**: 4 Standardized Views (`database/views.sql`)  
**Exports Generated**: 6 Analytical Mart CSVs (`data/processed/powerbi/`)  
**Analyst**: Nandini Patel ([GitHub: nandinipatel8011](https://github.com/nandinipatel8011))  

---

## 1. Executive Summary & Analytical Deliverables

Phase 5 developed and verified the production SQL querying layer of the platform. Using Common Table Expressions (CTEs), Window Functions, and multi-fact pre-aggregations, the queries extract business intelligence from raw relational tables without suffering from Cartesian fan-out.

### Summary of Executed Query Scripts & Exports

| Query Script | Exported Reporting CSV | Records | Key SQL Concepts Applied |
|---|---|---|---|
| `01_monthly_sales_trends.sql` | `monthly_sales_trends.csv` | 25 | `LAG()`, Running Total `SUM() OVER ()`, CTE pre-aggregation, `NULLIF()` |
| `02_product_category_performance.sql` | `category_performance.csv` | 74 | `DENSE_RANK()`, Pareto cumulative % `SUM() OVER ()`, multi-table `JOIN` |
| `03_customer_rfm_behavior.sql` | `customer_rfm_segments.csv` | 7 | `NTILE(5)`, Julian day date arithmetic, `customer_unique_id` grouping |
| `04_regional_geography_analysis.sql` | `regional_sales_performance.csv` | 27 | `LEFT JOIN` on postal centroids, missing coordinate tracking, `DENSE_RANK()` |
| `05_payment_channel_breakdown.sql` | `payment_channel_breakdown.csv` | 5 | Installment ratios, market share `OVER ()`, split payment analysis |
| `06_delivery_efficiency_and_reviews.sql` | `delivery_delay_vs_reviews.csv` | 5 | Multi-tier `CASE` bucketing, conditional `COUNT(CASE)`, satisfaction delta |

---

## 2. Advanced SQL Concepts Explained for Beginners

### 2.1. Common Table Expressions (CTEs)
- **Syntax**: `WITH cte_name AS (SELECT ...) SELECT ... FROM cte_name;`
- **What it is**: A CTE is a temporary named result set that exists only during query execution. It acts like an in-memory virtual table.
- **Why we used it**: In e-commerce, joining order items and payments directly causes **Cartesian multiplication (fan-out)**. By pre-aggregating `fact_order_items` into an `order_item_totals` CTE first, we roll up line items to the `order_id` level before joining with orders, completely preventing duplicate counting.

### 2.2. Window Function: `LAG()`
- **Syntax**: `LAG(column, offset) OVER (ORDER BY sort_column)`
- **What it is**: `LAG()` reaches back into the previous row in the result set without requiring a self-join.
- **Where implemented**: In `01_monthly_sales_trends.sql`, `LAG(total_gross_revenue, 1) OVER (ORDER BY year_month)` retrieves the previous month's revenue to compute **Month-over-Month (MoM) Growth %**:
  $$\text{MoM Growth \%} = \frac{\text{Current Month Revenue} - \text{Previous Month Revenue}}{\text{Previous Month Revenue}} \times 100$$
- **Edge Case Handling**: For the very first baseline month (`2016-09`), `LAG()` returns `NULL`. We used a `CASE` statement to return `NULL` instead of dividing by zero or inventing a fake percentage.

### 2.3. Running Totals & Cumulative Aggregations
- **Syntax**: `SUM(revenue) OVER (ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`
- **What it is**: A running total that accumulates revenue chronologically from the first record up to the current row.
- **Where implemented**: Tracks cumulative lifetime sales growth across all 25 active operating months.

### 2.4. Ranking with `DENSE_RANK()`
- **Syntax**: `DENSE_RANK() OVER (ORDER BY total_item_revenue DESC)`
- **Difference from `RANK()` and `ROW_NUMBER()`**:
  - `ROW_NUMBER()` assigns strict consecutive integers (1, 2, 3, 4) even if two items tie.
  - `RANK()` leaves gaps after ties (1, 2, 2, 4).
  - `DENSE_RANK()` assigns ties identical rank without skipping numbers (1, 2, 2, 3).
- **Where implemented**: Ranks the top-selling product categories and highest-revenue states.

### 2.5. Cumulative Percentage & Pareto (80/20) Analysis
- **Syntax**:
  ```sql
  ROUND(
      SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 
      / SUM(revenue) OVER (),
      2
  )
  ```
- **What it is**: The numerator computes the cumulative revenue of all top-ranked categories up to the current row. The denominator `SUM(revenue) OVER ()` computes the total marketplace revenue across the entire table.
- **Key Business Discovery**: Out of 74 total categories, exactly **17 categories** (~23%) generate **80% of total marketplace revenue**.

### 2.6. `NTILE(5)` Scoring & RFM Segmentation
- **Syntax**: `NTILE(5) OVER (ORDER BY metric ASC/DESC)`
- **What it is**: Divides an ordered population into 5 equal buckets (quintiles) numbered 1 through 5.
- **Where implemented**: Assigns Recency scores (5 = most recent, 1 = oldest) and Monetary scores (5 = highest spend, 1 = lowest spend).

---

## 3. Query Results & Business Answers

### 3.1. Monthly Sales Trends (`01_monthly_sales_trends.sql`)
- Total active historical operating months: **25 months** (Sept 2016 – Oct 2018).
- **Total Lifetime Product Revenue**: **13,591,643.70 BRL**
- **Total Freight Revenue Collected**: **2,251,909.54 BRL**
- **Total Gross Marketplace GMV**: **15,843,553.24 BRL**
- **Peak Monthly Revenue**: **November 2017** (1,194,882.80 BRL) driven by Black Friday promotions (+53.86% MoM growth).
- **Average Order Value (AOV)**: Stable between **130 BRL and 150 BRL** across mature operating months.

### 3.2. Top Product Categories & Pareto Distribution (`02_product_category_performance.sql`)
The top 5 categories by product merchandise value:
1. **`health_beauty`**: 1,258,681.34 BRL (9,670 units | 8,836 orders | 9.26% share)
2. **`watches_gifts`**: 1,205,005.68 BRL (5,991 units | 5,624 orders | 8.87% share)
3. **`bed_bath_table`**: 1,036,988.68 BRL (11,115 units | 9,417 orders | 7.63% share)
4. **`sports_leisure`**: 988,048.97 BRL (8,641 units | 7,720 orders | 7.27% share)
5. **`computers_accessories`**: 911,954.32 BRL (7,827 units | 6,689 orders | 6.71% share)

### 3.3. Customer RFM Segmentation (`03_customer_rfm_behavior.sql`)
Grouped by natural individual identity (`customer_unique_id`):

| Customer Segment | Total Buyers | Share % | Avg Recency (Days) | Avg Orders | Segment Revenue (BRL) | Revenue Share % |
|---|---|---|---|---|---|---|
| **New & Promising** | 36,911 | 38.68% | 139.5 | 1.00 | 5,213,699.94 | 38.36% |
| **Hibernating High-Spenders** | 14,042 | 14.72% | 445.2 | 1.00 | 3,918,635.55 | 28.83% |
| **Needs Attention** | 18,459 | 19.35% | 269.3 | 1.00 | 2,407,792.59 | 17.72% |
| **Lost / Inactive** | 23,095 | 24.20% | 444.9 | 1.00 | 1,288,223.76 | 9.48% |
| **Champions & Loyal** | 1,257 | 1.32% | 138.1 | 2.16 | 339,077.77 | 2.49% |
| **At Risk Repeaters** | 1,031 | 1.08% | 432.7 | 2.08 | 261,773.22 | 1.93% |
| **Potential Loyalists** | 625 | 0.65% | 267.3 | 2.09 | 162,440.87 | 1.19% |

### 3.4. Regional Geography & Logistics Cost (`04_regional_geography_analysis.sql`)
- **Dominant Market**: **São Paulo (`SP`)** represents **37.38% of total marketplace revenue** (5.92M BRL) across 41,746 orders.
- **Logistics Disparity**:
  - `SP` enjoys the fastest average delivery (**8.76 days**) and lowest average freight (**17.37 BRL**).
  - Northern and Northeastern states experience substantial logistics friction:
    - `BA` (Bahia): 19.34 days avg delivery, 29.83 BRL avg freight, 14.04% late orders.
    - `AM` (Amazonas): 25.99 days avg delivery, 43.84 BRL avg freight.
    - `RR` (Roraima): 28.98 days avg delivery, 53.30 BRL avg freight, 20.83% late delivery rate.
- **Postal Coverage Verification**: Preserving missing postal coordinates via `LEFT JOIN` ensured **100% of orders** and revenue were captured across all 27 Brazilian states.

### 3.5. Payment Methods & Installment Financing (`05_payment_channel_breakdown.sql`)
- **Credit Cards Dominate**: **78.34%** of total transaction value (12,542,084.19 BRL) across 76,795 payment tenders.
- **High Installment Penetration**: **66.85%** of credit card transactions use installment plans (average 3.51 installments, up to 24 months).
- **Cash Bank Slips (`boleto`)**: Second largest tender at **17.92%** (2,869,361.27 BRL) across 19,784 orders.
- **Split Tenders**: Exactly **2,961 orders** were paid using multiple tenders (e.g. voucher + credit card).

### 3.6. Delivery Timeliness vs. Customer Reviews (`06_delivery_efficiency_and_reviews.sql`)
Empirical proof of the direct link between delivery punctuality and customer satisfaction:

| Delivery Bucket | Total Orders | Order Share % | Avg Review Score | 1-Star Review Rate % |
|---|---|---|---|---|
| **0. Early / On-Time ($\le$ 0d delay)** | 88,649 | 89.15% | **4.29 / 5.0** | **6.56%** |
| **1. Slightly Late (1–3d delay)** | 2,662 | 2.68% | **3.77 / 5.0** | **13.69%** |
| **2. Moderately Late (4–7d delay)** | 1,819 | 1.83% | **2.32 / 5.0** | **53.02%** |
| **3. Severely Late (> 7d delay)** | 3,346 | 3.36% | **1.73 / 5.0** | **68.61%** |
| **Undelivered (In Transit / Canceled)** | 2,965 | 2.98% | **1.75 / 5.0** | **70.35%** |

> [!CAUTION]
> **Critical Business Finding**: When delivery delay crosses **3 days**, the 1-star dissatisfaction rate quadruples from 13.7% to 53.0%, and average review score collapses from 3.77 to 2.32. Proactive customer communications must trigger before day 3 of delay.

---

## 4. Standardized Reporting Views (`database/views.sql`)

Four views were instantiated inside `database/ecommerce.db` for BI consumption:
1. `view_monthly_sales`: Encapsulates monthly orders, customers, revenues, and MoM growth (25 rows).
2. `view_category_performance`: Encapsulates category ranks, revenues, and Pareto classification (74 rows).
3. `view_customer_rfm`: Encapsulates individual customer recency, frequency, spend, and segment tag (95,420 rows).
4. `view_delivery_performance`: Encapsulates order-level delivery status, delay duration, and review ratings (99,441 rows).
