# Power BI Semantic Data Model & Architecture Guide
**Project:** E-Commerce Sales & Business Intelligence Analytics Platform  
**Author:** Nandini Patel (GitHub: [nandinipatel8011](https://github.com/nandinipatel8011))  
**Target Tool:** Power BI Desktop / Power BI Service  
**Model Architecture:** Multi-Fact Star-Constellation Schema  
**Target Datasets Directory:** `data/processed/powerbi/`  

---

## 1. Architectural Overview

The Power BI analytical model is designed as an enterprise **star-constellation schema**. Rather than collapsing all transactional data into a single wide, unmanageable flat table, transactions are segmented into dedicated fact tables by natural business process and granularity:
- **Order Headers** (`fact_orders`): High-level order lifecycle, fulfillment dates, and delivery delay metrics.
- **Order Items** (`fact_order_items`): Granular merchandise lines, item pricing, and freight charges.
- **Payments** (`fact_order_payments`): Tender types, installment plans, and transaction values.
- **Customer Reviews** (`fact_order_reviews`): Survey feedback ratings, response turnaround, and text indicators.

Surrounding these facts are four clean, pre-enriched dimension tables: `dim_date`, `dim_customers`, `dim_products`, and `dim_sellers`.

```mermaid
graph TD
    %% Dimensions
    dim_date["dim_date<br/>(1,827 rows)<br/>PK: date"]
    dim_cust["dim_customers<br/>(99,441 rows)<br/>PK: customer_id<br/>Natural: customer_unique_id"]
    dim_prod["dim_products<br/>(32,951 rows)<br/>PK: product_id"]
    dim_sell["dim_sellers<br/>(3,095 rows)<br/>PK: seller_id"]

    %% Facts
    fact_ord["fact_orders<br/>(99,441 rows)<br/>PK: order_id"]
    fact_itm["fact_order_items<br/>(112,650 rows)<br/>PK: (order_id, order_item_id)"]
    fact_pay["fact_order_payments<br/>(103,886 rows)<br/>PK: (order_id, payment_sequential)"]
    fact_rev["fact_order_reviews<br/>(99,224 rows)<br/>PK: (review_id, order_id)"]

    %% Relationships
    dim_date -->|1 : Many (Active: purchase_date)| fact_ord
    dim_date -.->|1 : Many (Inactive: lifecycle)| fact_ord
    dim_date -.->|1 : Many (Inactive: shipping_limit)| fact_itm
    dim_date -.->|1 : Many (Inactive: review_dates)| fact_rev

    dim_cust -->|1 : 1 (Single)| fact_ord
    fact_ord -->|1 : Many (Single)| fact_itm
    fact_ord -->|1 : Many (Single)| fact_pay
    fact_ord -->|1 : Many (Single)| fact_rev

    dim_prod -->|1 : Many (Single)| fact_itm
    dim_sell -->|1 : Many (Single)| fact_itm
```

### Architectural Tiering: Group A vs Group B
- **Group A (Main Canvas Model - 8 Tables)**:
  Imported directly into Power BI Desktop: `dim_date`, `dim_customers`, `dim_products`, `dim_sellers`, `fact_orders`, `fact_order_items`, `fact_order_payments`, `fact_order_reviews`.
- **Group B (Auxiliary Reference Only - Do NOT Import)**:
  `dim_geolocation.csv` (19,010 postal centroid coordinates) and the 6 Phase 5 benchmark query CSVs.
  *Design Rationale*: Pre-joining representative latitude and longitude coordinates into `dim_customers` eliminates the need to load the auxiliary 19,010-row lookup table into the Power BI memory space, keeping the semantic model light, fast, and responsive.

---

## 2. Table-by-Table Specifications & Granularity

### 2.1. `dim_date` (Calendar Dimension)
- **Granularity**: 1 row per calendar day.
- **Row Count**: 1,827 rows.
- **Coverage**: `2016-01-01` to `2020-12-31` (100% continuous, zero gaps).
- **Primary Key**: `date` (or `date_key`).
- **Columns**:
  - `date_key` (Int64): `20171124`
  - `date` (Date, format `YYYY-MM-DD`): Primary relationship join key.
  - `year` (Int64): `2017`
  - `quarter` (Int64): `4`
  - `quarter_name` (Text): `"Q4"`
  - `year_quarter` (Text): `"2017-Q4"`
  - `month` (Int64): `11`
  - `month_name` (Text): `"November"`
  - `month_short` (Text): `"Nov"`
  - `year_month` (Text): `"2017-11"`
  - `day` (Int64): `24`
  - `day_of_week` (Int64): `1` (Monday) to `7` (Sunday)
  - `day_name` (Text): `"Friday"`
  - `is_weekend` (Int64): `0` (weekday) or `1` (weekend)

### 2.2. `dim_customers` (Customer Dimension)
- **Granularity**: 1 row per order-scoped customer profile (`customer_id`).
- **Row Count**: 99,441 rows.
- **Distinct Real-World Buyers**: 96,096 unique `customer_unique_id` values.
- **Primary Key**: `customer_id`.
- **Enriched Attributes**:
  - `customer_id` (Text): Transactional customer profile key.
  - `customer_unique_id` (Text): Natural buyer key for distinct customer counting.
  - `customer_zip_code_prefix` (Int64): Brazilian postal code.
  - `customer_city` (Text): City name.
  - `customer_state` (Text): 2-letter state code (SP, RJ, MG, etc.).
  - `customer_lat` (Double): Centroid latitude coordinate.
  - `customer_lng` (Double): Centroid longitude coordinate.
  - `customer_segment` (Text): 8-cohort RFM segment name (e.g. `"Champions & Loyal"`, `"Lost / Inactive"`).
  - `r_score`, `f_score`, `m_score` (Int64): 1–5 quintile scores.
  - `rfm_code` (Text): Composite score (e.g. `"555"`, `"111"`).
  - `recency_days` (Int64): Days since last purchase relative to dataset cutoff.
  - `order_frequency` (Int64): Lifetime completed orders for this buyer.
  - `total_monetary_spend` (Decimal): Lifetime product revenue for this buyer.

> [!WARNING]
> **Cardinality & Counting Rule**: Repeat buyers appear multiple times in `dim_customers` (once per order). In Power BI, **NEVER** use `COUNTROWS(dim_customers)` as the real-world customer count. Always use `DISTINCTCOUNT(dim_customers[customer_unique_id])`.

### 2.3. `dim_products` (Product Dimension)
- **Granularity**: 1 row per unique catalog product.
- **Row Count**: 32,951 rows.
- **Primary Key**: `product_id`.
- **Enriched Attributes**:
  - `product_id` (Text): Unique product alphanumeric hash.
  - `product_category_name` (Text): Portuguese category name.
  - `product_category_name_english` (Text): English translated category.
  - `pareto_class` (Text): `"Core 80% (A)"` or `"Long Tail (B/C)"`.
  - `category_revenue_rank` (Int64): 1 to 72 category rank by gross merchandise revenue.
  - Physical specifications: `product_name_length`, `product_description_length`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `product_volume_cm3`.

### 2.4. `dim_sellers` (Seller Dimension)
- **Granularity**: 1 row per merchant / merchant location.
- **Row Count**: 3,095 rows.
- **Primary Key**: `seller_id`.
- **Columns**: `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state`.

### 2.5. `fact_orders` (Order Headers Fact)
- **Granularity**: 1 row per order.
- **Row Count**: 99,441 rows.
- **Primary Key**: `order_id`.
- **Foreign Keys**: `customer_id`.
- **Columns**:
  - `order_id` (Text): Unique order hash.
  - `customer_id` (Text): 1:1 join key to `dim_customers`.
  - `order_status` (Text): `"delivered"`, `"shipped"`, `"canceled"`, `"unavailable"`, `"invoiced"`, `"processing"`, `"created"`, `"approved"`.
  - Timestamps: `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`.
  - Date-Only Join Keys:
    - `order_purchase_date` (Active relationship to `dim_date[date]`)
    - `order_approved_date` (Inactive relationship)
    - `order_delivered_carrier_date_only` (Inactive relationship)
    - `order_delivered_customer_date_only` (Inactive relationship)
  - Logistics KPIs: `delivery_duration_days`, `delivery_delay_days`, `is_delayed` (0/1), `is_delivered` (0/1), `delivery_performance_bucket`.

### 2.6. `fact_order_items` (Order Line Items Fact)
- **Granularity**: 1 row per item within an order.
- **Row Count**: 112,650 rows.
- **Primary Key**: Composite `(order_id, order_item_id)`.
- **Foreign Keys**: `order_id` -> `fact_orders`, `product_id` -> `dim_products`, `seller_id` -> `dim_sellers`.
- **Columns**:
  - `order_id` (Text), `order_item_id` (Int64).
  - `product_id` (Text), `seller_id` (Text).
  - `shipping_limit_date` (Text), `shipping_limit_date_only` (Date, inactive link to `dim_date`).
  - `price` (Decimal): Item product price in BRL (Total = R$ 13,591,643.70).
  - `freight_value` (Decimal): Shipping fee allocated in BRL (Total = R$ 2,251,909.54).
  - `total_item_value` (Decimal): `price + freight_value` (Total = R$ 15,843,553.24).

### 2.7. `fact_order_payments` (Order Payments Fact)
- **Granularity**: 1 row per payment transaction split.
- **Row Count**: 103,886 rows.
- **Primary Key**: Composite `(order_id, payment_sequential)`.
- **Foreign Keys**: `order_id` -> `fact_orders`.
- **Columns**:
  - `order_id` (Text), `payment_sequential` (Int64).
  - `payment_type` (Text): `"credit_card"`, `"boleto"`, `"voucher"`, `"debit_card"`, `"not_defined"`.
  - `payment_installments` (Int64): Number of installment payments (1 to 24).
  - `payment_value` (Decimal): Recorded payment amount in BRL (Total = R$ 16,008,872.12).
  - `is_installment` (Int64): 1 if installments > 1 else 0.

### 2.8. `fact_order_reviews` (Order Reviews Fact)
- **Granularity**: 1 row per customer satisfaction survey response.
- **Row Count**: 99,224 rows.
- **Primary Key**: Composite `(review_id, order_id)`.
- **Foreign Keys**: `order_id` -> `fact_orders`.
- **Columns**:
  - `review_id` (Text), `order_id` (Text).
  - `review_score` (Int64): Rating from 1 (lowest) to 5 (highest).
  - Text Feedback: `review_comment_title`, `review_comment_message`, `has_comment_title` (0/1), `has_comment_message` (0/1).
  - Survey Dates: `review_creation_date`, `review_creation_date_only` (Date), `review_answer_timestamp`, `review_answer_date_only` (Date), `review_response_hours` (Decimal).

---

## 3. Relationships & Cardinality Configuration

The following table defines every relationship to configure in Power BI Desktop's **Model View**:

| From Table (Child) | From Column (FK) | To Table (Parent) | To Column (PK) | Cardinality | Cross Filter Direction | State | Business Purpose |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `dim_customers` | `customer_id` | `fact_orders` | `customer_id` | **1 : 1** | **Single** (`dim_customers` $\to$ `fact_orders`) | **Active** | Filters orders by customer geography & RFM |
| `dim_date` | `date` | `fact_orders` | `order_purchase_date` | **1 : Many** | **Single** (`dim_date` $\to$ `fact_orders`) | **Active** | Primary sales trend & calendar timeline |
| `dim_date` | `date` | `fact_orders` | `order_approved_date` | **1 : Many** | **Single** | *Inactive* | Analysis by payment approval date |
| `dim_date` | `date` | `fact_orders` | `order_delivered_carrier_date_only` | **1 : Many** | **Single** | *Inactive* | Analysis by seller dispatch date |
| `dim_date` | `date` | `fact_orders` | `order_delivered_customer_date_only` | **1 : Many** | **Single** | *Inactive* | Analysis by final delivery date |
| `dim_date` | `date` | `fact_orders` | `order_estimated_delivery_date` | **1 : Many** | **Single** | *Inactive* | Analysis by promise / SLA date |
| `fact_orders` | `order_id` | `fact_order_items` | `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_items`) | **Active** | Propagates date & customer filters to item lines |
| `fact_orders` | `order_id` | `fact_order_payments` | `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_payments`) | **Active** | Propagates date & customer filters to payments |
| `fact_orders` | `order_id` | `fact_order_reviews` | `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_reviews`) | **Active** | Propagates date & customer filters to reviews |
| `dim_products` | `product_id` | `fact_order_items` | `product_id` | **1 : Many** | **Single** (`dim_products` $\to$ `fact_order_items`) | **Active** | Filters items by product category & Pareto class |
| `dim_sellers` | `seller_id` | `fact_order_items` | `seller_id` | **1 : Many** | **Single** (`dim_sellers` $\to$ `fact_order_items`) | **Active** | Filters items by seller state & city |
| `dim_date` | `date` | `fact_order_items` | `shipping_limit_date_only` | **1 : Many** | **Single** | *Inactive* | Analysis by seller dispatch deadline |
| `dim_date` | `date` | `fact_order_reviews` | `review_creation_date_only` | **1 : Many** | **Single** | *Inactive* | Analysis by survey sent date |
| `dim_date` | `date` | `fact_order_reviews` | `review_answer_date_only` | **1 : Many** | **Single** | *Inactive* | Analysis by customer review submission date |

