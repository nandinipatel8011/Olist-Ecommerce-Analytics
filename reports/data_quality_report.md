# Data Quality & Preprocessing Audit Report

**Project**: E-Commerce Sales & Business Intelligence Analytics Platform  
**Environment**: Python 3.13.2 | Pandas 2.3.3  
**Audit Status**: **PASSED (All Checks Verified)**  
**Analyst**: Nandini Patel ([GitHub: nandinipatel8011](https://github.com/nandinipatel8011))  

---

## 1. Executive Summary & Record Reconciliations

This report audits the transformations performed during Phase 3. Cleaning was executed on separate DataFrames without modifying any raw files in `data/raw/`. 

All original records were preserved across all transactional tables. Zero valid records were silently dropped due to optional fields (such as missing review comments or undelivered status).

### Record Count Reconciliation (Raw vs. Cleaned)

| Table Name | Raw Records | Cleaned Records | Delta | Transformation / Handling Description |
|---|---|---|---|---|
| `orders` | 99,441 | **99,441** | 0 | Converted 5 date columns to datetime. Retained 2,965 undelivered orders with `NULL` duration/delay. |
| `order_items` | 112,650 | **112,650** | 0 | Standardized currency floats, engineered `total_item_value` (`price + freight`). |
| `order_payments` | 103,886 | **103,886** | 0 | Standardized payment methods, engineered `is_installment` flag. |
| `order_reviews` | 99,224 | **99,224** | 0 | Preserved all rows. Imputed missing comment titles/messages with empty strings. |
| `customers` | 99,441 | **99,441** | 0 | Standardized city title-case and state upper-case. |
| `products` | 32,951 | **32,951** | 0 | Imputed 610 missing categories as `'unknown'`. Left-joined English translations. Engineered volume. |
| `sellers` | 3,095 | **3,095** | 0 | Standardized text formatting (title-cased cities, uppercase states). |
| `geolocation` | 1,000,163 | **19,010** | -981,153 | Filtered 42 coordinate noise anomalies; aggregated valid points to median coordinates by zip prefix. |
| `translations` | 71 | **74** | +3 | Enriched with 2 missing catalog categories (`portateis_cozinha...`, `pc_gamer`) and `'unknown'`. |

---

## 2. Customer Architecture & Identification Findings

Understanding the distinction between transactional customer IDs and real-world customer profiles:

```text
Total Order-Scoped Customer IDs (customer_id):       99,441
Distinct Real-World Buyers (customer_unique_id):      96,096
Distinct Repeat Buyers (>= 2 orders placed):          2,997 (3.12%)
Additional Repeat Orders (transactions beyond 1st):   3,345 (3.36%)
```

### Statistical Analysis
- **`customer_id`**: A surrogate transactional identifier generated per order. Because every row in `orders` links to a unique `customer_id`, counting `COUNT(DISTINCT customer_id)` would falsely report 100% single-time purchasers.
- **`customer_unique_id`**: Identifies the real-world individual.
  - Exactly **2,997 distinct customers** placed 2 or more orders in the marketplace.
  - These 2,997 repeat buyers generated **3,345 additional transactions** beyond their initial purchase.
  - The true repeat customer rate is **3.12%** of unique customers, generating 3.36% of all orders.

---

## 3. Delivery Metrics & Undelivered Orders Integrity

Per engineering requirements, delivery duration and delivery delay are calculated **strictly when valid dates exist**:

- **Delivered Orders**: 96,476 orders
- **Undelivered Orders** (In Transit, Canceled, Unavailable): 2,965 orders
- **Undelivered Handling Verification**:
  - `delivery_duration_days`: **100% NULL** for undelivered orders ([PASS])
  - `delivery_delay_days`: **100% NULL** for undelivered orders ([PASS])
  - `is_delayed`: **100% NULL** for undelivered orders ([PASS])
- **Delivery Performance Summary (Delivered Cohort)**:
  - Average Delivery Duration: **12.56 days** (Median: **10.22 days**)
  - Delayed Delivered Orders: **7,827** (8.11% of delivered orders)
  - On-Time Delivered Orders: **88,649** (91.89% of delivered orders)
  - Average Delay for Late Orders: **9.55 days** beyond promised SLA

---

## 4. Chronological Timestamp Anomaly Audit

A rigorous chronological audit of all timestamps identified:

1. **Delivered Before Purchase**: **0 records**. Zero physical violations found.
2. **Carrier Before Purchase**: **166 records**. Handover to the carrier is logged with a timestamp slightly earlier than the purchase timestamp. This is a recognized real-world artifact caused by time-zone differences between seller dispatch systems and marketplace checkout servers.
3. **Customer Before Carrier**: **23 records**. Customer doorstep delivery was recorded before the carrier status updated, attributable to courier batch scan synchronization delays.

---

## 5. Geolocation Coordinate Validation & Optimization

### Methodology & Spatial Trade-off
1. **Raw Coordinate Bounds**:
   - Brazil's geographical limits lie approximately within Latitude `[-33.75, +5.27]` and Longitude `[-73.98, -34.79]`.
   - An empirical bounding box `[-34.0, +5.5]` lat and `[-74.0, -34.5]` lng was applied as a sanity filter.
   - **42 corrupted rows** (e.g., coordinates in Europe or the Pacific due to sensor noise or sign inversion) were excluded.
   - *Documentation Note*: This bounding box is an empirical filter to eliminate corrupt noise, not an exact sovereign polygon.
2. **Median Coordinate Aggregation**:
   - The remaining 1,000,121 valid coordinate rows were grouped by `geolocation_zip_code_prefix` (19,010 distinct prefixes).
   - `geolocation_lat` = median latitude of the postal prefix.
   - `geolocation_lng` = median longitude of the postal prefix.
   - `geolocation_city` & `geolocation_state` = statistical mode.
3. **Impact**:
   - Storage reduced by **98.1%** (~58 MB down to ~1.2 MB), dramatically improving SQLite query execution speed and Power BI rendering responsiveness while preserving postal-level geographic accuracy.

---

## 6. Automated Integrity Test Results

### 6.1. Primary Key Uniqueness
- `orders.order_id`: **PASSED (Unique)**
- `customers.customer_id`: **PASSED (Unique)**
- `sellers.seller_id`: **PASSED (Unique)**
- `products.product_id`: **PASSED (Unique)**
- `geolocation.geolocation_zip_code_prefix`: **PASSED (Unique)**
- `order_items.(order_id, order_item_id)`: **PASSED (Composite Unique)**

### 6.2. Foreign Key Referential Integrity
- `order_items.order_id -> orders.order_id`: **PASSED (100% matched)**
- `order_items.product_id -> products.product_id`: **PASSED (100% matched)**
- `order_items.seller_id -> sellers.seller_id`: **PASSED (100% matched)**
- `order_payments.order_id -> orders.order_id`: **PASSED (100% matched)**
- `order_reviews.order_id -> orders.order_id`: **PASSED (100% matched)**
- `orders.customer_id -> customers.customer_id`: **PASSED (100% matched)**

### 6.3. Domain Constraints
- `price >= 0`: **PASSED**
- `freight_value >= 0`: **PASSED**
- `payment_value >= 0`: **PASSED**
- `payment_installments >= 0`: **PASSED**
- `review_score in [1, 5]`: **PASSED**
- `latitude in [-34.0, 5.5]`: **PASSED**
- `longitude in [-74.0, -34.5]`: **PASSED**
