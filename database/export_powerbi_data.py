"""
Power BI Analytical Datasets & Data Marts Exporter
==================================================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This script extracts and exports validated, Power BI-ready star-schema
analytical datasets from 'database/ecommerce.db' to 'data/processed/powerbi/'.

Datasets Exported:
------------------
Group A: Main Power BI Semantic Model (Import into Power BI Canvas)
  1. dim_date.csv              (1,827 rows, 2016-01-01 to 2020-12-31)
  2. dim_customers.csv         (99,441 rows, with RFM & Coordinates)
  3. dim_products.csv          (32,951 rows, with Pareto Category Class)
  4. dim_sellers.csv           (3,095 rows)
  5. fact_orders.csv           (99,441 rows, 1:1 with dim_customers)
  6. fact_order_items.csv      (112,650 rows, 1:Many child fact)
  7. fact_order_payments.csv   (103,886 rows, 1:Many child fact)
  8. fact_order_reviews.csv    (99,224 rows, 1:Many child fact)

Group B: Auxiliary Reference & Validation Exports (Do NOT Import into Model)
  9. dim_geolocation.csv       (19,010 rows, reference postal centroids)
  (Preserves existing Phase 5 benchmark query marts)
"""

import os
import sqlite3
import pandas as pd
import numpy as np


def generate_date_dimension(start_date: str = "2016-01-01", end_date: str = "2020-12-31") -> pd.DataFrame:
    """Generates a complete, continuous calendar date dimension."""
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    df_date = pd.DataFrame({"date_dt": date_range})
    df_date["date_key"] = df_date["date_dt"].dt.strftime("%Y%m%d").astype(int)
    df_date["date"] = df_date["date_dt"].dt.strftime("%Y-%m-%d")
    df_date["year"] = df_date["date_dt"].dt.year
    df_date["quarter"] = df_date["date_dt"].dt.quarter
    df_date["quarter_name"] = "Q" + df_date["quarter"].astype(str)
    df_date["year_quarter"] = df_date["year"].astype(str) + "-Q" + df_date["quarter"].astype(str)
    df_date["month"] = df_date["date_dt"].dt.month
    df_date["month_name"] = df_date["date_dt"].dt.strftime("%B")
    df_date["month_short"] = df_date["date_dt"].dt.strftime("%b")
    df_date["year_month"] = df_date["date_dt"].dt.strftime("%Y-%m")
    df_date["day"] = df_date["date_dt"].dt.day
    df_date["day_of_week"] = df_date["date_dt"].dt.dayofweek + 1  # 1 = Monday, 7 = Sunday
    df_date["day_name"] = df_date["date_dt"].dt.strftime("%A")
    df_date["is_weekend"] = df_date["day_of_week"].apply(lambda d: 1 if d in (6, 7) else 0)
    
    df_date = df_date.drop(columns=["date_dt"])
    return df_date


