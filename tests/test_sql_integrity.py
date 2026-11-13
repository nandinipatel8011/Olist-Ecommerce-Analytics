"""
Relational Database Integrity & Constraint Test Suite
=====================================================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

Tests the SQLite relational database ('database/ecommerce.db'):
1. Confirms existence and row counts of all 9 tables against CSV baselines.
2. Asserts zero foreign key violations (PRAGMA foreign_key_check).
3. Verifies that duplicate primary key insertions are rejected (UNIQUE constraint).
4. Verifies that invalid foreign key insertions are rejected (FOREIGN KEY constraint).
5. Verifies that out-of-domain insertions are rejected (CHECK constraints).
6. Investigates postal prefix coverage between customers, sellers, and geolocation.
"""

import os
import sqlite3
import unittest
import pandas as pd


class TestDatabaseIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.db_path = os.path.join(base_dir, "database", "ecommerce.db")
        cls.proc_dir = os.path.join(base_dir, "data", "processed")

        if not os.path.exists(cls.db_path):
            raise FileNotFoundError(f"Database file not found: {cls.db_path}")

        cls.conn = sqlite3.connect(cls.db_path)
        cls.conn.execute("PRAGMA foreign_keys = ON;")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_all_tables_exist(self):
        """Verifies that all 9 required relational tables exist in SQLite master catalog."""
        expected = [
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
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        existing_tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        for tbl in expected:
            self.assertIn(tbl, existing_tables, f"Table '{tbl}' is missing from database!")

    def test_02_row_counts_match_processed_csvs(self):
        """Verifies that every SQLite table has exact matching row count to its processed CSV."""
        mapping = {
            "dim_category_translation": "product_category_name_translation.csv",
            "dim_products": "products_cleaned.csv",
            "dim_customers": "customers_cleaned.csv",
            "dim_sellers": "sellers_cleaned.csv",
            "dim_geolocation": "geolocation_cleaned.csv",
            "fact_orders": "orders_cleaned.csv",
            "fact_order_items": "order_items_cleaned.csv",
            "fact_order_payments": "order_payments_cleaned.csv",
            "fact_order_reviews": "order_reviews_cleaned.csv"
        }
        cursor = self.conn.cursor()
        for tbl, csv_name in mapping.items():
            csv_path = os.path.join(self.proc_dir, csv_name)
            df = pd.read_csv(csv_path)
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            db_count = cursor.fetchone()[0]
            self.assertEqual(len(df), db_count, f"Count mismatch in {tbl}: CSV={len(df)}, DB={db_count}")

    def test_03_zero_foreign_key_violations(self):
        """Executes SQLite's internal foreign_key_check to assert 100% referential integrity."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        violations = cursor.fetchall()
        self.assertEqual(len(violations), 0, f"Foreign key violations detected: {violations}")

    def test_04_duplicate_primary_key_rejection(self):
        """Asserts that SQLite rejects duplicate primary key insertions with IntegrityError."""
        cursor = self.conn.cursor()
        # Fetch an existing customer_id
        cursor.execute("SELECT customer_id FROM dim_customers LIMIT 1;")
        existing_id = cursor.fetchone()[0]

        sql = "INSERT INTO dim_customers VALUES (?, 'duplicate_test', 1000, 'TestCity', 'SP');"
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(sql, (existing_id,))

    def test_05_invalid_foreign_key_rejection(self):
        """Asserts that SQLite rejects inserting an order referencing a non-existent customer."""
        cursor = self.conn.cursor()
        sql = """
        INSERT INTO fact_orders (
            order_id, customer_id, order_status, order_purchase_timestamp,
            order_estimated_delivery_date, order_purchase_year, order_purchase_month,
            order_purchase_year_month, order_purchase_day_of_week, is_delivered
        ) VALUES (
            'non_existent_order_id_test', 'NON_EXISTENT_CUSTOMER_UUID_123',
            'delivered', '2018-01-01', '2018-01-10', 2018, 1, '2018-01', 'Monday', 1
        );
        """
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(sql)

    def test_06_check_constraint_review_score(self):
        """Asserts that review_score values outside [1, 5] are rejected by CHECK constraint."""
        cursor = self.conn.cursor()
        # Fetch an existing order_id
        cursor.execute("SELECT order_id FROM fact_orders LIMIT 1;")
        existing_order = cursor.fetchone()[0]

        sql = """
        INSERT INTO fact_order_reviews (
            review_id, order_id, review_score, has_comment_title,
            has_comment_message, review_creation_date, review_answer_timestamp
        ) VALUES ('invalid_score_test', ?, 6, 0, 0, '2018-01-01', '2018-01-02');
        """
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(sql, (existing_order,))

    def test_07_check_constraint_negative_price(self):
        """Asserts that negative prices are rejected by CHECK constraint on fact_order_items."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT order_id, product_id, seller_id FROM fact_order_items LIMIT 1;")
        order_id, product_id, seller_id = cursor.fetchone()

        sql = """
        INSERT INTO fact_order_items (
            order_id, order_item_id, product_id, seller_id,
            shipping_limit_date, price, freight_value, total_item_value
        ) VALUES (?, 999, ?, ?, '2018-01-01', -15.50, 5.00, -10.50);
        """
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(sql, (order_id, product_id, seller_id))

    def test_08_geolocation_postal_coverage_analysis(self):
        """Audits postal prefix alignment between customers, sellers, and geolocation table."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT customer_zip_code_prefix) FROM dim_customers;")
        total_cust_zips = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT c.customer_zip_code_prefix)
            FROM dim_customers c
            LEFT JOIN dim_geolocation g ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
            WHERE g.geolocation_zip_code_prefix IS NULL;
        """)
        unmatched_cust_zips = cursor.fetchone()[0]

        # Assert that unmatched prefixes are exactly documented (158 prefixes)
        self.assertEqual(unmatched_cust_zips, 158)
        self.assertGreater(total_cust_zips, 14000)


if __name__ == "__main__":
    unittest.main()
