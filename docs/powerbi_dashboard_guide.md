# Power BI Executive Dashboard Implementation Guide
**Project:** E-Commerce Sales & Business Intelligence Analytics Platform  
**Author:** Nandini Patel (GitHub: [nandinipatel8011](https://github.com/nandinipatel8011))  
**Target Tool:** Power BI Desktop (Free / Pro / Premium)  
**Model Architecture:** Star-Constellation Relational Schema (14 Relationships: 7 Active, 7 Inactive)  
**Source Directory:** `data/processed/powerbi/`  
**Guide Scope:** Detailed, beginner-friendly manual for assembling the 5-page Executive BI Dashboard in Power BI Desktop.

---

## Executive Summary & Architecture Overview

This guide provides end-to-end, step-by-step instructions for constructing the executive Power BI dashboard in **Power BI Desktop**. The analytical semantic model is pre-built and validated across Phases 3–7, ensuring that data transformations, cleansing, and referential integrity have already been completed upstream in Python and SQLite.

### Star-Constellation Schema Blueprint

The semantic model consists of **8 core tables** connected via **14 relationships** (7 active, 7 inactive):

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

    %% Active Relationships (Solid)
    dim_date -->|1 : Many (Active: order_purchase_date)| fact_ord
    dim_cust -->|1 : 1 (Active: customer_id)| fact_ord
    fact_ord -->|1 : Many (Active: order_id)| fact_itm
    fact_ord -->|1 : Many (Active: order_id)| fact_pay
    fact_ord -->|1 : Many (Active: order_id)| fact_rev
    dim_prod -->|1 : Many (Active: product_id)| fact_itm
    dim_sell -->|1 : Many (Active: seller_id)| fact_itm

    %% Inactive Lifecycle Relationships (Dashed)
    dim_date -.->|1 : Many (Inactive: order_approved_date)| fact_ord
    dim_date -.->|1 : Many (Inactive: order_delivered_carrier_date_only)| fact_ord
    dim_date -.->|1 : Many (Inactive: order_delivered_customer_date_only)| fact_ord
    dim_date -.->|1 : Many (Inactive: order_estimated_delivery_date)| fact_ord
    dim_date -.->|1 : Many (Inactive: shipping_limit_date_only)| fact_itm
    dim_date -.->|1 : Many (Inactive: review_creation_date_only)| fact_rev
    dim_date -.->|1 : Many (Inactive: review_answer_date_only)| fact_rev
```

### The 8 Core Semantic Tables (Group A)
Only the following **eight CSV files** located in `data/processed/powerbi/` should be imported into the Power BI model:
1. `dim_date.csv` (1,827 rows) — Continuous calendar dimension (`2016-01-01` to `2020-12-31`).
2. `dim_customers.csv` (99,441 rows) — Order-scoped customer dimension enriched with RFM scores, lifetime metrics, and postal coordinates.
3. `dim_products.csv` (32,951 rows) — Product dimension enriched with Pareto classification and category revenue rank across all 74 catalog categories.
4. `dim_sellers.csv` (3,095 rows) — Merchant location and seller dimension.
5. `fact_orders.csv` (99,441 rows) — Order headers fact table (1:1 join with `dim_customers`).
6. `fact_order_items.csv` (112,650 rows) — Line-item merchandise fact table with item price and freight.
7. `fact_order_payments.csv` (103,886 rows) — Financial payment transaction splits and installment plans.
8. `fact_order_reviews.csv` (99,224 rows) — Customer survey review ratings and turnaround hours.

> [!CAUTION]
> **Files to EXCLUDE from Main Model Canvas**:
> - `dim_geolocation.csv`: Do NOT import. Representative postal centroid coordinates (`customer_lat`, `customer_lng`) have already been pre-joined into `dim_customers.csv`. Importing the auxiliary 19,010-row file creates unnecessary memory overhead.
> - The 6 Phase 5 benchmark query marts (`monthly_sales_trends.csv`, `category_performance.csv`, etc.): Do NOT import. These are static benchmark query exports used for validation, not semantic model tables.

---

## Section 1: Data Ingestion & Power Query Configuration

### Step 1.1: Import CSV Files
1. Launch **Power BI Desktop**.
2. On the **Home** ribbon, click **Get Data** $\to$ **Text/CSV**.
3. Browse to the project folder:
   `D:\DataAnalyticsProjects\Project1_EcommerceAnalytics\data\processed\powerbi\`
4. Select each of the **8 Group A CSV files** one by one.
5. In the preview window:
   - File Origin: **65001: Unicode (UTF-8)**.
   - Delimiter: **Comma**.
   - Data Type Detection: **Based on first 200 rows**.
   - Click **Transform Data** (do not click Load immediately).

### Step 1.2: Verify Data Types in Power Query Editor
Review each table in Power Query to ensure data types are correctly cast before loading. In particular, postal code prefixes must be formatted as **Text** to preserve leading zeros in Brazilian 5-digit postal codes:

| Table Name | Column Name(s) | Target Data Type | Format Setting | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `dim_date` | `date` | **Date** | `YYYY-MM-DD` | Primary join key |
| `dim_date` | `date_key`, `year`, `quarter`, `month`, `day`, `day_of_week`, `is_weekend` | **Whole Number** (Int64) | Integer | Calendar attributes |
| `dim_date` | `quarter_name`, `year_quarter`, `month_name`, `month_short`, `year_month`, `day_name` | **Text** | String | Visual labels |
| `dim_customers` | `customer_id`, `customer_unique_id`, `customer_city`, `customer_state`, `customer_segment` | **Text** | String | Profile & geography |
| `dim_customers` | `customer_zip_code_prefix` | **Text** | Postal Code | **Format as Text** to preserve leading zeros (e.g., `01001`) |
| `dim_customers` | `r_score`, `f_score`, `m_score`, `rfm_code`, `recency_days`, `order_frequency` | **Whole Number** (Int64) | Integer | RFM scores |
| `dim_customers` | `customer_lat`, `customer_lng` | **Decimal Number** | Float / Coordinates | Map coordinates |
| `dim_customers` | `total_monetary_spend` | **Fixed Decimal Number** | Currency (R$) | Buyer spend |
| `dim_products` | `product_id`, `product_category_name`, `product_category_name_english`, `pareto_class` | **Text** | String | 74 distinct categories |
| `dim_products` | `category_revenue_rank`, `product_photos_qty` | **Whole Number** (Int64) | Integer | Ranks & counts |
| `dim_products` | `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `product_volume_cm3` | **Decimal Number** | Float | Specifications |
| `dim_sellers` | `seller_id`, `seller_city`, `seller_state` | **Text** | String | Merchant profile |
| `dim_sellers` | `seller_zip_code_prefix` | **Text** | Postal Code | **Format as Text** to preserve leading zeros |
| `fact_orders` | `order_id`, `customer_id`, `order_status`, `delivery_performance_bucket` | **Text** | String | Header keys & 8 statuses |
| `fact_orders` | `order_purchase_date`, `order_approved_date`, `order_delivered_carrier_date_only`, `order_delivered_customer_date_only`, `order_estimated_delivery_date` | **Date** | `YYYY-MM-DD` | Date relationships |
| `fact_orders` | `order_purchase_year`, `order_purchase_month`, `is_delayed`, `is_delivered` | **Whole Number** | Integer / Boolean | Flags |
| `fact_orders` | `delivery_duration_days`, `delivery_delay_days` | **Decimal Number** | Float | Logistics durations |
| `fact_order_items` | `order_id`, `product_id`, `seller_id` | **Text** | String | Child fact keys |
| `fact_order_items` | `order_item_id` | **Whole Number** (Int64) | Integer | Line sequence |
| `fact_order_items` | `shipping_limit_date_only` | **Date** | `YYYY-MM-DD` | Inactive date join |
| `fact_order_items` | `price`, `freight_value`, `total_item_value` | **Fixed Decimal Number** | Currency (R$) | Item financial metrics |
| `fact_order_payments`| `order_id`, `payment_type` | **Text** | String | Tender methods |
| `fact_order_payments`| `payment_sequential`, `payment_installments`, `is_installment` | **Whole Number** (Int64) | Integer | Payment splits |
| `fact_order_payments`| `payment_value` | **Fixed Decimal Number** | Currency (R$) | Transaction tender value |
| `fact_order_reviews` | `review_id`, `order_id`, `review_comment_title`, `review_comment_message` | **Text** | String | Review feedback |
| `fact_order_reviews` | `review_score`, `has_comment_title`, `has_comment_message` | **Whole Number** (Int64) | Integer | Rating (1–5) & flags |
| `fact_order_reviews` | `review_creation_date_only`, `review_answer_date_only` | **Date** | `YYYY-MM-DD` | Survey & answer dates |
| `fact_order_reviews` | `review_response_hours` | **Decimal Number** | Float | Response turnaround |

6. Click **Close & Apply** on the Home ribbon.

### Step 1.3: Set Date Table Designation
1. In the **Data** pane on the right, right-click `dim_date`.
2. Select **Mark as Date Table** $\to$ **Mark as Date Table**.
3. In the dialog, select `date` as the Date column.
4. Verify that "Validated successfully" appears $\to$ click **OK**.

---

## Section 2: Model Relationships & Cardinality Configuration

Switch to **Model View** (icon on the far left). Drag and drop columns to establish the following **14 relationships** (**7 active**, **7 inactive**):

| # | From Table (Child) | From Column (FK) | To Table (Parent) | To Column (PK) | Cardinality | Cross Filter | State | Description |
| :-: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | `dim_customers` | `customer_id` | `fact_orders` | `customer_id` | **1 : 1** | **Single** (`dim_customers` $\to$ `fact_orders`) | **Active** | Primary customer profile join |
| **2** | `dim_date` | `date` | `fact_orders` | `order_purchase_date` | **1 : Many** | **Single** (`dim_date` $\to$ `fact_orders`) | **Active** | Primary sales timeline |
| **3** | `dim_date` | `date` | `fact_orders` | `order_approved_date` | **1 : Many** | **Single** | *Inactive* | Payment approval timeline |
| **4** | `dim_date` | `date` | `fact_orders` | `order_delivered_carrier_date_only`| **1 : Many** | **Single** | *Inactive* | Carrier dispatch timeline |
| **5** | `dim_date` | `date` | `fact_orders` | `order_delivered_customer_date_only`| **1 : Many** | **Single** | *Inactive* | Final customer delivery timeline |
| **6** | `dim_date` | `date` | `fact_orders` | `order_estimated_delivery_date` | **1 : Many** | **Single** | *Inactive* | Estimated SLA timeline |
| **7** | `fact_orders` | `order_id` | `fact_order_items` | `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_items`) | **Active** | Order items bridge |
| **8** | `fact_orders` | `order_id` | `fact_order_payments`| `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_payments`)| **Active** | Payments bridge |
| **9** | `fact_orders` | `order_id` | `fact_order_reviews` | `order_id` | **1 : Many** | **Single** (`fact_orders` $\to$ `fact_order_reviews`) | **Active** | Reviews bridge |
| **10** | `dim_products` | `product_id` | `fact_order_items` | `product_id` | **1 : Many** | **Single** (`dim_products` $\to$ `fact_order_items`)| **Active** | Product category & Pareto |
| **11** | `dim_sellers` | `seller_id` | `fact_order_items` | `seller_id` | **1 : Many** | **Single** (`dim_sellers` $\to$ `fact_order_items`) | **Active** | Seller merchant geography |
| **12** | `dim_date` | `date` | `fact_order_items` | `shipping_limit_date_only` | **1 : Many** | **Single** | *Inactive* | Seller shipping deadline |
| **13** | `dim_date` | `date` | `fact_order_reviews` | `review_creation_date_only` | **1 : Many** | **Single** | *Inactive* | Survey creation timeline |
| **14** | `dim_date` | `date` | `fact_order_reviews` | `review_answer_date_only` | **1 : Many** | **Single** | *Inactive* | Customer review answer timeline |