### Why Single Cross-Filtering Direction is Mandatory
- **Ambiguity Elimination**: In a multi-fact star constellation, bidirectional filtering creates circular filter propagation paths (e.g. `fact_order_items` filtering `fact_orders`, which filters `fact_order_payments`). This leads to unpredictable measure results and visual query failures.
- **Engine Performance**: The VertiPaq tabular storage engine optimizes 1-way single-direction relationships with maximum columnar compression. Single-direction filtering avoids expensive bi-directional query scans.

---

## 4. Filter Propagation Rules & Cross-Table Filtering

Understanding filter propagation is critical when building visuals in Phase 8:

```
[dim_date] --------+
                   | (Active: order_purchase_date)
                   v
[dim_customers] -> [fact_orders] 
                         |
                         +---> [fact_order_items] <--- [dim_products]
                         |           ^
                         |           +---------------- [dim_sellers]
                         +---> [fact_order_payments]
                         |
                         +---> [fact_order_reviews]
```

1. **Date & Customer Slicers**:
   - Selecting a date range or Brazilian customer state directly filters `fact_orders`.
   - Because `fact_orders` has active 1:Many relationships to `fact_order_items`, `fact_order_payments`, and `fact_order_reviews`, the filter naturally flows downstream to all three child fact tables.
2. **Product & Seller Slicers**:
   - Selecting a product category or seller state filters `fact_order_items`.
   - Because the relationship between `fact_orders` and `fact_order_items` is single-direction (`fact_orders` $\to$ `fact_order_items`), a product slicer does **not** automatically filter `fact_orders` or `fact_order_payments` across the canvas.
   - *Best Practice*: For product-filtered order counts or payment totals, use standard DAX pattern with `CALCULATE` or rely on item-level revenue metrics (`[Total Item Revenue]`), which naturally aggregate from `fact_order_items`.

