# Relational Database Validation & Schema Audit Report

**Project**: E-Commerce Sales & Business Intelligence Analytics Platform  
**Database File**: `database/ecommerce.db` (Local SQLite Engine)  
**DDL Schema**: `database/schema.sql`  
**Audit Date**: November 2026  
**Analyst**: Nandini Patel ([GitHub: nandinipatel8011](https://github.com/nandinipatel8011))  
**Validation Status**: **PASSED (100% Constraints & Referential Integrity Verified)**  

---

## 1. Executive Summary & Database Architecture

The SQLite relational database was successfully created and loaded using `database/create_database.py` and `database/load_data.py`. The schema implements a **Star-Constellation dimensional model** composed of **5 conformed dimensions** and **4 granular fact tables**.

### Core Architecture Highlights
- **Strict Foreign Key Enforcement**: Every database connection explicitly runs `PRAGMA foreign_keys = ON;` to enforce referential integrity at the database engine level.
- **Fact Table Grain Preservation**: Every fact table models a distinct business process at its lowest atomic grain, completely preventing Cartesian fan-out.
- **Dual Customer Identity**: Both `customer_id` (order-scoped surrogate) and `customer_unique_id` (real-world person natural ID) are preserved with indexed lookups.
- **Indexed Performance**: 11 targeted B-tree indexes were constructed across foreign keys, timestamps, and customer identifiers.

---

## 2. Master Table Inventory & Row Count Reconciliation

All 9 tables loaded with **zero row count delta** compared to the cleaned CSV baselines:

| Table Name | Entity Type | Relational Grain | Primary Key | Processed CSV Rows | SQLite DB Rows | Delta |
|---|---|---|---|---|---|---|
| `dim_category_translation` | Dimension | One row per catalog category | `product_category_name` | 74 | **74** | 0 |
| `dim_products` | Dimension | One row per catalog product | `product_id` | 32,951 | **32,951** | 0 |
| `dim_customers` | Dimension | One row per order-customer identity | `customer_id` | 99,441 | **99,441** | 0 |
| `dim_sellers` | Dimension | One row per registered seller | `seller_id` | 3,095 | **3,095** | 0 |
| `dim_geolocation` | Dimension | One row per 5-digit postal prefix | `geolocation_zip_code_prefix` | 19,010 | **19,010** | 0 |
| `fact_orders` | Fact (Snapshot) | One row per distinct customer order | `order_id` | 99,441 | **99,441** | 0 |
| `fact_order_items` | Fact (Line Item) | One row per item line inside an order | `(order_id, order_item_id)` | 112,650 | **112,650** | 0 |
| `fact_order_payments` | Fact (Financial) | One row per payment installment / tender | `(order_id, payment_sequential)` | 103,886 | **103,886** | 0 |
| `fact_order_reviews` | Fact (Feedback) | One row per review survey submission | `(review_id, order_id)` | 99,224 | **99,224** | 0 |
| **Total Database Records** | | | | **569,772** | **569,772** | **0** |

---

## 3. Atomic Grain Definitions & Fan-Out Prevention

Naively joining multiple 1-to-many child tables directly against orders causes severe Cartesian expansion (fan-out). To eliminate this risk:

### Fact Table Grain Matrix
1. **`fact_orders`**: Grain is **one row per order** (`order_id`). Stores order lifecycle timestamps, fulfillment milestones, and delivery SLA metrics.
2. **`fact_order_items`**: Grain is **one row per order item** (`order_id, order_item_id`). Measures: `price`, `freight_value`, `total_item_value`. Multiple items can belong to the same order.
3. **`fact_order_payments`**: Grain is **one row per payment installment attempt** (`order_id, payment_sequential`). Measures: `payment_value`. An order can be split across multiple payment methods (e.g., voucher + credit card).
4. **`fact_order_reviews`**: Grain is **one row per survey submission** (`review_id, order_id`). Measure: `review_score`. Multiple reviews can associate with an order if a survey is updated or resubmitted.

### Fan-Out Prevention Rule
> [!IMPORTANT]
> Analytical queries will **never** directly join `fact_order_items` and `fact_order_payments` in a single unaggregated `JOIN` clause. All joins combining item revenue and payment amounts must pre-aggregate each fact to the `order_id` level using Common Table Expressions (CTEs) or query them independently.

---

## 4. Customer Identity Architecture

The schema explicitly distinguishes the two customer keys:

```text
Table: dim_customers
├── customer_id (PK):         Order-scoped surrogate transaction ID (99,441 unique values)
└── customer_unique_id:        Natural real-world customer ID (96,096 distinct individuals)
```

- `customer_id` is foreign-keyed to `fact_orders.customer_id` (1-to-1 relationship per order).
- `customer_unique_id` is indexed via `idx_customers_unique_id` for fast customer-level aggregations (repeat purchase rate, lifetime value, and order frequency distributions).

---

## 5. Geolocation Postal Code Investigation & Relational Strategy

### 5.1. Investigation of the 5 Anomalous Prefixes
During raw data coordinate validation, 5 postal prefixes were identified where all coordinate entries fell outside Brazilian sovereign territory (e.g., positive latitudes in Europe or longitudes in the Pacific caused by sensor glitch or typing errors):
- `{18243, 53990, 78131, 83252, 95130}`
- Cross-referencing against customer and seller databases revealed:
  - **1 customer** resides in zip code `78131` (Várzea Grande, Mato Grosso).
  - **0 sellers** reside in those 5 postal prefixes.

### 5.2. Postal Prefix Coverage Analysis
- Total distinct customer postal prefixes in Brazil: **14,994**
- Total distinct seller postal prefixes in Brazil: **2,246**
- Total distinct prefixes in `dim_geolocation`: **19,010**
- **Unmatched Customer Prefixes**: Exactly **158 customer prefixes** (~0.16% of orders) present in the customer table have no GPS log entries anywhere in the Olist dataset (even in the original 1M raw rows).
- **Unmatched Seller Prefixes**: Exactly **7 seller prefixes** have no GPS log entries.

### 5.3. Relational Design Decision
- Rather than fabricating artificial coordinates or forcing an unnatural foreign key that would reject 158 legitimate customer orders, `dim_geolocation` is modeled as an **independent spatial lookup dimension**.
- Customers and sellers join to `dim_geolocation` via `LEFT JOIN`.
- Unmatched zip codes gracefully preserve the customer's city and state (stored natively in `dim_customers`), while coordinate fields (`lat`, `lng`) evaluate to `NULL`.

---

## 6. Monetary Representation & Precision

- **Storage Affinity**: Defined as `NUMERIC(10,2)` across `price`, `freight_value`, `total_item_value`, and `payment_value`.
- **Formatting Standard**: In Python ETL, all monetary values are explicitly rounded to 2 decimal places (`.round(2)`).
- **SQLite Dynamic Type Handling**: SQLite stores numbers with numeric affinity as 64-bit IEEE 754 floating-point values. To prevent micro-cent rounding drift in financial queries, SQL queries use `ROUND(SUM(price), 2)` and `ROUND(SUM(payment_value), 2)` to guarantee consistent financial reporting.

---

## 7. Constraint Enforcement & Unit Test Outcomes

The automated test suite (`tests/test_sql_integrity.py`) executed 8 verification suites against `database/ecommerce.db`:

```text
test_01_all_tables_exist ................................... [PASS]
test_02_row_counts_match_processed_csvs .................... [PASS]
test_03_zero_foreign_key_violations (PRAGMA check) ......... [PASS]
test_04_duplicate_primary_key_rejection (UNIQUE) ........... [PASS]
test_05_invalid_foreign_key_rejection (FK) ................. [PASS]
test_06_check_constraint_review_score (CHECK [1, 5]) ....... [PASS]
test_07_check_constraint_negative_price (CHECK >= 0) ....... [PASS]
test_08_geolocation_postal_coverage_analysis ............... [PASS]

Ran 8 tests in 2.216s -- ALL TESTS PASSED
```

### Detailed Rejection Proofs
1. **Duplicate Primary Key Rejection**: Inserting an existing `customer_id` raised `sqlite3.IntegrityError: UNIQUE constraint failed: dim_customers.customer_id`.
2. **Invalid Foreign Key Rejection**: Inserting an order with `customer_id = 'NON_EXISTENT_ID'` raised `sqlite3.IntegrityError: FOREIGN KEY constraint failed`.
3. **Out-of-Bounds Review Score Rejection**: Inserting `review_score = 6` raised `sqlite3.IntegrityError: CHECK constraint failed: review_score BETWEEN 1 AND 5`.
4. **Negative Price Rejection**: Inserting `price = -15.50` raised `sqlite3.IntegrityError: CHECK constraint failed: price >= 0`.
5. **Referential Integrity Audit**: `PRAGMA foreign_key_check;` returned **0 violations** across all 569,772 rows.

---

## 8. Opening and Inspecting in DB Browser for SQLite

You can independently inspect and query the database using **DB Browser for SQLite** (free, open-source tool):

1. **Launch**: Open **DB Browser for SQLite**.
2. **Open Database**: Click **Open Database** (Ctrl+O) and select:
   `D:\DataAnalyticsProjects\Project1_EcommerceAnalytics\database\ecommerce.db`
3. **Inspect Schema**:
   - Navigate to the **Database Structure** tab.
   - Expand tables to see column types, primary keys, and foreign keys.
4. **Browse Records**:
   - Click the **Browse Data** tab and select any table (e.g., `fact_orders` or `dim_products`) from the dropdown.
5. **Execute Queries**:
   - Go to the **Execute SQL** tab.
   - Run sample queries:
     ```sql
     PRAGMA foreign_keys = ON;

     -- Verify orders summary
     SELECT order_status, COUNT(*) AS total_orders
     FROM fact_orders
     GROUP BY order_status
     ORDER BY total_orders DESC;
     ```