### Core Modeling Principles
1. **Never Enable Bidirectional Filtering**: All relationships must have **Single** cross-filter direction. Bidirectional filtering causes circular filter paths and inflates calculations in multi-fact schemas.
2. **Never Create Fact-to-Fact Relationships**: Do not join `fact_order_items` directly to `fact_order_payments` or `fact_order_reviews`. The `fact_orders` header table acts as the unified bridge.
3. **1:1 Customer-to-Order Cardinality**: Both tables have exactly 99,441 unique keys. Set cross-filtering from `dim_customers` to `fact_orders`.

---

## Section 3: Centralized DAX Measures Library

To keep measures organized, create a dedicated table:
1. On the **Home** ribbon, click **Enter Data**.
2. Name the table `_Measures` and click **Load**.
3. Create each of the following beginner-friendly measures inside `_Measures`.

### 3.1. Financial & Revenue Measures
```dax
// Pure merchandise revenue (excludes shipping charges)
Total Item Revenue = 
SUM(fact_order_items[price])

// Total shipping fees paid by customers
Total Freight Revenue = 
SUM(fact_order_items[freight_value])

// Total invoice amount billed to customers (Items + Shipping)
Freight-Inclusive Order Value = 
SUM(fact_order_items[total_item_value])

// Total financial tender value processed in payment transactions
Total Recorded Payment Value = 
SUM(fact_order_payments[payment_value])

// Empirical variance between payment ledger and invoiced order lines
Payment Value Variance = 
[Total Recorded Payment Value] - [Freight-Inclusive Order Value]

// Average merchandise value per order placed platform-wide
Average Order Value = 
DIVIDE([Total Item Revenue], [Total Orders], 0)

// Average freight charged per order placed platform-wide
Average Freight per Order = 
DIVIDE([Total Freight Revenue], [Total Orders], 0)
```

### 3.2. Order & Volume Measures (Overall vs. Product-Context)
```dax
// Total orders placed platform-wide (from fact_orders)
Total Orders = 
DISTINCTCOUNT(fact_orders[order_id])

// Total physical items sold
Total Units Sold = 
COUNTROWS(fact_order_items)

// Platform-Wide Benchmark: Average item count across all orders placed (112,650 items / 99,441 orders = 1.13)
Average Units per Order = 
DIVIDE([Total Units Sold], [Total Orders], 0)

// Category/Product Context: Orders containing selected products
// Under single-direction filtering, dim_products filters fact_order_items, not fact_orders.
// Use this measure for all product category order counts!
Orders Containing Selected Products = 
DISTINCTCOUNT(fact_order_items[order_id])

// Category-Level Average Order Value: Denominator uses orders containing selected products
Average Product Order Value = 
DIVIDE([Total Item Revenue], [Orders Containing Selected Products], 0)

// Category/Product Context: Average units sold per order containing selected products
// When analyzing specific categories or products, this measure uses Orders Containing Selected Products
// as the denominator, accurately calculating basket depth for the filtered items.
Average Product Units per Order = 
DIVIDE([Total Units Sold], [Orders Containing Selected Products], 0)
```

### 3.3. Customer Population, Retention & Spend Measures
To create the Single-Order vs. Repeat Buyer visual legend, add a calculated column to `dim_customers`:

```dax
// Calculated Column in dim_customers table:
Customer Type = 
IF(
    dim_customers[order_frequency] > 1,
    "Repeat Buyer",
    "Single-Order Buyer"
)
```

Now create the customer measures in `_Measures`:
```dax
// All-Time Platform Customer Reach (independent of date slicers)
// Evaluates total distinct real-world buyers across the entire multi-year platform history (96,096)
// MANDATORY: Never use COUNTROWS on dim_customers because repeat buyers have multiple profiles.
Unique Real-World Buyers = 
DISTINCTCOUNT(dim_customers[customer_unique_id])

// Date-Responsive Active Real-World Buyers in the Selected Context:
// Because dim_customers -> fact_orders is single-direction, date filters on dim_date
// filter fact_orders, but do not automatically propagate backwards to dim_customers.
// TREATAS passes the active fact_orders[customer_id] values into dim_customers[customer_id],
// accurately counting distinct real-world buyers active in the selected period.
Active Buyers in Selected Period = 
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    TREATAS(
        VALUES(fact_orders[customer_id]),
        dim_customers[customer_id]
    )
)

// Customers who have placed exactly 1 order (All-Time)
Single-Order Buyers = 
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    dim_customers[order_frequency] = 1
)

// Customers who have placed 2 or more orders (All-Time)
Repeat Buyers = 
CALCULATE(
    DISTINCTCOUNT(dim_customers[customer_unique_id]),
    dim_customers[order_frequency] > 1
)

// Percentage of customer base with repeat purchases (consistent KPI name: 2,997 / 96,096 = 3.12%)
Repeat Purchase Rate = 
DIVIDE([Repeat Buyers], [Unique Real-World Buyers], 0)

// Average merchandise spend per active buyer in the selected date/filter context
Average Merchandise Revenue per Active Buyer = 
DIVIDE([Total Item Revenue], [Active Buyers in Selected Period], 0)
```