---

## 5. Production DAX Measure Library

To maintain clean governance, all DAX measures should be stored inside a dedicated display folder or dedicated measures table (`_Measures`).

### 5.1. Financial Revenue Measures
```dax
// Pure merchandise revenue
Total Item Revenue = 
SUM(fact_order_items[price])

// Customer shipping charges collected
Total Freight Revenue = 
SUM(fact_order_items[freight_value])

// Total customer invoice amount
Freight-Inclusive Order Value = 
SUM(fact_order_items[total_item_value])

// Total recorded tender payments
Total Recorded Payment Value = 
SUM(fact_order_payments[payment_value])

// Empirical variance between recorded payments and invoices
Payment Value Variance = 
[Total Recorded Payment Value] - [Freight-Inclusive Order Value]

// Average merchandise value per order
Average Order Value = 
DIVIDE([Total Item Revenue], [Total Orders], 0)
```

### 5.2. Order & Customer Volume Measures
```dax
// Total orders placed
Total Orders = 
DISTINCTCOUNT(fact_orders[order_id])

// Total merchandise line items sold
Total Units Sold = 
COUNTROWS(fact_order_items)

// Distinct real-world human buyers (MANDATORY: Never use COUNTROWS)
Unique Real-World Buyers = 
DISTINCTCOUNT(dim_customers[customer_unique_id])

// Buyers with exactly 1 order
Single-Order Buyers = 
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    dim_customers[order_frequency] = 1
)

// Buyers with 2 or more orders
Repeat Buyers = 
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    dim_customers[order_frequency] > 1
)

// Percentage of customer base with repeat purchases
Repeat Purchase Rate = 
DIVIDE([Repeat Buyers], [Unique Real-World Buyers], 0)
```