def export_powerbi_datasets(db_path: str = "database/ecommerce.db",
                            output_dir: str = "data/processed/powerbi") -> dict:
    """Extracts, transforms, validates, and exports datasets for Power BI."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    print("=" * 80)
    print("STARTING POWER BI DATASET EXPORT PIPELINE")
    print(f"Source Database: {db_path}")
    print(f"Target Directory: {output_dir}")
    print("=" * 80)

    exported_files = {}

    try:
        # -----------------------------------------------------------------
        # 1. Date Dimension (dim_date.csv)
        # -----------------------------------------------------------------
        print("\n[1/9] Generating Date Dimension (2016-01-01 to 2020-12-31) ...", end=" ", flush=True)
        df_date = generate_date_dimension("2016-01-01", "2020-12-31")
        date_path = os.path.join(output_dir, "dim_date.csv")
        df_date.to_csv(date_path, index=False)
        exported_files["dim_date.csv"] = len(df_date)
        print(f"Done ({len(df_date):,} rows -> {date_path})")

        # -----------------------------------------------------------------
        # 2. Customer Dimension with RFM & Coordinates (dim_customers.csv)
        # -----------------------------------------------------------------
        print("[2/9] Extracting & Enriching Customer Dimension ...", end=" ", flush=True)
        query_customers = """
        SELECT
            c.customer_id,
            c.customer_unique_id,
            c.customer_zip_code_prefix,
            c.customer_city,
            c.customer_state,
            g.geolocation_lat AS customer_lat,
            g.geolocation_lng AS customer_lng,
            rfm.customer_segment,
            rfm.r_score,
            rfm.f_score,
            rfm.m_score,
            rfm.rfm_code,
            rfm.recency_days,
            rfm.order_frequency,
            rfm.total_monetary_spend
        FROM dim_customers c
        LEFT JOIN dim_geolocation g 
            ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
        LEFT JOIN view_customer_rfm rfm 
            ON c.customer_unique_id = rfm.customer_unique_id;
        """
        df_customers = pd.read_sql_query(query_customers, conn)
        
        # Verify no customers dropped
        if len(df_customers) != 99441:
            raise ValueError(f"Customer row count mismatch: expected 99,441, got {len(df_customers):,}")
        if df_customers["customer_id"].nunique() != 99441:
            raise ValueError("customer_id is not unique in dim_customers")
        if df_customers["customer_unique_id"].nunique() != 96096:
            raise ValueError(f"Distinct buyer count mismatch: expected 96,096, got {df_customers['customer_unique_id'].nunique():,}")

        cust_path = os.path.join(output_dir, "dim_customers.csv")
        df_customers.to_csv(cust_path, index=False)
        exported_files["dim_customers.csv"] = len(df_customers)
        print(f"Done ({len(df_customers):,} rows -> {cust_path})")

        # -----------------------------------------------------------------
        # 3. Product Dimension with Pareto Class (dim_products.csv)
        # -----------------------------------------------------------------
        print("[3/9] Extracting & Enriching Product Dimension ...", end=" ", flush=True)
        query_products = """
        SELECT
            p.product_id,
            p.product_category_name,
            p.product_category_name_english,
            cat.pareto_class,
            cat.revenue_rank AS category_revenue_rank,
            p.product_name_length,
            p.product_description_length,
            p.product_photos_qty,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm,
            p.product_volume_cm3
        FROM dim_products p
        LEFT JOIN view_category_performance cat 
            ON p.product_category_name_english = cat.category_name;
        """
        df_products = pd.read_sql_query(query_products, conn)
        if len(df_products) != 32951:
            raise ValueError(f"Product row count mismatch: expected 32,951, got {len(df_products):,}")
        
        prod_path = os.path.join(output_dir, "dim_products.csv")
        df_products.to_csv(prod_path, index=False)
        exported_files["dim_products.csv"] = len(df_products)
        print(f"Done ({len(df_products):,} rows -> {prod_path})")

        # -----------------------------------------------------------------
        # 4. Seller Dimension (dim_sellers.csv)
        # -----------------------------------------------------------------
        print("[4/9] Extracting Seller Dimension ...", end=" ", flush=True)
        df_sellers = pd.read_sql_query("SELECT * FROM dim_sellers;", conn)
        if len(df_sellers) != 3095:
            raise ValueError(f"Seller row count mismatch: expected 3,095, got {len(df_sellers):,}")
        
        seller_path = os.path.join(output_dir, "dim_sellers.csv")
        df_sellers.to_csv(seller_path, index=False)
        exported_files["dim_sellers.csv"] = len(df_sellers)
        print(f"Done ({len(df_sellers):,} rows -> {seller_path})")

        # -----------------------------------------------------------------
        # 5. Geolocation Reference Export (dim_geolocation.csv)
        # -----------------------------------------------------------------
        print("[5/9] Extracting Auxiliary Geolocation Reference ...", end=" ", flush=True)
        df_geo = pd.read_sql_query("SELECT * FROM dim_geolocation;", conn)
        if len(df_geo) != 19010:
            raise ValueError(f"Geolocation row count mismatch: expected 19,010, got {len(df_geo):,}")
        
        geo_path = os.path.join(output_dir, "dim_geolocation.csv")
        df_geo.to_csv(geo_path, index=False)
        exported_files["dim_geolocation.csv"] = len(df_geo)
        print(f"Done ({len(df_geo):,} rows -> {geo_path})")

        # -----------------------------------------------------------------
        # 6. Orders Fact Table (fact_orders.csv)
        # -----------------------------------------------------------------
        print("[6/9] Extracting Orders Fact Table ...", end=" ", flush=True)
        query_orders = """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_status,
            o.order_purchase_timestamp,
            SUBSTR(o.order_purchase_timestamp, 1, 10) AS order_purchase_date,
            o.order_approved_at,
            SUBSTR(o.order_approved_at, 1, 10) AS order_approved_date,
            o.order_delivered_carrier_date,
            SUBSTR(o.order_delivered_carrier_date, 1, 10) AS order_delivered_carrier_date_only,
            o.order_delivered_customer_date,
            SUBSTR(o.order_delivered_customer_date, 1, 10) AS order_delivered_customer_date_only,
            o.order_estimated_delivery_date,
            o.order_purchase_year,
            o.order_purchase_month,
            o.order_purchase_year_month,
            o.order_purchase_day_of_week,
            o.delivery_duration_days,
            o.delivery_delay_days,
            o.is_delayed,
            o.is_delivered,
            v.delivery_performance_bucket
        FROM fact_orders o
        LEFT JOIN view_delivery_performance v ON o.order_id = v.order_id;
        """
        df_orders = pd.read_sql_query(query_orders, conn)
        if len(df_orders) != 99441:
            raise ValueError(f"Orders row count mismatch: expected 99,441, got {len(df_orders):,}")
        if df_orders["order_id"].nunique() != 99441:
            raise ValueError("order_id is not unique in fact_orders")
        if df_orders["customer_id"].nunique() != 99441:
            raise ValueError("customer_id is not unique in fact_orders (1:1 violation)")

        orders_path = os.path.join(output_dir, "fact_orders.csv")
        df_orders.to_csv(orders_path, index=False)
        exported_files["fact_orders.csv"] = len(df_orders)
        print(f"Done ({len(df_orders):,} rows -> {orders_path})")

        # -----------------------------------------------------------------
        # 7. Order Items Fact Table (fact_order_items.csv)
        # -----------------------------------------------------------------
        print("[7/9] Extracting Order Items Fact Table ...", end=" ", flush=True)
        query_items = """
        SELECT
            order_id,
            order_item_id,
            product_id,
            seller_id,
            shipping_limit_date,
            SUBSTR(shipping_limit_date, 1, 10) AS shipping_limit_date_only,
            price,
            freight_value,
            total_item_value
        FROM fact_order_items;
        """
        df_items = pd.read_sql_query(query_items, conn)
        if len(df_items) != 112650:
            raise ValueError(f"Order items row count mismatch: expected 112,650, got {len(df_items):,}")
        
        # Financial validation
        total_price = df_items["price"].sum()
        total_freight = df_items["freight_value"].sum()
        if abs(total_price - 13591643.70) > 0.01:
            raise ValueError(f"Item price reconciliation delta: {total_price} vs 13,591,643.70")
        if abs(total_freight - 2251909.54) > 0.01:
            raise ValueError(f"Freight value reconciliation delta: {total_freight} vs 2,251,909.54")

        items_path = os.path.join(output_dir, "fact_order_items.csv")
        df_items.to_csv(items_path, index=False)
        exported_files["fact_order_items.csv"] = len(df_items)
        print(f"Done ({len(df_items):,} rows -> {items_path})")

        # -----------------------------------------------------------------
        # 8. Order Payments Fact Table (fact_order_payments.csv)
        # -----------------------------------------------------------------
        print("[8/9] Extracting Order Payments Fact Table ...", end=" ", flush=True)
        df_payments = pd.read_sql_query("SELECT * FROM fact_order_payments;", conn)
        if len(df_payments) != 103886:
            raise ValueError(f"Payments row count mismatch: expected 103,886, got {len(df_payments):,}")
        
        total_payment = df_payments["payment_value"].sum()
        if abs(total_payment - 16008872.12) > 0.01:
            raise ValueError(f"Payment value reconciliation delta: {total_payment} vs 16,008,872.12")

        payments_path = os.path.join(output_dir, "fact_order_payments.csv")
        df_payments.to_csv(payments_path, index=False)
        exported_files["fact_order_payments.csv"] = len(df_payments)
        print(f"Done ({len(df_payments):,} rows -> {payments_path})")

        # -----------------------------------------------------------------
        # 9. Order Reviews Fact Table (fact_order_reviews.csv)
        # -----------------------------------------------------------------
        print("[9/9] Extracting Order Reviews Fact Table ...", end=" ", flush=True)
        query_reviews = """
        SELECT
            review_id,
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            has_comment_title,
            has_comment_message,
            review_creation_date,
            SUBSTR(review_creation_date, 1, 10) AS review_creation_date_only,
            review_answer_timestamp,
            SUBSTR(review_answer_timestamp, 1, 10) AS review_answer_date_only,
            review_response_hours
        FROM fact_order_reviews;
        """
        df_reviews = pd.read_sql_query(query_reviews, conn)
        if len(df_reviews) != 99224:
            raise ValueError(f"Reviews row count mismatch: expected 99,224, got {len(df_reviews):,}")

        reviews_path = os.path.join(output_dir, "fact_order_reviews.csv")
        df_reviews.to_csv(reviews_path, index=False)
        exported_files["fact_order_reviews.csv"] = len(df_reviews)
        print(f"Done ({len(df_reviews):,} rows -> {reviews_path})")

    finally:
        conn.close()

    print("\n" + "=" * 80)
    print("ALL 9 POWER BI DATASETS EXPORTED & RECONCILED SUCCESSFULLY")
    print("=" * 80)
    for filename, count in exported_files.items():
        print(f"  - {filename:<28} : {count:>8,} rows")
    
    return exported_files


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(base_dir, "database", "ecommerce.db")
    target_export = os.path.join(base_dir, "data", "processed", "powerbi")
    
    export_powerbi_datasets(target_db, target_export)