> [!NOTE]
> **Single-Direction Date Filter Propagation & Buyer Count Mechanics**:
> - **Filter Path Architecture**: The calendar dimension `dim_date[date]` filters `fact_orders[order_purchase_date]`. The customer dimension `dim_customers` connects to `fact_orders` via a 1:1 relationship with a **Single** cross-filter direction (`dim_customers` $\to$ `fact_orders`). Consequently, date slicers applied to `dim_date` filter `fact_orders`, but do **not** propagate backwards to filter `dim_customers`.
> - **All-Time vs. Date-Filtered Buyer Measures**:
>   - `[Unique Real-World Buyers]` counts distinct `customer_unique_id` in `dim_customers`. Because date filters do not reach `dim_customers`, this measure remains at the all-time platform total of **96,096 buyers** regardless of date slicer selections.
>   - `[Active Buyers in Selected Period]` uses `TREATAS(VALUES(fact_orders[customer_id]), dim_customers[customer_id])` to pass the filtered order customer keys into the customer dimension, accurately returning the count of distinct buyers who placed orders during the selected period.
>   - *Example (November 2017 Peak Month)*:
>     - Total Item Revenue = **R$ 1,010,271.37** | Total Orders = **7,544**.
>     - `[Unique Real-World Buyers]` = 96,096 (All-time platform reach).
>     - `[Active Buyers in Selected Period]` = **7,430 buyers** (Unique buyers placing orders in Nov 2017).
>     - `[Average Merchandise Revenue per Active Buyer]` = $\text{R\$ } 1,010,271.37 / 7,430 = \mathbf{\text{R\$ } 135.97}$.
>     - A naive formula `DIVIDE([Total Item Revenue], [Unique Real-World Buyers], 0)` would incorrectly divide Nov 2017 revenue by all 96,096 all-time buyers, producing an erroneous figure of R$ 10.51.
>   - *All-Time Platform Scope*:
>     - When no date slicer is applied, `[Active Buyers in Selected Period]` equals `[Unique Real-World Buyers]` (**96,096 buyers**), yielding $\text{R\$ } 13,591,643.70 / 96,096 = \mathbf{\text{R\$ } 141.44}$ per buyer. It is an empirical spend-per-active-buyer metric, not a predictive multi-year Cohort LTV.

### 3.4. Buyer-Level RFM Averages (Correct Distinct-Buyer Weighting)
Because repeat buyers possess multiple rows in `dim_customers` (one row per order-scoped profile), taking a naive row-based average (`AVERAGE(dim_customers[recency_days])`) gives repeat buyers disproportionate weight.

To ensure each real-world buyer (`customer_unique_id`) contributes **exactly once** to segment averages, use the `AVERAGEX(VALUES(...))` pattern:

```dax
// Average days since last purchase across distinct real-world buyers in the cohort
Average Recency Days per Buyer = 
AVERAGEX(
    VALUES(dim_customers[customer_unique_id]),
    CALCULATE(MAX(dim_customers[recency_days]))
)

// Average lifetime orders placed across distinct real-world buyers in the cohort
Average Order Frequency per Buyer = 
AVERAGEX(
    VALUES(dim_customers[customer_unique_id]),
    CALCULATE(MAX(dim_customers[order_frequency]))
)
```

*How this works*: `VALUES(dim_customers[customer_unique_id])` evaluates the distinct set of buyers within the segment. For each distinct buyer, `CALCULATE(MAX(...))` extracts their single recency/frequency value, and `AVERAGEX` computes the unweighted arithmetic mean across buyers, exactly matching the Phase 5/6 SQL benchmarks.

### 3.5. Pareto Category Cumulative Measures
To construct the Pareto 80/20 curve on Page 2, add the following DAX measures:

```dax
// Cumulative item revenue summing categories up to the current category rank
// Uses ALL(dim_products) to clear category and Pareto tier slicers, guaranteeing that
// categories from rank 1 to CurrentRank are always accumulated across the global catalog.
Cumulative Category Item Revenue = 
VAR CurrentRank = SELECTEDVALUE(dim_products[category_revenue_rank])
RETURN
CALCULATE(
    [Total Item Revenue],
    FILTER(
        ALL(dim_products),
        dim_products[category_revenue_rank] <= CurrentRank
    )
)

// Cumulative share of total platform merchandise revenue (Global Platform Denominator: R$ 13,591,643.70)
Cumulative Revenue Pct = 
VAR TotalPlatformRevenue = CALCULATE([Total Item Revenue], ALL(dim_products))
RETURN
DIVIDE([Cumulative Category Item Revenue], TotalPlatformRevenue, 0)

// Dynamic Top Category Label (dynamically updates when filters are applied)
Top Category Label = 
VAR TopCat = 
    TOPN(
        1,
        VALUES(dim_products[product_category_name_english]),
        [Total Item Revenue],
        DESC
    )
VAR TopRev = 
    CALCULATE([Total Item Revenue], TopCat)
RETURN
    CONCATENATEX(TopCat, dim_products[product_category_name_english]) & " (" & FORMAT(TopRev, "R$ #,##0.00") & ")"
```

> [!NOTE]
> **Global Pareto Ranking & Slicer Behavior**:
> - The Pareto cumulative curve is defined globally across all 74 catalog categories, anchored by the platform total merchandise revenue denominator of **R$ 13,591,643.70**.
> - By applying `ALL(dim_products)` in both the numerator filter table and the denominator, the cumulative revenue percentage remains mathematically stable even if category or tier slicers are selected:
>   - *Unfiltered Canvas*: Displays all 74 categories in rank order, with cumulative share rising from 9.26% (`health_beauty`, rank 1) to **79.62%** at rank 17 (`Core 80% (A)` threshold), reaching exactly 100.00% at rank 74.
>   - *When Slicing by Pareto Tier (`Core 80% (A)`)*: The visual displays the 17 core category columns, and the cumulative line tracks smoothly from 9.26% to 79.62%.
>   - *When Slicing by Pareto Tier (`Long Tail (B/C)`)*: The visual displays the 57 long-tail category columns, while the cumulative percentage continues from 80.20% (rank 18) up to 100.00% (rank 74). The percentage does **not** reset to 0%, preserving its global catalog context.
>   - *Power BI Desktop Best Practice*: To ensure the full Pareto curve remains visible for comparison when users explore specific categories, configure **Format** $\to$ **Edit Interactions** so the Pareto visual is not filtered by category slicers.

> [!TIP]
> **Power BI Sorting Step for Pareto Charts**:
> By default, Power BI sorts text categories alphabetically. To sort `product_category_name_english` in revenue order:
> 1. In the **Data** pane, select column `product_category_name_english` in `dim_products`.
> 2. On the **Column tools** ribbon, click **Sort by column** $\to$ select `category_revenue_rank`.

### 3.6. Delivery & Fulfillment SLA Measures
```dax
// Total orders with official delivered lifecycle status (from order_status)
// Counts all 96,478 orders officially recorded as order_status = "delivered"
Total Delivered Orders = 
CALCULATE(
    [Total Orders],
    fact_orders[order_status] = "delivered"
)

// Delivered orders with recorded customer delivery timestamp (Strict Eligible SLA Cohort = 96,470)
// Explicitly enforces both delivered status and a nonblank customer delivery date.
// (Excludes 8 delivered orders lacking delivery timestamps and 6 canceled orders with timestamps).
Delivered Orders with Delivery Date = 
CALCULATE(
    [Total Orders],
    fact_orders[order_status] = "delivered",
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Eligible delivered orders in current delivery bucket (used in Page 5 Visual 2 and Visual 4)
// Explicitly enforces both delivered status and a nonblank customer delivery date.
// Guarantees that timeliness column bars and delay rating trends reflect only the strict 96,470 delivered cohort.
Delivered Orders in Bucket = 
CALCULATE(
    [Total Orders],
    fact_orders[order_status] = "delivered",
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Delivered orders arriving on or before estimated SLA promise date (delivery_delay_days <= 0)
// Explicitly enforces both delivered status and a nonblank customer delivery date (88,644 orders).
Orders On-Time = 
CALCULATE(
    [Total Orders],
    fact_orders[order_status] = "delivered",
    fact_orders[is_delayed] = 0,
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Delivered orders arriving past estimated SLA promise date (delivery_delay_days > 0)
// Explicitly enforces both delivered status and a nonblank customer delivery date (7,826 orders).
Orders Delayed = 
CALCULATE(
    [Total Orders],
    fact_orders[order_status] = "delivered",
    fact_orders[is_delayed] = 1,
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// On-time fulfillment percentage (Evaluated strictly on eligible delivered cohort: 88,644 / 96,470 = 91.89%)
On-Time Delivery Rate = 
DIVIDE([Orders On-Time], [Delivered Orders with Delivery Date], 0)

// Late delivery percentage (Evaluated strictly on eligible delivered cohort: 7,826 / 96,470 = 8.11%)
Late Delivery Rate = 
DIVIDE([Orders Delayed], [Delivered Orders with Delivery Date], 0)

// Average transit duration in days from purchase to customer delivery (Eligible delivered orders with timestamps)
// Explicitly enforces both delivered status and a nonblank customer delivery date (12.56 days avg).
Avg Delivery Duration Days = 
CALCULATE(
    AVERAGE(fact_orders[delivery_duration_days]),
    fact_orders[order_status] = "delivered",
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Average days delivered past estimated SLA (Calculated strictly for late delivered orders with timestamps)
// Explicitly enforces both delivered status and a nonblank customer delivery date (9.55 days avg).
Avg Delivery Delay Days = 
CALCULATE(
    AVERAGE(fact_orders[delivery_delay_days]),
    fact_orders[order_status] = "delivered",
    fact_orders[is_delayed] = 1,
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Average customer review score for eligible delivered orders in current bucket
// Explicitly enforces both delivered status and a nonblank customer delivery date.
// Used on Page 5 Visual 4 to track satisfaction across delivery timeliness buckets.
Average Review Score for Delivered Orders = 
CALCULATE(
    [Average Review Score],
    fact_orders[order_status] = "delivered",
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)

// Percentage of customer reviews receiving a 1-star rating for eligible delivered orders in current bucket
// Explicitly enforces both delivered status and a nonblank customer delivery date.
// Used on Page 5 Visual 4 to track 1-star dissatisfaction escalation across delivery timeliness buckets.
Negative Review Rate for Delivered Orders = 
CALCULATE(
    [Negative Review Rate],
    fact_orders[order_status] = "delivered",
    NOT(ISBLANK(fact_orders[order_delivered_customer_date_only]))
)
```

