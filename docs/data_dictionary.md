# Olist E-Commerce Data Dictionary

## 1. Dataset Origin & Licensing

- **Dataset Name**: Brazilian E-Commerce Public Dataset by Olist
- **Source**: Kaggle ([Olist E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce))
- **Author**: Olist and André Sionek
- **Time Period**: Orders placed between October 2016 and October 2018
- **Geographic Coverage**: Brazil (27 Federative Units / States)
- **License**: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

---

## 2. Customer Identifiers: `customer_id` vs `customer_unique_id`

Understanding the dual-key customer architecture in Olist is one of the most important concepts for e-commerce data analysts.

| Column | Type | Scope | Definition & Analytical Purpose |
|---|---|---|---|
| `customer_id` | String (UUID) | Transactional / Order-Scoped | A surrogate key generated for each individual order. **It never repeats across orders**. Each row in `olist_orders_dataset` links to a unique `customer_id`. It is used exclusively as a foreign key to link orders to the customer dimension. |
| `customer_unique_id` | String (UUID) | Natural / Person-Scoped | A natural identifier representing the actual real-world person (e.g., citizen ID or customer profile). When the same individual places multiple orders across months, their purchases share the **same** `customer_unique_id`. |

### Critical Analytical Distinction
> [!IMPORTANT]
> - If an analyst counts `COUNT(DISTINCT customer_id)`, they will erroneously conclude that every customer only bought once (repeat rate = 0%).
> - To compute **Unique Customers**, **Repeat Purchase Rate**, **Cohort Retention**, and **Customer Lifetime Value (CLV)**, you **must use `customer_unique_id`**.

---

## 3. Detailed Table Specifications

### 3.1. `olist_orders_dataset.csv` (Orders Fact)
Grain: **One row per order**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | No | Unique identifier of the order (Primary Key). |
| `customer_id` | VARCHAR(32) | No | Order-scoped customer key (Foreign Key to `olist_customers_dataset`). |
| `order_status` | VARCHAR(20) | No | Status of order: `delivered`, `shipped`, `canceled`, `invoiced`, `processing`, `created`, `approved`, `unavailable`. |
| `order_purchase_timestamp` | DATETIME | No | Timestamp of when the purchase was made by the buyer. |
| `order_approved_at` | DATETIME | Yes | Timestamp of when payment was approved. Null for canceled/pending orders. |
| `order_delivered_carrier_date` | DATETIME | Yes | Timestamp of when the order was handed over to the postal partner/logistics carrier. |
| `order_delivered_customer_date` | DATETIME | Yes | Actual timestamp of order arrival at the customer's doorstep. |
| `order_estimated_delivery_date` | DATETIME | No | Promised estimated delivery date communicated to customer at purchase. |

---

### 3.2. `olist_order_items_dataset.csv` (Order Items Fact)
Grain: **One row per item line inside an order**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | No | Order identifier (Foreign Key to `olist_orders_dataset`). |
| `order_item_id` | INTEGER | No | Sequential item number within the same order (1, 2, 3...). Part of composite PK. |
| `product_id` | VARCHAR(32) | No | Product identifier (Foreign Key to `olist_products_dataset`). |
| `seller_id` | VARCHAR(32) | No | Seller identifier (Foreign Key to `olist_sellers_dataset`). |
| `shipping_limit_date` | DATETIME | No | Seller shipping deadline to hand the order over to the logistics partner. |
| `price` | DECIMAL(10,2) | No | Selling price per single item in Brazilian Real (BRL). |
| `freight_value` | DECIMAL(10,2) | No | Freight/shipping cost charged for this item in BRL. |

---

### 3.3. `olist_order_payments_dataset.csv` (Payments Fact)
Grain: **One row per payment attempt / transaction method**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `order_id` | VARCHAR(32) | No | Order identifier (Foreign Key to `olist_orders_dataset`). |
| `payment_sequential` | INTEGER | No | Sequence of payment attempt (e.g., 1 for card, 2 for voucher). |
| `payment_type` | VARCHAR(20) | No | Method of payment: `credit_card`, `boleto` (bank slip), `voucher`, `debit_card`. |
| `payment_installments` | INTEGER | No | Number of monthly installments chosen by customer (credit card). |
| `payment_value` | DECIMAL(10,2) | No | Total amount charged in this payment record in BRL. |

