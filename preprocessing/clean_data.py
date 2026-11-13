"""
Data Preprocessing and Cleaning Pipeline
=========================================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This module transforms raw Olist CSV datasets into clean, standardized,
and feature-engineered analytical tables:
1. Loads original CSVs without modifying the raw files.
2. Standardizes column names (snake_case, fixes typos like 'lenght' -> 'length').
3. Converts string timestamp columns to native datetime objects.
4. Corrects data types (integers, floats, categories).
5. Imputes missing values gracefully without dropping valid records.
6. Handles undelivered orders by keeping delivery duration and delay NULL.
7. Filters coordinate noise from geolocation using bounding box sanity checks
   and aggregates by zip code prefix using median coordinates.
8. Enriches products with English category translations.
9. Exports cleaned datasets to 'data/processed/'.
"""

import os
import sys
import pandas as pd
import numpy as np


# Translation additions for categories missing in official translation CSV
CATEGORY_TRANSLATION_OVERRIDES = {
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_and_food_preparers",
    "pc_gamer": "pc_gamer",
    "unknown": "unknown"
}


def clean_category_translations(raw_dir: str) -> pd.DataFrame:
    """
    Cleans category translations and incorporates missing Portuguese categories.
    """
    trans_path = os.path.join(raw_dir, "product_category_name_translation.csv")
    df = pd.read_csv(trans_path)

    # Standardize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Append category translation overrides
    new_rows = []
    existing_cats = set(df["product_category_name"])
    for pt, en in CATEGORY_TRANSLATION_OVERRIDES.items():
        if pt not in existing_cats:
            new_rows.append({"product_category_name": pt, "product_category_name_english": en})

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    df["product_category_name"] = df["product_category_name"].str.strip().str.lower()
    df["product_category_name_english"] = df["product_category_name_english"].str.strip().str.lower()

    return df


def clean_customers(raw_dir: str) -> pd.DataFrame:
    """
    Cleans customer dimension table:
    - customer_id: order-scoped surrogate key
    - customer_unique_id: natural real-world customer identifier
    - Standardizes text case (city title case, state upper case)
    """
    path = os.path.join(raw_dir, "olist_customers_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["customer_unique_id"] = df["customer_unique_id"].astype(str).str.strip()
    df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].astype(int)
    df["customer_city"] = df["customer_city"].astype(str).str.strip().str.title()
    df["customer_state"] = df["customer_state"].astype(str).str.strip().str.upper()

    return df