> [!IMPORTANT]
> **Delivery Population Disambiguation (99,441 Order Reconciliation)**:
> 1. **Delivered-Status Orders**: **96,478 orders** (97.02% of all 99,441 orders) have `order_status = "delivered"`.
> 2. **Delivered Orders with Usable Timestamps**: **96,470 orders** (99.99% of delivered orders) have a valid `order_delivered_customer_date`. This is the strict, eligible population for SLA timeliness, duration (12.56 days avg), delay (9.55 days avg when late), and on-time rate (91.89%).
> 3. **Delivered Orders Missing Timestamps**: Exactly **8 orders** have `order_status = "delivered"` but NULL `order_delivered_customer_date` (Order IDs: `2d1e2d...`, `f5dd62...`, `2ebdfc...`, `e69f75...`, `0d3268...`, `2d858f...`, `ab7c89...`, `20edc8...`). Because no delivery receipt was timestamped, their transit duration and delay days cannot be evaluated.
> 4. **Canceled Orders with Recorded Timestamps**: Exactly 6 orders have `order_status = "canceled"` yet record an `order_delivered_customer_date` (Order IDs: `1950d7...`, `dabf2b...`, `770d33...`, `8beb59...`, `65d1e2...`, `2c45c3...`). The dataset does not establish why these records contain both a canceled status and a delivery timestamp. They are strictly excluded from delivered-order SLA metrics.
> 5. **Orders Without Delivery Timestamps**: Exactly **2,965 orders** lack a delivery timestamp (2,957 non-delivered orders + 8 delivered-status orders). Because they lack recorded delivery timestamps, they are strictly excluded from the 96,470-order SLA cohort and its delivery timeliness bucket visual.
> - **Total Orders Reconciled**: $96,476 \text{ with timestamps } + 2,965 \text{ without timestamps} = \mathbf{99,441 \text{ orders}}$ (100.0%).

### 3.7. Customer Feedback & Review Measures
```dax
// Total survey reviews submitted
Total Reviews = 
COUNTROWS(fact_order_reviews)

// Overall average customer satisfaction rating (1.00 to 5.00)
Average Review Score = 
AVERAGE(fact_order_reviews[review_score])

// 5-Star (excellent) customer reviews
5-Star Reviews = 
CALCULATE([Total Reviews], fact_order_reviews[review_score] = 5)

// 1-Star (negative) customer reviews
1-Star Reviews = 
CALCULATE([Total Reviews], fact_order_reviews[review_score] = 1)

// Percentage of customer reviews receiving a 1-star rating
Negative Review Rate = 
DIVIDE([1-Star Reviews], [Total Reviews], 0)
```

### 3.8. Lifecycle Date Measures (Inactive Relationships via `USERELATIONSHIP`)
```dax
// Orders analyzed by payment approval date
Orders Approved = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_approved_date], dim_date[date])
)

// Orders analyzed by seller carrier dispatch date
Orders Dispatched to Carrier = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_delivered_carrier_date_only], dim_date[date])
)

// Orders analyzed by customer receipt date
Orders Delivered to Customer = 
CALCULATE(
    [Total Orders],
    USERELATIONSHIP(fact_orders[order_delivered_customer_date_only], dim_date[date])
)

// Customer reviews analyzed by review answer submission date
Reviews Answered = 
CALCULATE(
    [Total Reviews],
    USERELATIONSHIP(fact_order_reviews[review_answer_date_only], dim_date[date])
)
```

---

## Section 4: Dashboard Theme & Visual Formatting Standards

To ensure a cohesive, portfolio-grade executive aesthetic:

### 4.1. Color Palette (Hex Codes)
- **Primary Navy / Dark Slate**: `#0F172A` (Headers, main text, navigation tabs).
- **Primary Accent Blue**: `#2563EB` (Primary data bars, active trend lines).
- **Secondary Teal**: `#0D9488` (Orders, volume metrics, freight).
- **Success Green**: `#16A34A` (On-time deliveries, 5-star reviews, high scores).
- **Warning Amber**: `#D97706` (Moderate delays, 3-star reviews).
- **Danger Red / Crimson**: `#DC2626` (Late deliveries, 1-star reviews, cancellations).
- **Neutral Light Background**: `#F8FAFC` (Canvas background).
- **Card / Visual Background**: `#FFFFFF` (Pure white with 1px border `#E2E8F0` and 4px corner radius).

### 4.2. Typography Hierarchy
- **Dashboard / Page Titles**: `Segoe UI Bold`, 18–20 pt, Dark Navy (`#0F172A`).
- **KPI Card Callout Values**: `Segoe UI Bold`, 24–28 pt, Primary Accent (`#2563EB` or `#0F172A`).
- **KPI Card Labels**: `Segoe UI Semibold`, 10 pt, Slate Gray (`#64748B`).
- **Visual Titles**: `Segoe UI Semibold`, 12–14 pt, Dark Navy (`#0F172A`).
- **Data Labels & Axis Text**: `Segoe UI Regular`, 9–10 pt, Slate Gray (`#475569`).

### 4.3. Canvas Dimensions & Spacing
- **Canvas Size**: 16:9 Widescreen (**1280 x 720 px** or **1920 x 1080 px**).
- **Margins**: Consistent 16 px padding from canvas edges.
- **Visual Gaps**: 12–16 px spacing between adjacent cards and visuals.

---

## Section 5: Detailed Page-by-Page Visual Specifications

---

### Page 1 – Executive Overview

#### Business Objective
Deliver high-level visibility to C-suite leadership regarding marketplace revenue scale, order velocity, unique customer reach, satisfaction baseline, and payment tender distribution over the platform's multi-year history.

```text
+---------------------------------------------------------------------------------------------------+
|  [Date Range Slicer: 2016-09 - 2018-10]               [Customer State Slicer: All / Multi-Select] |
+---------------------------------------------------------------------------------------------------+
| [Card: Item Revenue]  [Card: Freight]  [Card: Gross Value]  [Card: Orders]  [Card: Buyers]  [Card: Rating] |
|   R$ 13.59M             R$ 2.25M          R$ 15.84M            99,441          96,096          4.09        |
+---------------------------------------------------------+-----------------------------------------+
| Visual 1: Monthly Sales & Order Trends (2016-2018)      | Visual 2: Payment Method Breakdown      |
| [Line and Clustered Column: Orders (Bar) vs Rev (Line)] | [Donut Chart: Credit Card / Boleto / ..]|
+---------------------------------------------------------+-----------------------------------------+
```

#### Page Visual Specifications

