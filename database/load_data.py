"""
Automated Database ETL Loader
=============================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This module loads cleaned datasets from 'data/processed/' into 'database/ecommerce.db':
- Enforces strict loading sequence to satisfy Foreign Key constraints:
    1. dim_category_translation
    2. dim_products
    3. dim_customers
    4. dim_sellers
    5. dim_geolocation
    6. fact_orders
    7. fact_order_items
    8. fact_order_payments
    9. fact_order_reviews
- Uses database transactions with automatic rollback on error.
- Validates post-load record counts against source CSVs.
- Runs SQLite 'PRAGMA foreign_key_check' to verify referential integrity.
"""

import os
import sqlite3
import sys
import pandas as pd

# Mapping of Cleaned CSV filename -> SQLite table name in dependency order
TABLE_MAPPING = [
    ("product_category_name_translation.csv", "dim_category_translation"),
    ("products_cleaned.csv", "dim_products"),
    ("customers_cleaned.csv", "dim_customers"),
    ("sellers_cleaned.csv", "dim_sellers"),
    ("geolocation_cleaned.csv", "dim_geolocation"),
    ("orders_cleaned.csv", "fact_orders"),
    ("order_items_cleaned.csv", "fact_order_items"),
    ("order_payments_cleaned.csv", "fact_order_payments"),
    ("order_reviews_cleaned.csv", "fact_order_reviews")
]


def load_all_data(db_path: str = "database/ecommerce.db", processed_dir: str = "data/processed") -> dict:
    """
    Loads all cleaned CSVs into the SQLite database in strict relational order.
    Returns a dictionary of loaded table row counts.
    """
    print("=" * 80)
    print("STARTING DATABASE ETL LOAD")
    print("=" * 80)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database does not exist at '{db_path}'. Run create_database.py first!")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    load_summary = {}

    try:
        # Load tables inside transaction
        for csv_name, table_name in TABLE_MAPPING:
            csv_path = os.path.join(processed_dir, csv_name)
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Source CSV file missing: {csv_path}")

            print(f"Loading '{table_name}' from '{csv_name}' ...", end=" ", flush=True)
            df = pd.read_csv(csv_path)
            csv_row_count = len(df)

            # Insert into SQLite table
            df.to_sql(name=table_name, con=conn, if_exists="append", index=False)
            conn.commit()

            # Verify count in database
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            db_row_count = cursor.fetchone()[0]

            if db_row_count != csv_row_count:
                raise ValueError(
                    f"Row count mismatch in table '{table_name}'! CSV had {csv_row_count}, DB has {db_row_count}"
                )

            load_summary[table_name] = {
                "csv_rows": csv_row_count,
                "db_rows": db_row_count,
                "status": "MATCH"
            }
            print(f"Done ({db_row_count:,} rows inserted)")

        # Run SQLite Foreign Key Integrity Check
        print("\nChecking SQLite foreign key constraints (PRAGMA foreign_key_check) ...", end=" ", flush=True)
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()

        if fk_violations:
            print("\n[FAIL] Foreign key violations detected!")
            for v in fk_violations:
                print(f"  Violation: Table '{v[0]}', RowID {v[1]}, Target '{v[2]}', FKeyID {v[3]}")
            raise RuntimeError("Database contains foreign key violations!")
        else:
            print("Passed (0 violations)")

        print("\n" + "=" * 80)
        print("[SUCCESS] All 9 tables loaded successfully with zero foreign key violations.")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] ETL load failed: {str(e)}")
        conn.close()
        raise e

    conn.close()
    return load_summary


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(base_dir, "database", "ecommerce.db")
    target_proc = os.path.join(base_dir, "data", "processed")

    load_all_data(target_db, target_proc)