### 5.3. Lifecycle Date Measures (Inactive Relationships)
```dax
// Orders by payment approval date
Orders Approved = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_approved_date], dim_date[date])
)

// Orders by seller carrier dispatch date
Orders Dispatched to Carrier = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_delivered_carrier_date_only], dim_date[date])
)

// Orders by customer delivery receipt date
Orders Delivered to Customer = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_delivered_customer_date_only], dim_date[date])
)

// Orders by estimated delivery promise date
Orders Estimated Delivery = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_estimated_delivery_date], dim_date[date])
)
```

### 5.4. Delivery Performance & Fulfillment SLA Measures
```dax
// Count of completed delivered orders
Total Delivered Orders = 
CALCULATE(
    [Total Orders],
    fact_orders[is_delivered] = 1
)

// Count of delayed orders
Orders Delayed = 
CALCULATE(
    [Total Orders],
    fact_orders[is_delayed] = 1
)

// On-time fulfillment percentage (Delivered order denominator)
On-Time Delivery Rate = 
DIVIDE(
    CALCULATE([Total Orders], fact_orders[is_delayed] = 0, fact_orders[is_delivered] = 1),
    [Total Delivered Orders],
    0
)

// Late delivery percentage
Late Delivery Rate = 
DIVIDE([Orders Delayed], [Total Delivered Orders], 0)

// Average transit days from purchase to customer delivery
Avg Delivery Duration Days = 
AVERAGE(fact_orders[delivery_duration_days])

// Average days delivered past estimated SLA (for late orders)
Avg Delivery Delay Days = 
CALCULATE(
    AVERAGE(fact_orders[delivery_delay_days]),
    fact_orders[is_delayed] = 1
)
```