| Visual # | Visual Type | Title | Field Bindings / Axes | Formatting & Styling |
| :--- | :--- | :--- | :--- | :--- |
| **Slicer 1** | Between Date Slicer | *Purchase Timeline* | `dim_date[date]` | Slider mode, range: `2016-09-04` to `2018-10-17`. |
| **Slicer 2** | Dropdown Slicer | *Customer State* | `dim_customers[customer_state]` | Searchable dropdown with "Select All" enabled. |
| **KPI 1** | Card | *Item Product Revenue* | `[Total Item Revenue]` | Display Units: Millions (`R$ 13.59M`), font color `#2563EB`. |
| **KPI 2** | Card | *Freight Revenue Collected*| `[Total Freight Revenue]` | Display Units: Millions (`R$ 2.25M`), font color `#0D9488`. |
| **KPI 3** | Card | *Freight-Inclusive Order Value*| `[Freight-Inclusive Order Value]` | Display Units: Millions (`R$ 15.84M`), font color `#0F172A`. |
| **KPI 4** | Card | *Total Orders Placed* | `[Total Orders]` | Format: Whole Number with comma (`99,441`). |
| **KPI 5** | Card | *Active Buyers (Selected Period)*| `[Active Buyers in Selected Period]` | Format: Whole Number with comma (**96,096** all-time; dynamically adjusts to date filter, e.g. **7,430** in Nov 2017). Subtitle: "All-Time Platform Reach: 96,096 Unique Buyers". |
| **KPI 6** | Card | *Average Customer Rating* | `[Average Review Score]` | Format: 2 decimal places (`4.09 / 5.00`), star icon if supported. |
| **Visual 1** | Line and Clustered Column | *Monthly Order Volume & Revenue Trends* | **X-axis**: `dim_date[year_month]`<br/>**Column Y-axis**: `[Total Orders]`<br/>**Line Y-axis**: `[Total Item Revenue]`<br/>**Secondary Line**: `[Total Freight Revenue]` | Bar color `#0D9488` (Teal), Item line `#2563EB` (Blue), Freight line `#D97706` (Amber). Enable data markers on lines. |
| **Visual 2** | Donut Chart | *Payment Method Share of Transaction Value* | **Legend**: `fact_order_payments[payment_type]`<br/>**Values**: `[Total Recorded Payment Value]` | Color sequence: Credit Card `#2563EB`, Boleto `#0D9488`, Voucher `#D97706`, Debit Card `#8B5CF6`. Data labels: Category & Percent of Total. |

#### Expected Benchmark Verification Values (Page 1)
- Total Item Revenue: **R$ 13,591,643.70**
- Total Freight Revenue: **R$ 2,251,909.54**
- Freight-Inclusive Order Value: **R$ 15,843,553.24**
- Total Recorded Payment Value: **R$ 16,008,872.12**
- Total Orders: **99,441**
- Unique Real-World Buyers (All-Time Reach): **96,096**
- Peak Month (Nov 2017): Item Rev = **R$ 1,010,271.37**, Freight = **R$ 168,872.40**, Orders = **7,544**, Active Buyers = **7,430**, Avg Spend per Active Buyer = **R$ 135.97**.

---

### Page 2 – Product Performance

#### Business Objective
Analyze catalog merchandise categories, isolate top revenue generators, validate the Pareto 80/20 distribution rule, and evaluate ticket size versus sales volume across all **74 catalog categories**.

```text
+---------------------------------------------------------------------------------------------------+
|  [Pareto Slicer: Core 80% (A) / Long Tail (B/C)]         [Category Slicer: Searchable Multi-Select] |
+---------------------------------------------------------------------------------------------------+
| [Card: Catalog Categories]  [Card: Core Categories]  [Card: Top Category Dynamic] [Card: Avg Product Units/Order]|
|            74                      17                Health & Beauty (R$ 1.26M)                 1.13      |
+---------------------------------------------------------+-----------------------------------------+
| Visual 1: Top 15 Product Categories by Item Revenue     | Visual 2: Pareto Cumulative Revenue %   |
| [Clustered Bar Chart: Revenue by Category (Top 15)]     | [Line & Column: Ranked Categories]      |
+---------------------------------------------------------+-----------------------------------------+
| Visual 3: Category Performance Master Matrix                                                      |
| [Matrix: Category | Item Revenue | Freight | Units Sold | Orders Containing Products | Avg Order Val | Avg Units/Order] |
+---------------------------------------------------------------------------------------------------+
```

#### Page Visual Specifications

| Visual # | Visual Type | Title | Field Bindings / Axes | Formatting & Styling |
| :--- | :--- | :--- | :--- | :--- |
| **Slicer 1** | Tile / Button Slicer | *Pareto Tier* | `dim_products[pareto_class]` | Buttons: `Core 80% (A)`, `Long Tail (B/C)`, Multi-select allowed. |
| **Slicer 2** | Dropdown Slicer | *Product Category* | `dim_products[product_category_name_english]` | Search enabled, sorted by `category_revenue_rank`. |
| **KPI 1** | Card | *Catalog Categories* | Distinct Count of `dim_products[product_category_name_english]` | Whole number: **74** (73 translated + 1 `'unknown'`). |
| **KPI 2** | Card | *Core 80% Drivers* | Fixed Card / Measure: `17 Categories` | Subtitle: "Generate 79.62% of merchandise value". |
| **KPI 3** | Card | *Top Category (Dynamic)* | `[Top Category Label]` | Dynamically updates: `"health_beauty (R$ 1,258,681.34)"`. |
| **KPI 4** | Card | *Avg Product Units/Order* | `[Average Product Units per Order]` | Format: 2 decimals (**1.13** platform-wide; dynamically evaluates basket depth when categories are filtered). Subtitle: "Platform-Wide Benchmark: 1.13 Units/Order". |
| **Visual 1** | Clustered Bar Chart | *Top 15 Categories by Item Product Revenue* | **Y-axis**: `dim_products[product_category_name_english]` (Sorted by `category_revenue_rank`)<br/>**X-axis**: `[Total Item Revenue]`<br/>**Filter**: Top N = 15 by `[Total Item Revenue]` | Data labels ON (Millions). Bar color `#2563EB`. Tooltip includes `[Total Units Sold]`, `[Orders Containing Selected Products]`, `[Average Product Order Value]`, `[Average Product Units per Order]`. |
| **Visual 2** | Line and Clustered Column | *Pareto Category Concentration Curve* | **X-axis**: `dim_products[product_category_name_english]` (Sorted by `category_revenue_rank`)<br/>**Column Y-axis**: `[Total Item Revenue]`<br/>**Line Y-axis**: `[Cumulative Revenue Pct]` | Highlights steep initial slope of the top 17 categories reaching 79.62% of platform merchandise revenue. Uses global catalog measures unaffected by tier slicer distortion. |
| **Visual 3** | Table / Matrix | *Category Performance Master Summary* | **Rows**: `dim_products[product_category_name_english]`<br/>**Values**: `[Total Item Revenue]`, `[Total Freight Revenue]`, `[Total Units Sold]`, `[Orders Containing Selected Products]`, `[Average Product Order Value]`, `[Average Product Units per Order]` | Conditional data bars on `[Total Item Revenue]`. Column totals enabled. |

#### Expected Benchmark Verification Values (Page 2)
- Top 5 Categories:
  1. `health_beauty`: R$ 1,258,681.34 item rev (9,670 units | 8,836 orders | Avg Order Val: R$ 142.45 | Avg Units/Order: 1.09)
  2. `watches_gifts`: R$ 1,205,005.68 item rev (5,991 units | 5,624 orders | Avg Order Val: R$ 214.26 | Avg Units/Order: 1.07)
  3. `bed_bath_table`: R$ 1,036,988.68 item rev (11,115 units | 9,417 orders | Avg Order Val: R$ 110.12 | Avg Units/Order: 1.18)
  4. `sports_leisure`: R$ 988,048.97 item rev (8,641 units | 7,720 orders | Avg Order Val: R$ 127.99 | Avg Units/Order: 1.12)
  5. `computers_accessories`: R$ 911,954.32 item rev (7,827 units | 6,689 orders | Avg Order Val: R$ 136.34 | Avg Units/Order: 1.17)
- **Pareto Core (`Core 80% (A)`, 17 categories)**: **R$ 10,822,328.51** item revenue (**79.62%** share) across 82,055 units.
- **Long Tail (`Long Tail (B/C)`, 57 categories)**: **R$ 2,769,315.19** item revenue (**20.38%** share) across 30,595 units.
- Total Categories Accounted For: **74 categories** | **R$ 13,591,643.70** (100.0%).

---

### Page 3 – Customer Analytics & RFM Segmentation

#### Business Objective
Analyze customer retention, distinguish single-order buyers from repeat purchasers, and evaluate customer cohorts using the standardized 8-segment RFM framework with distinct buyer-level averages.

```text
+---------------------------------------------------------------------------------------------------+
|  [Customer State Slicer: All / Multi-Select]             [RFM Segment Slicer: 8 Cohorts]          |
+---------------------------------------------------------------------------------------------------+
| [Card: Unique Buyers]  [Card: Single-Order Buyers]  [Card: Repeat Buyers]  [Card: Repeat Rate %]  |
|         96,096                 93,099 (96.88%)              2,997                  3.12%          |
+---------------------------------------------------------+-----------------------------------------+
| Visual 1: Buyer Loyalty Breakdown (Single vs Repeat)    | Visual 2: RFM Cohort Population Share   |
| [Donut Chart: 96.9% Single vs 3.1% Repeat]              | [Horizontal Bar: Buyer Count by Segment]|
+---------------------------------------------------------+-----------------------------------------+
| Visual 3: RFM Customer Cohort Behavioral & Financial Matrix                                       |
| [Matrix: Segment | Unique Buyers | Buyer Share % | Avg Recency | Avg Freq | Item Rev | Rev Share%]|
+---------------------------------------------------------------------------------------------------+
```

