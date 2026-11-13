# Raw Data Inspection & Quality Audit Report

**Project**: E-Commerce Sales & Business Intelligence Analytics Platform  
**Dataset**: Olist Brazilian E-Commerce Public Dataset (Kaggle)  
**Audit Date**: November 2026  
**Analyst**: Nandini Patel ([GitHub: nandinipatel8011](https://github.com/nandinipatel8011))  
**Environment**: Python 3.13.2 | Pandas 2.3.3  

---

## 1. Executive Summary & Table Inventory

All 9 original CSV datasets were successfully extracted and audited from `data/raw/archive.zip`. The inspection verified that no files were corrupted, schemas match official Olist specifications, and uncompressed storage totals **~126.2 MB** across **1,450,861 total transactional records**.

### Master Table Inventory

| Table Name | Entity Type | File Size (MB) | RAM (MB) | Row Count | Column Count | Null Values | Exact Duplicates |
|---|---|---|---|---|---|---|---|
| `olist_orders_dataset.csv` | Fact (Orders) | 16.84 | 52.94 | 99,441 | 8 | 4,908 | 0 |
| `olist_order_items_dataset.csv` | Fact (Items) | 14.72 | 35.99 | 112,650 | 7 | 0 | 0 |
| `olist_order_payments_dataset.csv` | Fact (Payments) | 5.51 | 16.23 | 103,886 | 5 | 0 | 0 |
| `olist_order_reviews_dataset.csv` | Fact (Reviews) | 13.78 | 39.12 | 99,224 | 7 | 145,903 | 0 |
| `olist_customers_dataset.csv` | Dimension (Customers) | 8.62 | 26.59 | 99,441 | 5 | 0 | 0 |
| `olist_products_dataset.csv` | Dimension (Products) | 2.27 | 6.30 | 32,951 | 9 | 2,448 | 0 |
| `olist_sellers_dataset.csv` | Dimension (Sellers) | 0.17 | 0.59 | 3,095 | 4 | 0 | 0 |
| `olist_geolocation_dataset.csv` | Dimension (Spatial) | 58.44 | 129.38 | 1,000,163 | 5 | 0 | 261,831 |
| `product_category_name_translation.csv` | Lookup (Translation) | 0.003 | 0.01 | 71 | 2 | 0 | 0 |
| **Total** | | **126.17 MB** | **307.15 MB** | **1,450,861** | **52** | **153,259** | **261,831** |

---

## 2. Table-by-Table Schema & Null Audit

### 2.1. `olist_orders_dataset.csv` (99,441 rows, 8 columns)
Grain: **One row per order**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `order_id` | object (UUID) | 0 | 0.00% | Unique order identifier. Primary Key. |
| `customer_id` | object (UUID) | 0 | 0.00% | Transactional customer key linking to `olist_customers_dataset`. |
| `order_status` | object | 0 | 0.00% | Order lifecycle status (`delivered`, `shipped`, `canceled`, etc.). |
| `order_purchase_timestamp` | object | 0 | 0.00% | Customer checkout timestamp. |
| `order_approved_at` | object | 160 | 0.16% | Missing for canceled orders or bank slips (`boleto`) pending payment. |
| `order_delivered_carrier_date` | object | 1,783 | 1.79% | Missing for orders canceled prior to fulfillment or awaiting pickup. |
| `order_delivered_customer_date` | object | 2,965 | 2.98% | Missing for undelivered orders (in transit, unavailable, or canceled). |
| `order_estimated_delivery_date` | object | 0 | 0.00% | Delivery SLA promised to buyer. |

---

### 2.2. `olist_order_items_dataset.csv` (112,650 rows, 7 columns)
Grain: **One row per item line within an order**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `order_id` | object (UUID) | 0 | 0.00% | Foreign Key linking to `olist_orders_dataset`. |
| `order_item_id` | int64 | 0 | 0.00% | Item sequence counter within the order (1, 2, 3...). |
| `product_id` | object (UUID) | 0 | 0.00% | Foreign Key linking to `olist_products_dataset`. |
| `seller_id` | object (UUID) | 0 | 0.00% | Foreign Key linking to `olist_sellers_dataset`. |
| `shipping_limit_date` | object | 0 | 0.00% | Seller dispatch deadline. |
| `price` | float64 | 0 | 0.00% | Item sales price in BRL. Range: [0.85, 6,729.00]. |
| `freight_value` | float64 | 0 | 0.00% | Shipping cost charged for item in BRL. Range: [0.00, 409.68]. |

---

### 2.3. `olist_order_payments_dataset.csv` (103,886 rows, 5 columns)
Grain: **One row per payment installment / voucher attempt**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `order_id` | object (UUID) | 0 | 0.00% | Foreign Key linking to `olist_orders_dataset`. |
| `payment_sequential` | int64 | 0 | 0.00% | Payment sequence counter (1 to 29). |
| `payment_type` | object | 0 | 0.00% | Channels: `credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`. |
| `payment_installments` | int64 | 0 | 0.00% | Installments count (0 to 24). |
| `payment_value` | float64 | 0 | 0.00% | Transaction value in BRL. Range: [0.00, 13,664.08]. |

---

### 2.4. `olist_order_reviews_dataset.csv` (99,224 rows, 7 columns)
Grain: **One row per customer satisfaction survey**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `review_id` | object (UUID) | 0 | 0.00% | Review record identifier. |
| `order_id` | object (UUID) | 0 | 0.00% | Foreign Key linking to `olist_orders_dataset`. |
| `review_score` | int64 | 0 | 0.00% | Rating from 1 (worst) to 5 (best). Zero nulls. |
| `review_comment_title` | object | 87,656 | 88.34% | Optional written title. Mostly omitted by mobile users. |
| `review_comment_message` | object | 58,247 | 58.70% | Optional written feedback. Omitted when satisfied with simple star rating. |
| `review_creation_date` | object | 0 | 0.00% | Survey generation timestamp. |
| `review_answer_timestamp` | object | 0 | 0.00% | Survey submission timestamp. |

---

### 2.5. `olist_customers_dataset.csv` (99,441 rows, 5 columns)
Grain: **One row per transactional customer profile**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `customer_id` | object (UUID) | 0 | 0.00% | Order-scoped surrogate key (99,441 distinct values). |
| `customer_unique_id` | object (UUID) | 0 | 0.00% | Real-world customer ID (96,096 distinct individuals). |
| `customer_zip_code_prefix` | int64 | 0 | 0.00% | First 5 digits of CEP postal code. |
| `customer_city` | object | 0 | 0.00% | Customer city (4,119 distinct cities). |
| `customer_state` | object | 0 | 0.00% | Customer state (27 Brazilian Federative Units). |

---

### 2.6. `olist_products_dataset.csv` (32,951 rows, 9 columns)
Grain: **One row per catalog product**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `product_id` | object (UUID) | 0 | 0.00% | Product identifier. Primary Key. |
| `product_category_name` | object | 610 | 1.85% | Portuguese category name. 610 items have missing category. |
| `product_name_lenght` | float64 | 610 | 1.85% | Missing whenever category is missing. |
| `product_description_lenght` | float64 | 610 | 1.85% | Missing whenever category is missing. |
| `product_photos_qty` | float64 | 610 | 1.85% | Missing whenever category is missing. |
| `product_weight_g` | float64 | 2 | 0.01% | Physical package weight in grams. |
| `product_length_cm` | float64 | 2 | 0.01% | Physical package length in cm. |
| `product_height_cm` | float64 | 2 | 0.01% | Physical package height in cm. |
| `product_width_cm` | float64 | 2 | 0.01% | Physical package width in cm. |

---

### 2.7. `olist_sellers_dataset.csv` (3,095 rows, 4 columns)
Grain: **One row per active seller**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `seller_id` | object (UUID) | 0 | 0.00% | Seller identifier. Primary Key. |
| `seller_zip_code_prefix` | int64 | 0 | 0.00% | Seller postal prefix. |
| `seller_city` | object | 0 | 0.00% | Seller municipality. |
| `seller_state` | object | 0 | 0.00% | Seller state. |

---

### 2.8. `product_category_name_translation.csv` (71 rows, 2 columns)
Grain: **One row per category mapping**.

| Column | Data Type | Null Count | Null % | Business Interpretation |
|---|---|---|---|---|
| `product_category_name` | object | 0 | 0.00% | Original Portuguese category name. |
| `product_category_name_english` | object | 0 | 0.00% | English translation for international reporting. |

---

## 3. Customer Architecture Deep-Dive

An essential audit finding is the structural difference between `customer_id` and `customer_unique_id`:

```text
Total Order-Scoped Records (customer_id):       99,441
Distinct Real-World Buyers (customer_unique_id):  96,096
Repeat Buyer Transactions:                         3,345 (3.36%)
```

- **Why this exists**: Olist creates a separate `customer_id` for every transaction for anonymization and session tracking.
- **Analytical Rule**: Any customer retention metric (Repeat Rate, Cohort Analysis, Customer Lifetime Value) **must use `customer_unique_id`**. Using `customer_id` will artificially report a 0% repeat purchase rate.

---

## 4. Geolocation Table Deep-Dive & Anomalies

Inspection of `olist_geolocation_dataset.csv` reveals key physical data characteristics:
- **Total Records**: 1,000,163 rows.
- **Exact Duplicate Rows**: 261,831 rows (identical in all 5 columns).
- **Distinct Zip Code Prefixes**: 19,015 prefixes.
- **Redundancy Ratio**: **98.1%** of rows are redundant spatial readings for existing prefixes.
- **Coordinate Boundary Anomalies**:
  - Brazilian territory spans Latitude [-33.75, +5.27] and Longitude [-73.98, -34.79].
  - In raw data:
    - Latitude range: `[-36.6054, +45.0659]` (positive latitudes like +45.06 are in Europe/North America, representing GPS sensor glitches or mistyped signs).
    - Longitude range: `[-101.4668, +121.1054]` (readings in the Pacific or Asia).
- **Phase 3 Treatment**: Filter out coordinate outliers outside Brazil's geographic bounding box, deduplicate exact rows, and aggregate by `geolocation_zip_code_prefix` taking median latitude and longitude.

---

## 5. Pipeline Readiness & Phase 3 Actions

| Pipeline Task | Target Table(s) | Action Required |
|---|---|---|
| **Datetime Coercion** | `orders`, `order_items`, `reviews` | Convert 8 timestamp columns from string objects to `datetime64[ns]`. |
| **Missing Category Handling** | `products` | Impute 610 missing product categories as `'unknown'` / `'nao_informado'`. |
| **Category Translation Join** | `products` $\rightarrow$ `translation` | Left join to enrich products with English category names. Identify any unmapped categories. |
| **Coordinate Aggregation** | `geolocation` | Filter GPS noise and group by zip prefix using median lat/lng. |
| **Analytical Metrics** | `orders` | Calculate `delivery_duration_days` and `delivery_delay_days`. |
| **Relational Validation** | All tables | Assert referential integrity of foreign keys before loading into SQLite. |