### 5.5. Customer Feedback & Review Experience Measures
```dax
// Total customer survey reviews recorded
Total Reviews = 
COUNTROWS(fact_order_reviews)

// Overall average customer satisfaction rating (1.00 to 5.00)
Average Review Score = 
AVERAGE(fact_order_reviews[review_score])

// 5-Star review count
5-Star Reviews = 
CALCULATE([Total Reviews], fact_order_reviews[review_score] = 5)

// 1-Star review count
1-Star Reviews = 
CALCULATE([Total Reviews], fact_order_reviews[review_score] = 1)

// Percentage of negative (1-star) ratings
Negative Review Rate = 
DIVIDE([1-Star Reviews], [Total Reviews], 0)
```

---

## 6. Step-by-Step Power BI Desktop Import Guide (Phase 8 Readiness)

When initiating Phase 8 dashboard development in Power BI Desktop:

1. **Import Group A Datasets**:
   - In Power BI Desktop, click **Get Data** $\to$ **Text/CSV**.
   - Navigate to `data/processed/powerbi/` and import the **8 Group A CSV files**:
     1. `dim_date.csv`
     2. `dim_customers.csv`
     3. `dim_products.csv`
     4. `dim_sellers.csv`
     5. `fact_orders.csv`
     6. `fact_order_items.csv`
     7. `fact_order_payments.csv`
     8. `fact_order_reviews.csv`
   - **Do NOT import** `dim_geolocation.csv` or the 6 Phase 5 query CSVs into the active model canvas.

2. **Power Query Column Type Verification**:
   - Ensure `date` columns are formatted as **Date** (`YYYY-MM-DD`).
   - Ensure monetary metrics (`price`, `freight_value`, `total_item_value`, `payment_value`) are formatted as **Fixed Decimal Number** (Currency).
   - Ensure postal codes and integer IDs are set to **Text** if not participating in arithmetic operations.

3. **Configure Date Dimension**:
   - Right-click `dim_date` $\to$ **Mark as Date Table** $\to$ Select column `date`.

4. **Establish Model Relationships**:
   - Switch to **Model View** and build the 13 relationships specified in Section 3.
   - Verify that all active relationships use **Single** cross-filter direction.
   - Verify that `dim_customers` to `fact_orders` is configured as **1 : 1**.

5. **Deploy Measures**:
   - Create a blank table named `_Measures` via **Enter Data**.
   - Add the DAX measures from Section 5.
