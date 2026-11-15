# Power BI Dataset Validation & Data Mart Reconciliation Report
**Project:** E-Commerce Sales & Business Intelligence Analytics Platform  
**Author:** Nandini Patel (GitHub: [nandinipatel8011](https://github.com/nandinipatel8011))  
**Date:** November 2026  
**Source Database:** `database/ecommerce.db` (SQLite relational schema)  
**Export Target Directory:** `data/processed/powerbi/`  
**Automated Export Pipeline:** `database/export_powerbi_data.py`  
**Automated Unit Test Suite:** `tests/test_powerbi_exports.py`  

---

## Executive Summary

Phase 7 establishes the analytical data marts and semantic datasets required for executive reporting and interactive dashboard design in Power BI Desktop (Phase 8). Using the fully cleansed, validated, and normalized relational schema from Phases 3–5, an automated export pipeline was built to generate a high-performance **star-constellation schema**.

The exported datasets are categorized into two architectural tiers:
1. **Group A: Core Power BI Semantic Model (8 files)**: Primary dimensional and transactional tables to be imported directly into the Power BI semantic model canvas.
2. **Group B: Auxiliary Reference & Validation Datasets (1 file + 6 query CSVs)**: High-resolution postal centroid lookups (`dim_geolocation.csv`) and existing Phase 5 benchmark SQL query extracts preserved for verification and external audit.

All datasets were subjected to a rigorous 9-point automated test suite (`tests/test_powerbi_exports.py`), verifying 100% row count parity, primary key uniqueness, strict 1:1 customer-to-order cardinality, customer population preservation (96,096 distinct real-world buyers), exact 8-cohort RFM segmentation reconciliation, decimal-level financial reconciliation, and complete 1,827-day date dimension continuity.

---

## 1. Export Manifest & Row Count Parity

Every table exported from SQLite was validated against its source row count. The table below details the complete export manifest:

| Tier | Filename | Source Table / View | Exported Rows | SQLite Row Count | Status | Grain / Entity Level |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Group A** | `dim_date.csv` | Synthetic Generation | 1,827 | N/A (1,827 days) | **PASSED** | 1 row per calendar day (`2016-01-01` to `2020-12-31`) |
| **Group A** | `dim_customers.csv` | `dim_customers` + RFM + Geo | 99,441 | 99,441 | **PASSED** | 1 row per order-scoped `customer_id` profile |
| **Group A** | `dim_products.csv` | `dim_products` + Pareto View | 32,951 | 32,951 | **PASSED** | 1 row per unique `product_id` |
| **Group A** | `dim_sellers.csv` | `dim_sellers` | 3,095 | 3,095 | **PASSED** | 1 row per unique `seller_id` |
| **Group A** | `fact_orders.csv` | `fact_orders` + Delivery View | 99,441 | 99,441 | **PASSED** | 1 row per unique `order_id` (header grain) |
| **Group A** | `fact_order_items.csv` | `fact_order_items` | 112,650 | 112,650 | **PASSED** | 1 row per order line item (`order_id`, `order_item_id`) |
| **Group A** | `fact_order_payments.csv` | `fact_order_payments` | 103,886 | 103,886 | **PASSED** | 1 row per payment split (`order_id`, `payment_sequential`) |
| **Group A** | `fact_order_reviews.csv` | `fact_order_reviews` | 99,224 | 99,224 | **PASSED** | 1 row per survey response (`review_id`, `order_id`) |
| **Group B** | `dim_geolocation.csv` | `dim_geolocation` | 19,010 | 19,010 | **PASSED** | 1 row per Brazilian postal code prefix centroid |

### Preservation of Phase 5 Benchmark Query Datasets
The 6 analytical CSV extracts generated in Phase 5 remain intact in `data/processed/powerbi/` for reference and SQL benchmark validation:
- `monthly_sales_trends.csv` (25 rows)
- `category_performance.csv` (72 rows)
- `customer_rfm_segments.csv` (8 rows)
- `regional_sales_performance.csv` (27 rows)
- `payment_channel_breakdown.csv` (5 rows)
- `delivery_delay_vs_reviews.csv` (4 rows)

---

## 2. Cardinality & Key Uniqueness Audit

### 2.1. Primary & Composite Key Uniqueness
Primary and composite key integrity was verified across all exported datasets:
- `dim_date`: `date_key` (1,827 unique) and `date` (1,827 unique). Zero duplicates.
- `dim_customers`: `customer_id` (99,441 unique). Zero duplicates.
- `dim_products`: `product_id` (32,951 unique). Zero duplicates.
- `dim_sellers`: `seller_id` (3,095 unique). Zero duplicates.
- `dim_geolocation`: `geolocation_zip_code_prefix` (19,010 unique). Zero duplicates.
- `fact_orders`: `order_id` (99,441 unique). Zero duplicates.
- `fact_order_items`: Composite `(order_id, order_item_id)` has 112,650 unique combinations. Zero duplicates.
- `fact_order_payments`: Composite `(order_id, payment_sequential)` has 103,886 unique combinations. Zero duplicates.
- `fact_order_reviews`: Composite `(review_id, order_id)` has 99,224 unique combinations. Zero duplicates.

### 2.2. Customer-to-Order Cardinality Proof (Strict 1:1)
A core modeling requirement was to resolve whether `dim_customers` to `fact_orders` represents a 1:1 or 1:Many relationship. The audit confirms:
1. `dim_customers` has **99,441 rows** and **99,441 unique `customer_id` values**.
2. `fact_orders` has **99,441 rows** and **99,441 unique `customer_id` values**.
3. Set equality audit:
   $$\text{Set}(\text{dim\_customers}[\text{customer\_id}]) \equiv \text{Set}(\text{fact\_orders}[\text{customer\_id}])$$
   - Fact orders with missing customer profile: **0**
   - Customer profiles without an order: **0**
4. **Conclusion**: The relationship between `dim_customers[customer_id]` and `fact_orders[customer_id]` is strictly **1:1**. In Power BI, this is modeled as a 1:1 relationship with single-direction cross-filtering (`dim_customers` filtering `fact_orders`).

---

## 3. Customer Population & RFM Segmentation Reconciliation

### 3.1. Order-Scoped Profile vs Real-World Buyer Distinction
In the Olist dataset architecture:
- `customer_id`: An order-scoped transaction identifier generated uniquely for each purchase.
- `customer_unique_id`: A persistent natural person identifier representing the real-world buyer.

Enriching `dim_customers` with customer-level RFM metrics links the RFM attributes of a `customer_unique_id` to each of their order-scoped `customer_id` rows. The audit confirms:
- Total order-scoped customer records in `dim_customers`: **99,441**
- Distinct real-world buyers (`customer_unique_id`): **96,096**
- Real-world buyers with exactly 1 order: **93,099** (96.88%)
- Real-world buyers with 2 or more orders: **2,997** (3.12%)

> [!IMPORTANT]
> **DAX Modeling Guideline**: In Power BI, real-world customer counts must **always** be calculated using `DISTINCTCOUNT(dim_customers[customer_unique_id])`. Never use table row counts `COUNTROWS(dim_customers)` as a proxy for customer population, as repeat buyers possess multiple rows.

### 3.2. Reconciliation of the 8 RFM Cohorts
When aggregated at the real-world buyer level (`customer_unique_id`), the customer segments in `dim_customers.csv` reconcile with 100% precision to the analytical views and reports established in Phases 5 and 6:

| RFM Customer Segment | Unique Real-World Buyers | % of Unique Buyers | Total Row Records in `dim_customers` | Reconciliation Status |
| :--- | :---: | :---: | :---: | :--- |
| **New & Promising** | 37,032 | 38.54% | 37,032 | **MATCHED (100%)** |
| **Lost / Inactive** | 22,995 | 23.93% | 22,995 | **MATCHED (100%)** |
| **Needs Attention** | 18,466 | 19.22% | 18,466 | **MATCHED (100%)** |
| **Hibernating High-Spenders** | 13,938 | 14.50% | 13,938 | **MATCHED (100%)** |
| **Champions & Loyal** | 1,305 | 1.36% | 2,815 | **MATCHED (100%)** |
| **At Risk Repeaters** | 1,047 | 1.09% | 2,179 | **MATCHED (100%)** |
| **Unfulfilled / Canceled** | 676 | 0.70% | 685 | **MATCHED (100%)** |
| **Potential Loyalists** | 637 | 0.66% | 1,331 | **MATCHED (100%)** |
| **Total Population** | **96,096** | **100.00%** | **99,441** | **PERFECT RECONCILIATION** |

---

## 4. Decimal Financial Reconciliation

Financial metrics in the exported fact tables were reconciled against SQLite source sums at the cent level:

| Financial Metric | Source Table & Column | Reconciled Sum (BRL) | Target Benchmark | Variance | Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Item Product Revenue** | `fact_order_items.price` | **R$ 13,591,643.70** | R$ 13,591,643.70 | R$ 0.00 | **MATCHED** |
| **Freight Revenue** | `fact_order_items.freight_value` | **R$ 2,251,909.54** | R$ 2,251,909.54 | R$ 0.00 | **MATCHED** |
| **Freight-Inclusive Order Value** | `fact_order_items.total_item_value` | **R$ 15,843,553.24** | R$ 15,843,553.24 | R$ 0.00 | **MATCHED** |
| **Total Recorded Payment Value** | `fact_order_payments.payment_value` | **R$ 16,008,872.12** | R$ 16,008,872.12 | R$ 0.00 | **MATCHED** |

### Payment Value vs Order Value Variance
$$\text{Total Recorded Payment Value} - \text{Freight-Inclusive Order Value} = \text{R\$ } 16,008,872.12 - \text{R\$ } 15,843,553.24 = \mathbf{\text{R\$ } 165,318.88}$$

This **R$ 165,318.88** difference is documented directly as an observed empirical variance between recorded customer payments and order line item invoices. In accordance with analytical guidelines, its cause is not attributed to unverified assumptions (such as payment gateway interest or installment financing surcharges), as such mechanisms cannot be independently validated from the schema attributes.

---

## 5. Date Dimension Continuity & Lifecycle Coverage

### 5.1. Calendar Table Structure
The generated calendar table (`dim_date.csv`) spans from **January 1, 2016** through **December 31, 2020**, providing:
- **1,827 continuous calendar days**
- Zero missing days or date gaps
- Standardized Power BI attributes: `date_key` (integer YYYYMMDD), `date` (YYYY-MM-DD), `year`, `quarter`, `quarter_name`, `year_quarter`, `month`, `month_name`, `month_short`, `year_month`, `day`, `day_of_week` (1=Mon, 7=Sun), `day_name`, and `is_weekend` (0/1).

### 5.2. Fact Table Date Coverage Audit
All date fields across the fact tables were audited against `dim_date.csv` to ensure 100% referential integrity without null relationship errors in Power BI:

| Fact Table | Date Column Audited | Min Date | Max Date | Distinct Dates | Dates Missing in `dim_date` | Integrity Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `fact_orders` | `order_purchase_date` | 2016-09-04 | 2018-10-17 | 634 | **0** | **100% Covered** |
| `fact_orders` | `order_approved_date` | 2016-09-15 | 2018-11-12 | 611 | **0** | **100% Covered** |
| `fact_orders` | `order_delivered_carrier_date_only` | 2016-10-08 | 2018-10-17 | 547 | **0** | **100% Covered** |
| `fact_orders` | `order_delivered_customer_date_only` | 2016-10-11 | 2018-10-17 | 645 | **0** | **100% Covered** |
| `fact_orders` | `order_estimated_delivery_date` | 2016-09-30 | 2018-11-12 | 459 | **0** | **100% Covered** |
| `fact_order_items` | `shipping_limit_date_only` | 2016-09-19 | 2020-04-09 | 555 | **0** | **100% Covered** |
| `fact_order_reviews` | `review_creation_date_only` | 2016-10-02 | 2018-10-29 | 636 | **0** | **100% Covered** |
| `fact_order_reviews` | `review_answer_date_only` | 2016-10-07 | 2018-10-29 | 715 | **0** | **100% Covered** |

> [!NOTE]
> **2020 Outlier Items**: Exactly four order items in early 2017 have seller dispatch deadlines recorded in April 2020 (orders `13bdf4...`, `9c94a4...`, and `c2bb89...`). By extending `dim_date` to `2020-12-31`, 100% of these dates are accommodated without synthetic date truncation or orphaned relationships.

---

## 6. Automated Test Suite Execution

The automated test suite `tests/test_powerbi_exports.py` was executed with standard unittest runner:

```text
test_01_exported_files_exist_and_readable ... ok
test_02_row_counts_parity ... ok
test_03_primary_key_uniqueness ... ok
test_04_customer_orders_one_to_one_cardinality ... ok
test_05_customer_rfm_reconciliation ... ok
test_06_financial_reconciliation ... ok
test_07_foreign_key_referential_integrity ... ok
test_08_date_dimension_continuity_and_coverage ... ok
test_09_product_pareto_enrichment ... ok

----------------------------------------------------------------------
Ran 9 tests in 1.730s

OK
```

All 9 validation tests passed with zero errors and zero warnings. The datasets in `data/processed/powerbi/` are certified ready for Power BI semantic model import.