def clean_sellers(raw_dir: str) -> pd.DataFrame:
    """
    Cleans sellers dimension table.
    """
    path = os.path.join(raw_dir, "olist_sellers_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]
    df["seller_id"] = df["seller_id"].astype(str).str.strip()
    df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype(int)
    df["seller_city"] = df["seller_city"].astype(str).str.strip().str.title()
    df["seller_state"] = df["seller_state"].astype(str).str.strip().str.upper()

    return df


def clean_products(raw_dir: str, trans_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans products dimension:
    - Imputes missing categories as 'unknown'
    - Corrects column typos: 'product_name_lenght' -> 'product_name_length'
    - Enriches with English translation via left join
    - Computes product volume in cm3
    """
    path = os.path.join(raw_dir, "olist_products_dataset.csv")
    df = pd.read_csv(path)

    # Standardize typos
    df = df.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length"
    })
    df.columns = [c.strip().lower() for c in df.columns]

    # Impute missing categories
    df["product_category_name"] = df["product_category_name"].fillna("unknown").str.strip().str.lower()

    # Join English translation
    df = df.merge(trans_df, on="product_category_name", how="left")
    df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")

    # Compute physical dimensions volume
    df["product_volume_cm3"] = (
        df["product_length_cm"] * df["product_height_cm"] * df["product_width_cm"]
    )

    return df


def clean_orders(raw_dir: str) -> pd.DataFrame:
    """
    Cleans orders fact table:
    - Parses 5 timestamp columns to datetime
    - Engineers calendar dimensions: purchase year, month, year_month, day of week
    - Computes delivery duration and delay ONLY when dates are valid
    - Keeps delivery duration, delivery delay, and is_delayed as NULL for undelivered orders
    """
    path = os.path.join(raw_dir, "olist_orders_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]

    # Convert timestamps to datetime
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Calendar feature engineering
    df["order_purchase_year"] = df["order_purchase_timestamp"].dt.year
    df["order_purchase_month"] = df["order_purchase_timestamp"].dt.month
    df["order_purchase_year_month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")
    df["order_purchase_day_of_week"] = df["order_purchase_timestamp"].dt.day_name()

    # Delivery performance calculations (strictly for valid delivered orders)
    is_delivered = df["order_delivered_customer_date"].notnull()
    valid_duration = is_delivered & (df["order_delivered_customer_date"] >= df["order_purchase_timestamp"])

    # Duration in fractional days: purchase -> delivery
    df["delivery_duration_days"] = np.nan
    df.loc[valid_duration, "delivery_duration_days"] = (
        df.loc[valid_duration, "order_delivered_customer_date"] - df.loc[valid_duration, "order_purchase_timestamp"]
    ).dt.total_seconds() / 86400.0

    # Delay in days: actual delivery - promised estimated delivery date
    # Positive = late; Zero/Negative = delivered on time or early
    df["delivery_delay_days"] = np.nan
    df.loc[is_delivered, "delivery_delay_days"] = (
        df.loc[is_delivered, "order_delivered_customer_date"] - df.loc[is_delivered, "order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400.0

    # Binary flag: 1 = delayed, 0 = on-time/early, NaN = undelivered
    df["is_delayed"] = np.nan
    df.loc[is_delivered, "is_delayed"] = (df.loc[is_delivered, "delivery_delay_days"] > 0).astype(int)

    # Status flag: is order marked delivered
    df["is_delivered"] = (df["order_status"] == "delivered").astype(int)

    return df


def clean_order_items(raw_dir: str) -> pd.DataFrame:
    """
    Cleans order items fact table:
    - Parses shipping_limit_date to datetime
    - Formats price and freight_value
    - Computes total item line value (price + freight)
    """
    path = os.path.join(raw_dir, "olist_order_items_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["price"] = df["price"].astype(float).round(2)
    df["freight_value"] = df["freight_value"].astype(float).round(2)
    df["total_item_value"] = (df["price"] + df["freight_value"]).round(2)

    return df


def clean_order_payments(raw_dir: str) -> pd.DataFrame:
    """
    Cleans payments fact table:
    - Standardizes payment method text
    - Identifies installment transactions (installments > 1)
    """
    path = os.path.join(raw_dir, "olist_order_payments_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]
    df["payment_type"] = df["payment_type"].astype(str).str.strip().str.lower()
    df["payment_installments"] = df["payment_installments"].astype(int)
    df["payment_value"] = df["payment_value"].astype(float).round(2)
    df["is_installment"] = (df["payment_installments"] > 1).astype(int)

    return df


def clean_order_reviews(raw_dir: str) -> pd.DataFrame:
    """
    Cleans reviews fact table:
    - Preserves all review records without dropping optional comments
    - Parses creation date and answer timestamp
    - Computes customer review response time in hours
    - Flags presence of text comments
    """
    path = os.path.join(raw_dir, "olist_order_reviews_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]
    df["review_score"] = df["review_score"].astype(int)
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    # Survey response latency in hours
    df["review_response_hours"] = (
        df["review_answer_timestamp"] - df["review_creation_date"]
    ).dt.total_seconds() / 3600.0

    # Flags for presence of textual feedback
    df["has_comment_title"] = df["review_comment_title"].notnull().astype(int)
    df["has_comment_message"] = df["review_comment_message"].notnull().astype(int)

    # Impute empty strings for missing comment text (avoids NaN handling issues in SQL/BI)
    df["review_comment_title"] = df["review_comment_title"].fillna("")
    df["review_comment_message"] = df["review_comment_message"].fillna("")

    return df


def clean_geolocation(raw_dir: str) -> pd.DataFrame:
    """
    Cleans and optimizes the 1,000,163-row geolocation table:
    1. Documents coordinate validation method:
       Filters coordinates using an empirical bounding box sanity check:
       lat in [-34.0, +5.5], lng in [-74.0, -34.5].
       This removes 42 corrupt sensor readings (e.g., positive latitudes in Europe).
       Note: This is an empirical bounding box filter, not an exact border polygon.
    2. Groups by 'geolocation_zip_code_prefix' and aggregates:
       - median_latitude = median(geolocation_lat)
       - median_longitude = median(geolocation_lng)
       - city = dominant / mode city
       - state = dominant / mode state
    3. Reduces 1M+ rows to ~19k rows, dramatically optimizing SQLite/Power BI performance.
    """
    path = os.path.join(raw_dir, "olist_geolocation_dataset.csv")
    df = pd.read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]

    # Coordinate sanity filter (Brazil bounding box)
    valid_coords = df[
        (df["geolocation_lat"] >= -34.0) & (df["geolocation_lat"] <= 5.5) &
        (df["geolocation_lng"] >= -74.0) & (df["geolocation_lng"] <= -34.5)
    ].copy()

    # Standardize text
    valid_coords["geolocation_city"] = valid_coords["geolocation_city"].astype(str).str.strip().str.title()
    valid_coords["geolocation_state"] = valid_coords["geolocation_state"].astype(str).str.strip().str.upper()

    # Helper for mode
    def get_mode(series):
        m = series.mode()
        return m.iloc[0] if not m.empty else series.iloc[0]

    # Aggregate by 5-digit zip code prefix
    aggregated = valid_coords.groupby("geolocation_zip_code_prefix", as_index=False).agg(
        geolocation_lat=("geolocation_lat", "median"),
        geolocation_lng=("geolocation_lng", "median"),
        geolocation_city=("geolocation_city", get_mode),
        geolocation_state=("geolocation_state", get_mode)
    )

    aggregated["geolocation_lat"] = aggregated["geolocation_lat"].round(6)
    aggregated["geolocation_lng"] = aggregated["geolocation_lng"].round(6)

    return aggregated


def run_pipeline(raw_dir: str = "data/raw", processed_dir: str = "data/processed") -> dict:
    """
    Executes the full preprocessing pipeline and saves cleaned CSVs.
    """
    os.makedirs(processed_dir, exist_ok=True)
    print("=" * 80)
    print("STARTING OLIST E-COMMERCE DATA PREPROCESSING PIPELINE")
    print("=" * 80)

    # 1. Translation
    print("\n1. Cleaning category translations...", end=" ", flush=True)
    trans_clean = clean_category_translations(raw_dir)
    trans_clean.to_csv(os.path.join(processed_dir, "product_category_name_translation.csv"), index=False)
    print(f"Done ({len(trans_clean):,} rows)")

    # 2. Customers
    print("2. Cleaning customer dimension...", end=" ", flush=True)
    cust_clean = clean_customers(raw_dir)
    cust_clean.to_csv(os.path.join(processed_dir, "customers_cleaned.csv"), index=False)
    print(f"Done ({len(cust_clean):,} rows)")

    # 3. Sellers
    print("3. Cleaning seller dimension...", end=" ", flush=True)
    sellers_clean = clean_sellers(raw_dir)
    sellers_clean.to_csv(os.path.join(processed_dir, "sellers_cleaned.csv"), index=False)
    print(f"Done ({len(sellers_clean):,} rows)")

    # 4. Products
    print("4. Cleaning product dimension & translation join...", end=" ", flush=True)
    prods_clean = clean_products(raw_dir, trans_clean)
    prods_clean.to_csv(os.path.join(processed_dir, "products_cleaned.csv"), index=False)
    print(f"Done ({len(prods_clean):,} rows)")

    # 5. Orders
    print("5. Cleaning orders fact & engineering delivery metrics...", end=" ", flush=True)
    orders_clean = clean_orders(raw_dir)
    orders_clean.to_csv(os.path.join(processed_dir, "orders_cleaned.csv"), index=False)
    print(f"Done ({len(orders_clean):,} rows)")

    # 6. Order Items
    print("6. Cleaning order items fact...", end=" ", flush=True)
    items_clean = clean_order_items(raw_dir)
    items_clean.to_csv(os.path.join(processed_dir, "order_items_cleaned.csv"), index=False)
    print(f"Done ({len(items_clean):,} rows)")

    # 7. Payments
    print("7. Cleaning order payments fact...", end=" ", flush=True)
    payments_clean = clean_order_payments(raw_dir)
    payments_clean.to_csv(os.path.join(processed_dir, "order_payments_cleaned.csv"), index=False)
    print(f"Done ({len(payments_clean):,} rows)")

    # 8. Reviews
    print("8. Cleaning order reviews fact...", end=" ", flush=True)
    reviews_clean = clean_order_reviews(raw_dir)
    reviews_clean.to_csv(os.path.join(processed_dir, "order_reviews_cleaned.csv"), index=False)
    print(f"Done ({len(reviews_clean):,} rows)")

    # 9. Geolocation
    print("9. Cleaning & aggregating geolocation coordinates...", end=" ", flush=True)
    geo_clean = clean_geolocation(raw_dir)
    geo_clean.to_csv(os.path.join(processed_dir, "geolocation_cleaned.csv"), index=False)
    print(f"Done ({len(geo_clean):,} unique zip prefixes)")

    print("\n" + "=" * 80)
    print("[SUCCESS] All cleaned datasets successfully exported to 'data/processed/'.")
    print("=" * 80)

    return {
        "customers": cust_clean,
        "sellers": sellers_clean,
        "products": prods_clean,
        "orders": orders_clean,
        "order_items": items_clean,
        "order_payments": payments_clean,
        "order_reviews": reviews_clean,
        "geolocation": geo_clean,
        "translations": trans_clean
    }


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw")
    proc_path = os.path.join(base_dir, "data", "processed")
    run_pipeline(raw_path, proc_path)