#### Page Visual Specifications

| Visual # | Visual Type | Title | Field Bindings / Axes | Formatting & Styling |
| :--- | :--- | :--- | :--- | :--- |
| **Slicer 1** | Dropdown Slicer | *Customer State* | `dim_customers[customer_state]` | Alphabetical 2-letter state selector. |
| **Slicer 2** | Dropdown Slicer | *RFM Segment* | `dim_customers[customer_segment]` | Multi-select dropdown of the 8 segments. |
| **KPI 1** | Card | *Unique Real-World Buyers*| `[Unique Real-World Buyers]` | Number format: `96,096`. |
| **KPI 2** | Card | *Single-Order Buyers* | `[Single-Order Buyers]` | Number format: `93,099` (96.88%). |
| **KPI 3** | Card | *Repeat Buyers* | `[Repeat Buyers]` | Number format: `2,997` (3.12%). |
| **KPI 4** | Card | *Repeat Purchase Rate* | `[Repeat Purchase Rate]` | Percentage format: `3.12%`, warning color `#D97706`. |
| **Visual 1** | Donut Chart | *Customer Frequency Distribution* | **Legend**: `dim_customers[Customer Type]`<br/>**Values**: `[Unique Real-World Buyers]` | Single-order `#2563EB` (96.9%), Repeat `#16A34A` (3.1%). Data labels: Percent & Value. |
| **Visual 2** | Clustered Bar Chart | *Customer Population by RFM Segment* | **Y-axis**: `dim_customers[customer_segment]`<br/>**X-axis**: `[Unique Real-World Buyers]` | Sorted descending. Data labels ON. Color by segment tier. |
| **Visual 3** | Matrix | *Customer RFM Segment Behavioral & Financial Matrix* | **Rows**: `dim_customers[customer_segment]`<br/>**Values**: `[Unique Real-World Buyers]`, `[Total Item Revenue]`, `[Average Recency Days per Buyer]`, `[Average Order Frequency per Buyer]` | Buyer-level measures ensure each unique buyer contributes once. Subtotals OFF, Grand Total ON. |

#### Expected Benchmark Verification Values (Page 3)
- Real-World Buyer Population: **96,096 distinct buyers**
- Single-Order Buyers: **93,099** (96.88%)
- Repeat Buyers: **2,997** (3.12%)
- `[Repeat Purchase Rate]`: **3.12%**
- Segment Breakdown (Unique Buyers, Item Revenue, Buyer-Weighted Avg Recency, Buyer-Weighted Avg Frequency):
  - `New & Promising`: 37,032 buyers (38.54%) | R$ 5,231,783.91 (38.49%) | **139.9 days** | **1.00 orders**
  - `Lost / Inactive`: 22,995 buyers (23.93%) | R$ 1,284,210.68 (9.45%) | **445.3 days** | **1.00 orders**
  - `Needs Attention`: 18,466 buyers (19.22%) | R$ 2,402,105.03 (17.67%) | **270.1 days** | **1.00 orders**
  - `Hibernating High-Spenders`: 13,938 buyers (14.50%) | R$ 3,894,722.11 (28.66%) | **446.1 days** | **1.00 orders**
  - `Champions & Loyal`: 1,305 buyers (1.36%) | R$ 350,103.63 (2.58%) | **136.7 days** | **2.16 orders**
  - `At Risk Repeaters`: 1,047 buyers (1.09%) | R$ 263,764.51 (1.94%) | **433.3 days** | **2.08 orders**
  - `Unfulfilled / Canceled`: 676 buyers (0.70%) | R$ 0.00 (0.00%) | **378.0 days** | **1.01 orders**
  - `Potential Loyalists`: 637 buyers (0.66%) | R$ 164,953.83 (1.21%) | **268.2 days** | **2.09 orders**
  - **Total Population**: **96,096 buyers** | **R$ 13,591,643.70** | **242.4 days avg** | **1.03 orders avg**

---

### Page 4 – Regional Geography & Logistics Friction

#### Business Objective
Map e-commerce demand across all 27 Brazilian Federative Units, distinguish commercial concentration metrics in São Paulo, and quantify the severe freight cost and transit time disparities faced by customers in Northern and Northeastern states.

```text
+---------------------------------------------------------------------------------------------------+
|  [Date Timeline Slicer: Between]                         [State Multi-Select Slicer]              |
+---------------------------------------------------------------------------------------------------+
| [Card: Federative Units]  [Card: SP Gross Share]   [Card: Fastest Transit]  [Card: Highest Freight]|
|           27                   SP (37.38% Gross)        SP (8.76 Days)            RR (R$ 53.30)   |
+---------------------------------------------------------+-----------------------------------------+
| Visual 1: Brazilian Demand Map                          | Visual 2: Top 10 States by Revenue      |
| [Filled Map / Bubble Map: State Bubble by Revenue]      | [Horizontal Bar: SP, RJ, MG, ...]       |
+---------------------------------------------------------+-----------------------------------------+
| Visual 3: Average Freight Cost by State (Logistics Tax) | Visual 4: Delivery Duration by State    |
| [Horizontal Bar: RR, AP, AM at top]                     | [Horizontal Bar: RR, AP, AM at top]     |
+---------------------------------------------------------+-----------------------------------------+
```

#### Page Visual Specifications

| Visual # | Visual Type | Title | Field Bindings / Axes | Formatting & Styling |
| :--- | :--- | :--- | :--- | :--- |
| **Slicer 1** | Dropdown Slicer | *State Selector* | `dim_customers[customer_state]` | Alphabetical listing with search. |
| **KPI 1** | Card | *Federative Units Covered*| Distinct Count of `dim_customers[customer_state]` | Whole number: **27**. |
| **KPI 2** | Card | *São Paulo Market Dominance* | Text / Calculated Card: `"SP Gross Share: 37.38%"` | Subtitle: "41,746 Orders (41.98% Vol) \| R$ 5.20M Item Rev (38.28%)". |
| **KPI 3** | Card | *Fastest Delivery State* | Text: `"SP: 8.76 Days Avg"` | Benchmark of lowest logistical friction. |
| **KPI 4** | Card | *Highest Freight State* | Text: `"RR: R$ 53.30 Avg"` | Benchmark of severe remote freight penalty. |
| **Visual 1** | Map (Filled Map / Bubble Map) | *Regional Marketplace Demand & Logistics Geography* | **Location**: `dim_customers[customer_state]`<br/>**Latitude**: `dim_customers[customer_lat]` (Average)<br/>**Longitude**: `dim_customers[customer_lng]` (Average)<br/>**Size**: `[Total Item Revenue]`<br/>**Tooltip**: `[Total Orders]`, `[Avg Delivery Duration Days]`, `[Average Freight per Order]` | High contrast bubbles over Brazilian territory. |
| **Visual 2** | Clustered Bar Chart | *Top 10 Brazilian States by Item Revenue* | **Y-axis**: `dim_customers[customer_state]`<br/>**X-axis**: `[Total Item Revenue]`<br/>**Filter**: Top N = 10 | Primary color `#2563EB`. Data labels enabled. |
| **Visual 3** | Clustered Bar Chart | *Average Freight Cost per Order by State* | **Y-axis**: `dim_customers[customer_state]`<br/>**X-axis**: `[Average Freight per Order]`<br/>**Sort**: Descending by freight value | Diverging color scale: Red/Amber for high freight (`RR`, `AP`, `AM`), Green/Teal for low freight (`SP`, `PR`). |
| **Visual 4** | Clustered Bar Chart | *Average Delivery Duration (Days) by State* | **Y-axis**: `dim_customers[customer_state]`<br/>**X-axis**: `[Avg Delivery Duration Days]`<br/>**Sort**: Descending by duration | Illustrates the 3-week+ transit time in remote regions. |

#### Reconciled Regional Benchmarks & Denominator Audit (Page 4)

