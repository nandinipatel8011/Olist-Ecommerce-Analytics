"""
Data Ingestion and Inspection Script for Olist E-Commerce Dataset
================================================================
This script inspects the raw CSV datasets extracted from the Kaggle Olist archive:
1. Verifies the presence of all 9 expected CSV files.
2. Inspects dataset dimensions (row and column counts).
3. Inspects column names, inferred data types, and memory usage.
4. Audits missing values and duplicate rows.
5. Performs a deep-dive inspection of the 1M+ row geolocation dataset.
6. Returns an audit summary dictionary for reporting and quality validation.

Author: Nandini Patel (GitHub: nandinipatel8011)
Project: E-Commerce Sales & Business Intelligence Analytics Platform
"""

import os
import sys
import pandas as pd
import numpy as np

# Expected 9 Olist CSV filenames
EXPECTED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv"
]


def verify_raw_files_exist(raw_dir: str = "data/raw") -> dict:
    """
    Checks that all 9 expected Olist CSV files exist in the target directory.
    Returns a dictionary mapping filename to file size in bytes.
    """
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

    file_status = {}
    missing = []

    for filename in EXPECTED_FILES:
        file_path = os.path.join(raw_dir, filename)
        if os.path.exists(file_path):
            file_status[filename] = {
                "exists": True,
                "size_bytes": os.path.getsize(file_path),
                "size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
                "path": file_path
            }
        else:
            file_status[filename] = {"exists": False, "size_bytes": 0, "size_mb": 0.0, "path": file_path}
            missing.append(filename)

    if missing:
        raise FileNotFoundError(f"Missing expected Olist files in {raw_dir}: {missing}")

    return file_status


def inspect_csv(file_path: str) -> dict:
    """
    Inspects a single CSV file:
    - Row and column count
    - Column names and data types
    - Null counts and percentages
    - Exact duplicate rows
    - Memory usage
    """
    df = pd.read_csv(file_path)
    total_rows = len(df)
    total_cols = len(df.columns)
    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    duplicates = int(df.duplicated().sum())

    columns_info = []
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        columns_info.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "sample_value": str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else None
        })

    return {
        "filename": os.path.basename(file_path),
        "total_rows": total_rows,
        "total_columns": total_cols,
        "memory_mb": memory_mb,
        "duplicate_rows": duplicates,
        "columns": columns_info
    }


def inspect_geolocation_deep_dive(file_path: str) -> dict:
    """
    Specialized inspection of the 1,000,163 row geolocation dataset.
    Documents the density of duplicate postal code prefixes and coordinate distributions.
    """
    df = pd.read_csv(file_path)
    total_rows = len(df)
    unique_prefixes = int(df["geolocation_zip_code_prefix"].nunique())
    duplicate_prefix_rows = total_rows - unique_prefixes
    compression_ratio = round((1 - (unique_prefixes / total_rows)) * 100, 2)

    lat_stats = {
        "min": float(df["geolocation_lat"].min()),
        "max": float(df["geolocation_lat"].max()),
        "median": float(df["geolocation_lat"].median())
    }
    lng_stats = {
        "min": float(df["geolocation_lng"].min()),
        "max": float(df["geolocation_lng"].max()),
        "median": float(df["geolocation_lng"].median())
    }

    return {
        "total_rows": total_rows,
        "unique_zip_prefixes": unique_prefixes,
        "duplicate_prefix_rows": duplicate_prefix_rows,
        "redundancy_pct": compression_ratio,
        "lat_stats": lat_stats,
        "lng_stats": lng_stats,
        "unique_cities": int(df["geolocation_city"].nunique()),
        "unique_states": int(df["geolocation_state"].nunique())
    }


def run_full_inspection(raw_dir: str = "data/raw") -> dict:
    """
    Executes inspection across all 9 files and prints a formatted summary.
    """
    print("=" * 80)
    print("OLIST BRAZILIAN E-COMMERCE DATASET - RAW DATA INSPECTION")
    print("=" * 80)

    file_status = verify_raw_files_exist(raw_dir)
    print(f"\n[OK] All {len(file_status)} expected CSV files are present in '{raw_dir}'.\n")

    inspection_results = {}
    summary_table = []

    for filename in EXPECTED_FILES:
        path = file_status[filename]["path"]
        print(f"Inspecting: {filename} ...", end=" ", flush=True)
        info = inspect_csv(path)
        inspection_results[filename] = info
        summary_table.append({
            "File": filename,
            "Rows": f"{info['total_rows']:,}",
            "Cols": info["total_columns"],
            "Nulls": sum(c["null_count"] for c in info["columns"]),
            "Duplicates": info["duplicate_rows"],
            "File Size (MB)": file_status[filename]["size_mb"],
            "RAM (MB)": info["memory_mb"]
        })
        print(f"Done ({info['total_rows']:,} rows, {info['total_columns']} cols)")

    summary_df = pd.DataFrame(summary_table)
    print("\n" + "=" * 80)
    print("RAW DATASET SUMMARY TABLE")
    print("=" * 80)
    print(summary_df.to_string(index=False))

    geo_info = inspect_geolocation_deep_dive(file_status["olist_geolocation_dataset.csv"]["path"])
    print("\n" + "=" * 80)
    print("GEOLOCATION TABLE DEEP-DIVE")
    print("=" * 80)
    print(f"Total Raw Rows:                 {geo_info['total_rows']:,}")
    print(f"Unique Zip Code Prefixes:       {geo_info['unique_zip_prefixes']:,}")
    print(f"Duplicate Prefix Rows:          {geo_info['duplicate_prefix_rows']:,}")
    print(f"Redundancy / Compression Ratio: {geo_info['redundancy_pct']}%")
    print(f"Latitude Range:                 [{geo_info['lat_stats']['min']:.4f}, {geo_info['lat_stats']['max']:.4f}] (Median: {geo_info['lat_stats']['median']:.4f})")
    print(f"Longitude Range:                [{geo_info['lng_stats']['min']:.4f}, {geo_info['lng_stats']['max']:.4f}] (Median: {geo_info['lng_stats']['median']:.4f})")
    print(f"Unique Cities:                  {geo_info['unique_cities']:,}")
    print(f"Unique States:                  {geo_info['unique_states']}")

    return {
        "files": inspection_results,
        "geolocation_deep_dive": geo_info
    }


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_raw_dir = os.path.join(base_dir, "data", "raw")
    run_full_inspection(target_raw_dir)
