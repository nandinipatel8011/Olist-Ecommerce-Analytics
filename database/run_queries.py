"""
Analytical Query Runner & View Manager
======================================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This script:
1. Applies analytical reporting views ('database/views.sql') to 'database/ecommerce.db'.
2. Executes all 6 production SQL queries in 'database/queries/'.
3. Validates and displays formatted summary results.
4. Exports clean analytical reporting CSVs to 'data/processed/powerbi/' for Power BI ingestion.
"""

import os
import sqlite3
import sys
import pandas as pd

QUERY_FILES = [
    ("01_monthly_sales_trends.sql", "monthly_sales_trends.csv"),
    ("02_product_category_performance.sql", "category_performance.csv"),
    ("03_customer_rfm_behavior.sql", "customer_rfm_segments.csv"),
    ("04_regional_geography_analysis.sql", "regional_sales_performance.csv"),
    ("05_payment_channel_breakdown.sql", "payment_channel_breakdown.csv"),
    ("06_delivery_efficiency_and_reviews.sql", "delivery_delay_vs_reviews.csv")
]

EXPECTED_VIEWS = [
    "view_monthly_sales",
    "view_category_performance",
    "view_customer_rfm",
    "view_delivery_performance"
]


def apply_views(conn: sqlite3.Connection, views_path: str):
    """Executes views.sql DDL to create reporting views in SQLite."""
    print("=" * 80)
    print("APPLYING REPORTING VIEWS")
    print("=" * 80)
    with open(views_path, "r", encoding="utf-8") as f:
        views_sql = f.read()

    cursor = conn.cursor()
    cursor.executescript(views_sql)
    conn.commit()

    # Verify views in system catalog
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;")
    created_views = [row[0] for row in cursor.fetchall()]

    for v in EXPECTED_VIEWS:
        if v in created_views:
            cursor.execute(f"SELECT COUNT(*) FROM {v};")
            count = cursor.fetchone()[0]
            print(f"  [OK] View: {v:<28} ({count:,} rows)")
        else:
            raise RuntimeError(f"Failed to create view: {v}")

    print("[SUCCESS] All 4 reporting views created successfully.\n")


def execute_queries_and_export(conn: sqlite3.Connection, queries_dir: str, export_dir: str) -> dict:
    """Executes each SQL query script and exports results to CSV."""
    os.makedirs(export_dir, exist_ok=True)
    results = {}

    print("=" * 80)
    print("EXECUTING ANALYTICAL SQL SCRIPTS & EXPORTING MARTS")
    print("=" * 80)

    for sql_file, csv_export in QUERY_FILES:
        file_path = os.path.join(queries_dir, sql_file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Query file missing: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            query_sql = f.read()

        print(f"\nRunning: {sql_file} ...", end=" ", flush=True)
        df = pd.read_sql_query(query_sql, conn)
        print(f"Done ({len(df):,} rows returned, {len(df.columns)} columns)")

        # Export to CSV
        export_path = os.path.join(export_dir, csv_export)
        df.to_csv(export_path, index=False)
        print(f"  Exported -> {export_path}")

        results[sql_file] = {
            "df": df,
            "export_file": csv_export,
            "rows": len(df),
            "cols": len(df.columns)
        }

    return results


def run_all(db_path: str = "database/ecommerce.db",
            views_path: str = "database/views.sql",
            queries_dir: str = "database/queries",
            export_dir: str = "data/processed/powerbi"):
    """Orchestrates view creation and query execution."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        apply_views(conn, views_path)
        results = execute_queries_and_export(conn, queries_dir, export_dir)

        print("\n" + "=" * 80)
        print("SQL ANALYTICAL SUMMARY OF RESULTS")
        print("=" * 80)
        for sql_file, data in results.items():
            print(f"\n--- Output of {sql_file} (First 5 Rows) ---")
            print(data["df"].head(5).to_string(index=False))

    finally:
        conn.close()

    return results


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(base_dir, "database", "ecommerce.db")
    target_views = os.path.join(base_dir, "database", "views.sql")
    target_queries = os.path.join(base_dir, "database", "queries")
    target_export = os.path.join(base_dir, "data", "processed", "powerbi")

    run_all(target_db, target_views, target_queries, target_export)