##### São Paulo (`SP`) Metric Disambiguation & Integrity Audit:
- **Order Volume Share**: **41.98%** ($41,746 \text{ orders} / 99,441 \text{ platform orders}$)
- **Unique Real-World Buyer Share**: **41.94%** ($40,302 \text{ buyers} / 96,096 \text{ platform buyers}$)
- **Item Product Revenue**: **R$ 5,202,955.05** (Exact: 520,295,505 integer cents)
- **Item Product Revenue Share**: **38.28%** ($\text{R\$ } 5,202,955.05 / \text{R\$ } 13,591,643.70$)
- **Freight Revenue Collected**: **R$ 718,723.07** (Exact: 71,872,307 integer cents)
- **Freight-Inclusive (Gross) Order Value**: **R$ 5,921,678.12** (Exact: 592,167,812 integer cents)
- **Freight-Inclusive (Gross) Order Value Share**: **37.38%** ($\text{R\$ } 5,921,678.12 / \text{R\$ } 15,843,553.24$)

> [!NOTE]
> **Reconciliation of Earlier R$ 5,249,271.86 Draft Discrepancy**:
> - A fresh, independent multi-layer aggregation confirms that São Paulo merchandise item revenue is strictly **R$ 5,202,955.05** (520,295,505 cents) across:
>   1. Direct SQLite database aggregation (`fact_orders` $\to$ `dim_customers` $\to$ `fact_order_items` on `customer_state = 'SP'`).
>   2. Phase 5 SQL query mart (`04_regional_geography_analysis.sql` / `regional_sales_performance.csv`).
>   3. Power BI reporting CSV export join (`fact_order_items.csv` joined to `fact_orders.csv` and `dim_customers.csv`).
> - The earlier cited figure of R$ 5,249,271.86 (an observed difference of R$ 46,316.81) was an unreconciled figure from an earlier project draft. Subsequent three-source validation established the authoritative value of **R$ 5,202,955.05**. The precise cause of the earlier R$ 46,316.81 discrepancy was not established from the available project artifacts, and no specific mechanism is assumed.

> [!NOTE]
> **Average Freight per Order Denominator Reconciled**:
> - **Platform-wide calculation in DAX**: `DIVIDE([Total Freight Revenue], [Total Orders], 0)` divides SP freight by all 41,746 orders placed $\to \mathbf{\text{R\$ } 17.22}$.
> - **Phase 5 SQL Mart calculation**: In `04_regional_geography_analysis.sql`, `AVG(i.freight_revenue)` averaged only across the 41,375 fulfilled orders with assigned items (ignoring 371 unfulfilled orders with NULL freight) $\to \mathbf{\text{R\$ } 17.37}$. Both figures are correct under their respective denominators.

##### Other Key State Benchmarks:
- **Rio de Janeiro (`RJ`)**: 12,852 orders | R$ 1,824,093.63 item rev | Avg Freight: **R$ 20.97** | Avg Delivery Duration: **15.08 days** | Late Rate: **13.47%**
- **Minas Gerais (`MG`)**: 11,635 orders | R$ 1,585,408.04 item rev | Avg Freight: **R$ 20.63** | Avg Delivery Duration: **11.83 days** | Late Rate: **5.62%**
- **Remote Outliers (Highest Friction)**:
  - Roraima (`RR`): 46 orders | Avg Freight: **R$ 42.98** (All orders) / **R$ 53.30** (Fulfilled orders) | Avg Delivery: **28.98 days** | Late Rate: **20.83%**
  - Amapá (`AP`): 68 orders | Avg Delivery: **26.73 days**
  - Amazonas (`AM`): 148 orders | Avg Delivery: **25.99 days**

---

### Page 5 – Delivery Performance & Customer Satisfaction

#### Business Objective
Quantify fulfillment timeliness, track delivery delay distribution against the estimated SLA, evaluate all 8 distinct order lifecycle statuses, and visualize the empirical relationship between transit delays and customer review scores.

```text
+---------------------------------------------------------------------------------------------------+
|  [Order Status Slicer: All 8 Statuses]                   [Purchase Date Range Slicer]              |
+---------------------------------------------------------------------------------------------------+
| [Card: Delivered Orders]  [Card: On-Time Rate]   [Card: Avg Transit Time]  [Card: Avg Review Score]|
|     96,478 (97.02%)          91.89% (On-Time)           12.5 Days                  4.09 / 5.00     |
+---------------------------------------------------------+-----------------------------------------+
| Visual 1: Order Lifecycle Status Breakdown (All 8)      | Visual 2: Delivery Timeliness Buckets   |
| [Donut Chart: Delivered (96.5k), Shipped (1.1k), ..]    | [Column Chart: 0. On-Time to 3. Severe] |
+---------------------------------------------------------+-----------------------------------------+
| Visual 3: Customer Review Score Distribution (1-5)      | Visual 4: Delivery Delay vs Rating      |
| [Column Chart: 5-Star (57.4k) to 1-Star (11.4k)]        | [Column/Line: Rating collapse on delay] |
+---------------------------------------------------------+-----------------------------------------+
| > [!NOTE] Empirical Association: Review scores drop sharply past Day 3 of delay.                  |
+---------------------------------------------------------------------------------------------------+
```

#### Page Visual Specifications

| Visual # | Visual Type | Title | Field Bindings / Axes | Formatting & Styling |
| :--- | :--- | :--- | :--- | :--- |
| **Slicer 1** | Dropdown Slicer | *Order Lifecycle Status*| `fact_orders[order_status]` | Multi-select dropdown containing all 8 distinct statuses. |
| **Slicer 2** | Between Date Slicer | *Purchase Date* | `dim_date[date]` | Slider mode. |
| **KPI 1** | Card | *Delivered Orders* | `[Total Delivered Orders]` | Whole number: **96,478** (97.02% of all orders). Subtitle: "96,470 with recorded delivery dates". |
| **KPI 2** | Card | *On-Time Fulfillment Rate*| `[On-Time Delivery Rate]` | Percentage: **91.89%** (evaluated across the 96,470 eligible delivered orders with recorded delivery timestamps). |
| **KPI 3** | Card | *Avg Delivery Duration* | `[Avg Delivery Duration Days]` | Format: 1 decimal (**12.5 days** / 12.56 days across delivered orders). |
| **KPI 4** | Card | *Average Customer Rating* | `[Average Review Score]` | Format: 2 decimals (**4.09 / 5.00**). |
| **Visual 1** | Donut Chart | *Order Completion Status Breakdown (All 8 Statuses)* | **Legend**: `fact_orders[order_status]`<br/>**Values**: `[Total Orders]` | Displays all 8 observed statuses: Delivered `#16A34A` (96,478), Shipped `#2563EB` (1,107), Canceled `#DC2626` (625), Unavailable `#D97706` (609), Invoiced `#8B5CF6` (314), Processing `#64748B` (301), Created `#94A3B8` (5), Approved `#CBD5E1` (2). Total = 99,441. |
| **Visual 2** | Clustered Column Chart | *Delivery Timeliness SLA Performance* | **X-axis**: `fact_orders[delivery_performance_bucket]`<br/>**Y-axis**: `[Delivered Orders in Bucket]` | Colors: On-Time `#16A34A`, Slightly Late `#F59E0B`, Moderately Late `#EA580C`, Severely Late `#DC2626`. Dedicated measure restricts visual strictly to the 96,470 eligible delivered orders with valid delivery dates. |
| **Visual 3** | Clustered Column Chart | *Customer Satisfaction Survey Distribution* | **X-axis**: `fact_order_reviews[review_score]` (1 to 5)<br/>**Y-axis**: `[Total Reviews]` | Colors: 5-Star `#16A34A`, 4-Star `#10B981`, 3-Star `#F59E0B`, 2-Star `#EA580C`, 1-Star `#DC2626`. General-purpose measure covers all 99,224 customer reviews across all orders. |
| **Visual 4** | Line and Clustered Column | *Customer Satisfaction vs. Delivery Delay Buckets* | **X-axis**: `fact_orders[delivery_performance_bucket]`<br/>**Column Y-axis**: `[Delivered Orders in Bucket]`<br/>**Line Y-axis**: `[Average Review Score for Delivered Orders]`<br/>**Secondary Line**: `[Negative Review Rate for Delivered Orders]` | Column bars `#CBD5E1` (muted), Rating line `#2563EB` (Blue marker), Dissatisfaction line `#DC2626` (Red dashed). Dedicated measures ensure volume, rating, and dissatisfaction are evaluated strictly across the 96,470 eligible delivered orders. |

#### Expected Benchmark Verification Values (Page 5)

##### Order Status Breakdown (All 8 Statuses = 99,441 Orders):
1. `delivered`: **96,478 orders** (97.02%)
2. `shipped`: **1,107 orders** (1.11%)
3. `canceled`: **625 orders** (0.63%)
4. `unavailable`: **609 orders** (0.61%)
5. `invoiced`: **314 orders** (0.32%)
6. `processing`: **301 orders** (0.30%)
7. `created`: **5 orders** (0.01%)
8. `approved`: **2 orders** (0.00%)
*Total*: **99,441 orders** (100.00%)

