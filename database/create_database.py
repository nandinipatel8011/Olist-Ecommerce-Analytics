"""
SQLite Database Initializer
===========================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This script initializes the local SQLite relational database ('database/ecommerce.db')
by applying the official DDL schema ('database/schema.sql'):
- Enforces foreign key constraints (PRAGMA foreign_keys = ON).
- Creates 5 conformed dimension tables and 4 granular fact tables.
- Builds high-performance indexes on primary and foreign keys.
- Verifies table and index creation against SQLite system catalogs.
"""

import os
import sqlite3
import sys

# Expected 9 tables
EXPECTED_TABLES = [
    "dim_category_translation",
    "dim_products",
    "dim_customers",
    "dim_sellers",
    "dim_geolocation",
    "fact_orders",
    "fact_order_items",
    "fact_order_payments",
    "fact_order_reviews"
]


def init_database(db_path: str = "database/ecommerce.db", schema_path: str = "database/schema.sql") -> sqlite3.Connection:
    """
    Creates or resets the SQLite database and executes the DDL schema.
    Returns an open SQLite connection.
    """
    print("=" * 80)
    print("INITIALIZING SQLITE RELATIONAL DATABASE")
    print("=" * 80)

    # Ensure target directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print(f"Connecting to database: {db_path} ...", end=" ", flush=True)
    conn = sqlite3.connect(db_path)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    print("Connected (PRAGMA foreign_keys = ON)")

    print(f"Applying schema from: {schema_path} ...", end=" ", flush=True)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    print("Schema applied successfully.\n")

    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    print("Created Relational Tables:")
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        col_count = len(cursor.fetchall())
        print(f"  [OK] Table: {t:<28} ({col_count} columns)")

    # Verify indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\nCreated {len(indexes)} Performance Indexes:")
    for idx in indexes:
        print(f"  [OK] Index: {idx}")

    missing_tables = set(EXPECTED_TABLES) - set(tables)
    if missing_tables:
        raise RuntimeError(f"Database initialization failed! Missing tables: {missing_tables}")

    print("\n" + "=" * 80)
    print(f"[SUCCESS] Database successfully initialized with all {len(tables)} tables.")
    print("=" * 80)

    return conn


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(base_dir, "database", "ecommerce.db")
    target_schema = os.path.join(base_dir, "database", "schema.sql")

    connection = init_database(target_db, target_schema)
    connection.close()
