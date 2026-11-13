-- =====================================================================
-- Olist E-Commerce Relational Database Schema (SQLite)
-- =====================================================================
-- Project: E-Commerce Sales & Business Intelligence Analytics Platform
-- Author: Nandini Patel (GitHub: nandinipatel8011)
-- Design: Star-Constellation Schema with Conformed Dimensions & Granular Facts
-- Foreign Keys: PRAGMA foreign_keys = ON; must be enabled on every connection.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- 1. DIMENSION TABLES (Conformed Dimensions)
-- ---------------------------------------------------------------------

-- Dimension: Product Category Translation Lookup
DROP TABLE IF EXISTS dim_category_translation;
CREATE TABLE dim_category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT NOT NULL
);

-- Dimension: Products
-- Grain: One row per unique catalog product.
DROP TABLE IF EXISTS dim_products;
CREATE TABLE dim_products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT NOT NULL,
    product_category_name_english TEXT NOT NULL,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL,
    product_volume_cm3 REAL,
    FOREIGN KEY (product_category_name) REFERENCES dim_category_translation(product_category_name)
);

-- Dimension: Customers
-- Grain: One row per transactional customer profile.
-- Note: customer_id is the order-scoped surrogate key. customer_unique_id identifies the real person.
DROP TABLE IF EXISTS dim_customers;
CREATE TABLE dim_customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix INTEGER NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state TEXT NOT NULL
);

-- Dimension: Sellers
-- Grain: One row per registered marketplace merchant.
DROP TABLE IF EXISTS dim_sellers;
CREATE TABLE dim_sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state TEXT NOT NULL
);

-- Dimension: Geolocation Lookup (Aggregated Postal Centroids)
-- Grain: One row per 5-digit Brazilian CEP zip code prefix.
-- Coordinates are the median values of verified readings within Brazil.
DROP TABLE IF EXISTS dim_geolocation;
CREATE TABLE dim_geolocation (
    geolocation_zip_code_prefix INTEGER PRIMARY KEY,
    geolocation_lat REAL NOT NULL,
    geolocation_lng REAL NOT NULL,
    geolocation_city TEXT NOT NULL,
    geolocation_state TEXT NOT NULL,
    CHECK (geolocation_lat BETWEEN -34.0 AND 5.5),
    CHECK (geolocation_lng BETWEEN -74.0 AND -34.5)
);

-- ---------------------------------------------------------------------
-- 2. FACT TABLES (Granular Transactional Events)
-- ---------------------------------------------------------------------

-- Fact: Orders (Accumulating Snapshot Fact)
-- Grain: One row per distinct customer order.
DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TEXT NOT NULL,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT NOT NULL,
    order_purchase_year INTEGER NOT NULL,
    order_purchase_month INTEGER NOT NULL,
    order_purchase_year_month TEXT NOT NULL,
    order_purchase_day_of_week TEXT NOT NULL,
    delivery_duration_days REAL,
    delivery_delay_days REAL,
    is_delayed INTEGER,
    is_delivered INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    CHECK (is_delivered IN (0, 1)),
    CHECK (is_delayed IN (0, 1) OR is_delayed IS NULL),
    CHECK (delivery_duration_days >= 0 OR delivery_duration_days IS NULL)
);

-- Fact: Order Items (Transaction Line Item Fact)
-- Grain: One row per item line inside an order.
DROP TABLE IF EXISTS fact_order_items;
CREATE TABLE fact_order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,
    total_item_value NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (seller_id) REFERENCES dim_sellers(seller_id),
    CHECK (price >= 0),
    CHECK (freight_value >= 0),
    CHECK (total_item_value >= 0)
);

-- Fact: Order Payments (Financial Tender Fact)
-- Grain: One row per payment attempt / voucher installment.
DROP TABLE IF EXISTS fact_order_payments;
CREATE TABLE fact_order_payments (
    order_id TEXT NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value NUMERIC(10,2) NOT NULL,
    is_installment INTEGER NOT NULL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    CHECK (payment_installments >= 0),
    CHECK (payment_value >= 0),
    CHECK (is_installment IN (0, 1))
);

-- Fact: Order Reviews (Customer Feedback Fact)
-- Grain: One row per customer satisfaction survey response.
DROP TABLE IF EXISTS fact_order_reviews;
CREATE TABLE fact_order_reviews (
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_score INTEGER NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    has_comment_title INTEGER NOT NULL,
    has_comment_message INTEGER NOT NULL,
    review_creation_date TEXT NOT NULL,
    review_answer_timestamp TEXT NOT NULL,
    review_response_hours REAL,
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES fact_orders(order_id),
    CHECK (review_score BETWEEN 1 AND 5),
    CHECK (has_comment_title IN (0, 1)),
    CHECK (has_comment_message IN (0, 1))
);

-- ---------------------------------------------------------------------
-- 3. PERFORMANCE INDEXES
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp ON fact_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_year_month ON fact_orders(order_purchase_year_month);
CREATE INDEX IF NOT EXISTS idx_items_order_id ON fact_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product_id ON fact_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_items_seller_id ON fact_order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON fact_order_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON fact_order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON dim_customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_customers_zip ON dim_customers(customer_zip_code_prefix);
CREATE INDEX IF NOT EXISTS idx_sellers_zip ON dim_sellers(seller_zip_code_prefix);