##### Delivery Timeliness SLA Buckets Reconciled (Strict Delivered Cohort = 96,470 Orders):
Evaluated strictly across delivered-status orders with valid customer delivery timestamps (excluding 8 delivered orders missing timestamps and 6 canceled orders with timestamps):
- `0. Early / On-Time (<= 0d)`: **88,644 orders** (91.89% of eligible delivered | 89.14% of all orders) | 88,163 reviewed orders (88,653 reviews) | **Avg Rating: 4.29** | 1-Star Rate: **6.60%** review grain (5,851 / 88,653) / **6.55%** order grain (5,779 / 88,163) | Avg Duration: **10.88d** | Avg Delay: **-13.01d**
- `1. Slightly Late (1-3d)`: **2,662 orders** (2.76% of eligible delivered | 2.68% of all orders) | 2,636 reviewed orders (2,651 reviews) | **Avg Rating: 3.77** | 1-Star Rate: **13.81%** review grain (366 / 2,651) / **13.69%** order grain (361 / 2,636) | Avg Duration: **21.08d** | Avg Delay: **+1.40d**
- `2. Moderately Late (4-7d)`: **1,819 orders** (1.89% of eligible delivered | 1.83% of all orders) | 1,773 reviewed orders (1,777 reviews) | **Avg Rating: 2.32** | 1-Star Rate: **53.01%** review grain (942 / 1,777) / **53.02%** order grain (940 / 1,773) | Avg Duration: **26.68d** | Avg Delay: **+5.12d**
- `3. Severely Late (> 7d)`: **3,345 orders** (3.47% of eligible delivered | 3.36% of all orders) | 3,252 reviewed orders (3,272 reviews) | **Avg Rating: 1.73** | 1-Star Rate: **68.64%** review grain (2,246 / 3,272) / **68.63%** order grain (2,232 / 3,252) | Avg Duration: **42.46d** | Avg Delay: **+18.45d**
- **Total Eligible Delivered Cohort**: **96,470 orders** (100.0% of delivered with timestamps)
  - **On-Time Fulfillment (<= 0d)**: **88,644 orders** (**91.89%**)
  - **Delayed Fulfillment (> 0d)**: **7,826 orders** (**8.11%**) | Avg Late Duration: **31.52 days** | Avg Late Delay: **9.55 days**

##### Orders Without Usable Delivery Timestamps (2,965 Orders):
- Exactly **2,965 orders** lack a recorded customer delivery timestamp:
  - **2,957 orders** with non-delivered lifecycle status (1,107 shipped, 619 canceled without delivery timestamp, 609 unavailable, 314 invoiced, 301 processing, 5 created, 2 approved).
  - Exactly **8 orders** with `order_status = "delivered"` missing delivery timestamps (`2d1e2d...`, `f5dd62...`, `2ebdfc...`, `e69f75...`, `0d3268...`, `2d858f...`, `ab7c89...`, `20edc8...`).
  - Because they lack valid customer delivery timestamps, all 2,965 orders are strictly excluded from the 96,470-order SLA cohort and its delivery timeliness bucket visual.
  - Review Performance for Undelivered / Missing Timestamp Orders: 2,843 reviews | **Avg Rating: 1.75** | 1-Star Rate: **70.35%** (2,000 reviews).

##### Canceled Orders with Recorded Delivery Timestamps (6 Orders):
- Exactly 6 orders have `order_status = "canceled"` yet record an `order_delivered_customer_date` (`1950d7...`, `dabf2b...`, `770d33...`, `8beb59...`, `65d1e2...`, `2c45c3...`). The dataset does not establish why these records contain both a canceled status and a delivery timestamp. They are strictly excluded from delivered-order SLA metrics.
- **Master Platform Reconciliation**: $96,470 \text{ (Eligible Delivered)} + 6 \text{ (Canceled with Timestamps)} + 2,965 \text{ (Without Timestamps)} = \mathbf{99,441 \text{ orders}}$ (100.0%).

> [!NOTE]
> **Careful Non-Causal Interpretation**:
> The empirical findings show a strong statistical association between extended shipping delays and negative customer satisfaction reviews. However, this is documented strictly as an **empirical association**, not proof of causation, as unobserved co-occurring factors (such as packaging damage, incorrect SKU dispatch, or product defects) may correlate with shipping friction.

---

## Section 6: Limitations & Non-Supported Metrics

When designing visuals or presenting conclusions to stakeholders, keep these dataset boundaries in mind:

1. **No Profit, COGS, or Gross Margin**:
   - The public Olist dataset contains selling price and freight, but **does not record wholesale merchant acquisition costs (Cost of Goods Sold / COGS)** or platform operating costs.
   - Do **not** calculate, display, or estimate profit margins or net income. All revenue figures represent top-line merchandise or freight collections.
2. **No Marketing ROI, CAC, or Campaign Attribution**:
   - Customer acquisition costs, digital marketing ad spend, and conversion channel attribution are not present.
   - Do **not** invent or display Return on Ad Spend (ROAS) or Customer Acquisition Cost (CAC).
3. **No Carrier Identity**:
   - Courier and logistics provider names are anonymized or omitted from the public data. Delivery duration reflects the combined seller dispatch and postal transit timeframe.
4. **Natural Buyer Counting Rule**:
   - Never use `COUNTROWS(dim_customers)` as the real-world customer count. Always use `DISTINCTCOUNT(dim_customers[customer_unique_id])`.

---

## Section 7: Final Dashboard Verification Checklist

Before publishing or presenting the `.pbix` file, verify each visual against the following audit benchmarks:

| Checkpoint | Visual / Area | Expected Exact Value | Verified in Power BI? |
| :-: | :--- | :--- | :-: |
| **1** | Main Canvas Model | Exactly 8 Group A tables loaded; `dim_geolocation` excluded. | [ ] |
| **2** | Relationships | Exactly **14 relationships** (7 active, 7 inactive); single-direction cross-filtering. | [ ] |
| **3** | Customer Join | `dim_customers` $\to$ `fact_orders` is strictly **1:1**. | [ ] |
| **4** | Date Table | `dim_date` marked as official Date Table with column `date`. | [ ] |
| **5** | Page 1 Revenue | `[Total Item Revenue]` = **R$ 13,591,643.70** | [ ] |
| **6** | Page 1 Freight | `[Total Freight Revenue]` = **R$ 2,251,909.54** | [ ] |
| **7** | Page 1 Order Value | `[Freight-Inclusive Order Value]` = **R$ 15,843,553.24** | [ ] |
| **8** | Page 1 Payments | `[Total Recorded Payment Value]` = **R$ 16,008,872.12** | [ ] |
| **9** | Page 1 Orders | `[Total Orders]` = **99,441** | [ ] |
| **10** | Page 1 Buyers | `[Active Buyers in Selected Period]` = **96,096** all-time reach (**7,430** active buyers in Nov 2017). | [ ] |
| **11** | Page 1 Review Avg | `[Average Review Score]` = **4.09 / 5.00** | [ ] |
| **12** | Page 2 Categories | Exactly **74 catalog categories**; Top category dynamically evaluated. | [ ] |
| **13** | Page 2 Pareto | Exactly **17 categories** in `Core 80% (A)` driving **R$ 10,822,328.51** (79.62%). | [ ] |
| **14** | Page 2 Orders | Category matrix uses `[Orders Containing Selected Products]`, `[Average Product Order Value]`, and `[Average Product Units per Order]`. | [ ] |
| **15** | Page 3 Retention | Single-Order: **93,099** (96.88%) \| Repeat: **2,997** (3.12%) \| `[Repeat Purchase Rate]`: **3.12%**. | [ ] |
| **16** | Page 3 RFM Matrix | Matrix averages use `[Average Recency Days per Buyer]` and `[Average Order Frequency per Buyer]`. | [ ] |
| **17** | Page 4 Dominance | São Paulo (`SP`): **41.98%** order volume, **38.28%** item rev (R$ 5,202,955.05), **37.38%** gross value (R$ 5,921,678.12), R$ 17.22 vs R$ 17.37 freight. | [ ] |
| **18** | Page 5 Order Status | Donut chart displays all **8 distinct statuses** totaling **99,441 orders**. | [ ] |
| **19** | Page 5 Delivered | `[Total Delivered Orders]` = **96,478** (96,470 eligible with timestamps: 88,644 on-time $\to$ **91.89%** fulfillment rate); Visuals 2 & 4 enforce `[Delivered Orders in Bucket]`. | [ ] |
| **20** | Page 5 Delay Drop | Review score drops from **4.29** (On-Time, 6.60% review / 6.55% order) to **1.73** (Severe Delay, 68.64% review / 68.63% order) via `[Average Review Score for Delivered Orders]`. | [ ] |