---

### 3.4. `olist_order_reviews_dataset.csv` (Reviews Fact)
Grain: **One row per customer review submission**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `review_id` | VARCHAR(32) | No | Unique identifier of the review record. |
| `order_id` | VARCHAR(32) | No | Order identifier (Foreign Key to `olist_orders_dataset`). |
| `review_score` | INTEGER | No | Customer satisfaction score from 1 (worst) to 5 (best). |
| `review_comment_title` | TEXT | Yes | Title of the written review (Portuguese). |
| `review_comment_message` | TEXT | Yes | Full feedback text left by the customer (Portuguese). |
| `review_creation_date` | DATETIME | No | Date when the satisfaction survey was sent to customer. |
| `review_answer_timestamp` | DATETIME | No | Timestamp of when customer submitted the survey response. |

---

### 3.5. `olist_customers_dataset.csv` (Customer Dimension)
Grain: **One row per transactional customer profile**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `customer_id` | VARCHAR(32) | No | Unique transaction customer key (Primary Key). |
| `customer_unique_id` | VARCHAR(32) | No | Natural unique identifier for the customer (tracks repeat purchases). |
| `customer_zip_code_prefix` | VARCHAR(5) | No | First 5 digits of Brazilian CEP zip code. |
| `customer_city` | VARCHAR(50) | No | City where the customer is located. |
| `customer_state` | VARCHAR(2) | No | 2-letter state abbreviation (e.g., `SP`, `RJ`, `MG`). |

---

### 3.6. `olist_products_dataset.csv` (Product Dimension)
Grain: **One row per distinct catalog product**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `product_id` | VARCHAR(32) | No | Unique product identifier (Primary Key). |
| `product_category_name` | VARCHAR(50) | Yes | Original Portuguese category name. |
| `product_name_lenght` | INTEGER | Yes | Character count of product name. |
| `product_description_lenght` | INTEGER | Yes | Character count of product description. |
| `product_photos_qty` | INTEGER | Yes | Number of product photos in the listing. |
| `product_weight_g` | INTEGER | Yes | Product weight in grams. |
| `product_length_cm` | INTEGER | Yes | Package length in centimeters. |
| `product_height_cm` | INTEGER | Yes | Package height in centimeters. |
| `product_width_cm` | INTEGER | Yes | Package width in centimeters. |

---

### 3.7. `product_category_name_translation.csv` (Translation Dimension)
Grain: **One row per category mapping**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `product_category_name` | VARCHAR(50) | No | Category name in Portuguese. |
| `product_category_name_english` | VARCHAR(50) | No | English translated category name for international reporting. |

---

### 3.8. `olist_sellers_dataset.csv` (Seller Dimension)
Grain: **One row per registered seller**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `seller_id` | VARCHAR(32) | No | Unique seller identifier (Primary Key). |
| `seller_zip_code_prefix` | VARCHAR(5) | No | First 5 digits of seller's zip code. |
| `seller_city` | VARCHAR(50) | No | City of seller operations. |
| `seller_state` | VARCHAR(2) | No | 2-letter state abbreviation. |

---

### 3.9. `olist_geolocation_dataset.csv` (Spatial Lookup)
Grain: **Raw coordinate points (1M+ rows) linked by 5-digit zip code**.

| Column | Data Type | Nullable? | Description |
|---|---|---|---|
| `geolocation_zip_code_prefix` | VARCHAR(5) | No | First 5 digits of Brazilian CEP zip code. |
| `geolocation_lat` | FLOAT | No | Latitude coordinate in decimal degrees. |
| `geolocation_lng` | FLOAT | No | Longitude coordinate in decimal degrees. |
| `geolocation_city` | VARCHAR(50) | No | City name reported for this coordinate point. |
| `geolocation_state` | VARCHAR(2) | No | 2-letter state code. |
