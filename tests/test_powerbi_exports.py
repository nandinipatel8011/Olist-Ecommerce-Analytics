"""
Automated Test Suite: Power BI Analytical Datasets & Data Marts
==============================================================
Project: E-Commerce Sales & Business Intelligence Analytics Platform
Author: Nandini Patel (GitHub: nandinipatel8011)

This test suite validates the integrity, schema conformance, cardinality,
and financial reconciliation of the exported Power BI CSV datasets located in
'data/processed/powerbi/'.

Tests Performed:
  1. test_01_exported_files_exist_and_readable: All 9 CSV files exist and can be loaded.
  2. test_02_row_counts_parity: Exact row counts match database and benchmark specs.
  3. test_03_primary_key_uniqueness: Primary and composite keys are unique.
  4. test_04_customer_orders_one_to_one_cardinality: Strict 1:1 join with zero orphans.
  5. test_05_customer_rfm_reconciliation: 96,096 distinct buyers and exact segment counts.
  6. test_06_financial_reconciliation: Item, freight, gross, and payment sums match exact figures.
  7. test_07_foreign_key_referential_integrity: All child facts have zero orphan foreign keys.
  8. test_08_date_dimension_continuity_and_coverage: 1,827 continuous days with 100% fact date coverage.
  9. test_09_product_pareto_enrichment: Pareto classes and category ranks properly assigned.
"""

import os
import unittest
import pandas as pd
import numpy as np


class TestPowerBIExports(unittest.TestCase):
    """Test suite for Power BI exported datasets."""

    @classmethod
    def setUpClass(cls):
        """Load all exported CSV files once for the entire test class."""
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.export_dir = os.path.join(cls.base_dir, "data", "processed", "powerbi")

        cls.expected_files = {
            "dim_date.csv": 1827,
            "dim_customers.csv": 99441,
            "dim_products.csv": 32951,
            "dim_sellers.csv": 3095,
            "dim_geolocation.csv": 19010,
            "fact_orders.csv": 99441,
            "fact_order_items.csv": 112650,
            "fact_order_payments.csv": 103886,
            "fact_order_reviews.csv": 99224,
        }

        cls.dfs = {}
        for filename in cls.expected_files:
            filepath = os.path.join(cls.export_dir, filename)
            if os.path.exists(filepath):
                cls.dfs[filename] = pd.read_csv(filepath, low_memory=False)

    def test_01_exported_files_exist_and_readable(self):
        """Verify that all 9 expected Power BI datasets exist on disk and are readable."""
        for filename in self.expected_files:
            filepath = os.path.join(self.export_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"Missing expected export file: {filepath}")
            self.assertIn(filename, self.dfs, f"File {filename} could not be loaded into DataFrame")
            self.assertGreater(len(self.dfs[filename]), 0, f"File {filename} is empty")

    def test_02_row_counts_parity(self):
        """Verify exact row counts for each dataset against database specifications."""
        for filename, expected_count in self.expected_files.items():
            actual_count = len(self.dfs[filename])
            self.assertEqual(
                actual_count,
                expected_count,
                f"Row count mismatch for {filename}: expected {expected_count:,}, got {actual_count:,}"
            )

    def test_03_primary_key_uniqueness(self):
        """Verify primary and composite key uniqueness across dimension and fact tables."""
        # dim_date: date_key and date
        df_date = self.dfs["dim_date.csv"]
        self.assertEqual(df_date["date_key"].nunique(), len(df_date), "dim_date[date_key] is not unique")
        self.assertEqual(df_date["date"].nunique(), len(df_date), "dim_date[date] is not unique")

        # dim_customers: customer_id
        df_cust = self.dfs["dim_customers.csv"]
        self.assertEqual(df_cust["customer_id"].nunique(), len(df_cust), "dim_customers[customer_id] is not unique")

        # dim_products: product_id
        df_prod = self.dfs["dim_products.csv"]
        self.assertEqual(df_prod["product_id"].nunique(), len(df_prod), "dim_products[product_id] is not unique")

        # dim_sellers: seller_id
        df_seller = self.dfs["dim_sellers.csv"]
        self.assertEqual(df_seller["seller_id"].nunique(), len(df_seller), "dim_sellers[seller_id] is not unique")

        # dim_geolocation: geolocation_zip_code_prefix
        df_geo = self.dfs["dim_geolocation.csv"]
        self.assertEqual(
            df_geo["geolocation_zip_code_prefix"].nunique(),
            len(df_geo),
            "dim_geolocation[geolocation_zip_code_prefix] is not unique"
        )

        # fact_orders: order_id
        df_orders = self.dfs["fact_orders.csv"]
        self.assertEqual(df_orders["order_id"].nunique(), len(df_orders), "fact_orders[order_id] is not unique")

        # fact_order_items: (order_id, order_item_id) composite key
        df_items = self.dfs["fact_order_items.csv"]
        items_composite = df_items["order_id"].astype(str) + "_" + df_items["order_item_id"].astype(str)
        self.assertEqual(
            items_composite.nunique(),
            len(df_items),
            "fact_order_items composite key (order_id, order_item_id) is not unique"
        )

        # fact_order_payments: (order_id, payment_sequential) composite key
        df_payments = self.dfs["fact_order_payments.csv"]
        payments_composite = df_payments["order_id"].astype(str) + "_" + df_payments["payment_sequential"].astype(str)
        self.assertEqual(
            payments_composite.nunique(),
            len(df_payments),
            "fact_order_payments composite key (order_id, payment_sequential) is not unique"
        )

        # fact_order_reviews: (review_id, order_id) composite key
        df_reviews = self.dfs["fact_order_reviews.csv"]
        reviews_composite = df_reviews["review_id"].astype(str) + "_" + df_reviews["order_id"].astype(str)
        self.assertEqual(
            reviews_composite.nunique(),
            len(df_reviews),
            "fact_order_reviews composite key (review_id, order_id) is not unique"
        )

    def test_04_customer_orders_one_to_one_cardinality(self):
        """Verify strict 1:1 relationship between dim_customers and fact_orders with 0 orphans."""
        df_cust = self.dfs["dim_customers.csv"]
        df_orders = self.dfs["fact_orders.csv"]

        cust_ids = set(df_cust["customer_id"])
        order_cust_ids = set(df_orders["customer_id"])

        self.assertEqual(len(cust_ids), 99441, "dim_customers must have exactly 99,441 unique customer_id values")
        self.assertEqual(len(order_cust_ids), 99441, "fact_orders must have exactly 99,441 unique customer_id values")
        self.assertEqual(cust_ids, order_cust_ids, "Strict set equality failed between customer_id sets (1:1 violation)")
        self.assertEqual(len(order_cust_ids - cust_ids), 0, "Found orphan customer_id in fact_orders")
        self.assertEqual(len(cust_ids - order_cust_ids), 0, "Found unmapped customer_id in dim_customers")

    def test_05_customer_rfm_reconciliation(self):
        """Verify that customer dimension preserves exactly 96,096 distinct buyers and RFM cohort counts."""
        df_cust = self.dfs["dim_customers.csv"]

        # Distinct buyers
        distinct_buyers = df_cust["customer_unique_id"].nunique()
        self.assertEqual(distinct_buyers, 96096, f"Expected 96,096 distinct buyers, got {distinct_buyers:,}")

        # Unique buyer slice
        unique_buyers_df = df_cust.drop_duplicates(subset=["customer_unique_id"])
        self.assertEqual(len(unique_buyers_df), 96096)

        # Single-order vs repeat buyer counts
        single_order_buyers = (unique_buyers_df["order_frequency"] == 1).sum()
        repeat_order_buyers = (unique_buyers_df["order_frequency"] > 1).sum()

        self.assertEqual(single_order_buyers, 93099, f"Expected 93,099 single-order buyers, got {single_order_buyers:,}")
        self.assertEqual(repeat_order_buyers, 2997, f"Expected 2,997 repeat buyers, got {repeat_order_buyers:,}")
        self.assertEqual(single_order_buyers + repeat_order_buyers, 96096)

        # Reconciled RFM segment distribution
        expected_segments = {
            "New & Promising": 37032,
            "Lost / Inactive": 22995,
            "Needs Attention": 18466,
            "Hibernating High-Spenders": 13938,
            "Champions & Loyal": 1305,
            "At Risk Repeaters": 1047,
            "Unfulfilled / Canceled": 676,
            "Potential Loyalists": 637,
        }

        actual_segments = unique_buyers_df["customer_segment"].value_counts().to_dict()
        self.assertEqual(
            actual_segments,
            expected_segments,
            f"RFM segment distribution mismatch:\nExpected: {expected_segments}\nGot: {actual_segments}"
        )

    def test_06_financial_reconciliation(self):
        """Verify decimal financial reconciliation across items and payments."""
        df_items = self.dfs["fact_order_items.csv"]
        df_payments = self.dfs["fact_order_payments.csv"]

        total_item_price = round(df_items["price"].sum(), 2)
        total_freight_val = round(df_items["freight_value"].sum(), 2)
        total_order_val = round(df_items["total_item_value"].sum(), 2)
        total_payment_val = round(df_payments["payment_value"].sum(), 2)

        # Reconcile Item Product Revenue: R$ 13,591,643.70
        self.assertAlmostEqual(
            total_item_price,
            13591643.70,
            places=2,
            msg=f"Item price mismatch: expected 13,591,643.70, got {total_item_price}"
        )

        # Reconcile Freight Revenue: R$ 2,251,909.54
        self.assertAlmostEqual(
            total_freight_val,
            2251909.54,
            places=2,
            msg=f"Freight value mismatch: expected 2,251,909.54, got {total_freight_val}"
        )

        # Reconcile Freight-Inclusive Order Value: R$ 15,843,553.24
        self.assertAlmostEqual(
            total_order_val,
            15843553.24,
            places=2,
            msg=f"Order value mismatch: expected 15,843,553.24, got {total_order_val}"
        )

        # Reconcile Total Recorded Payment Value: R$ 16,008,872.12
        self.assertAlmostEqual(
            total_payment_val,
            16008872.12,
            places=2,
            msg=f"Payment value mismatch: expected 16,008,872.12, got {total_payment_val}"
        )

        # Documented variance
        variance = round(total_payment_val - total_order_val, 2)
        self.assertAlmostEqual(variance, 165318.88, places=2)

    def test_07_foreign_key_referential_integrity(self):
        """Verify referential integrity across all child fact tables (zero orphan records)."""
        df_cust = self.dfs["dim_customers.csv"]
        df_prod = self.dfs["dim_products.csv"]
        df_seller = self.dfs["dim_sellers.csv"]
        df_orders = self.dfs["fact_orders.csv"]
        df_items = self.dfs["fact_order_items.csv"]
        df_payments = self.dfs["fact_order_payments.csv"]
        df_reviews = self.dfs["fact_order_reviews.csv"]

        cust_id_set = set(df_cust["customer_id"])
        order_id_set = set(df_orders["order_id"])
        prod_id_set = set(df_prod["product_id"])
        seller_id_set = set(df_seller["seller_id"])

        # fact_orders -> dim_customers
        self.assertEqual(len(set(df_orders["customer_id"]) - cust_id_set), 0)

        # fact_order_items -> fact_orders, dim_products, dim_sellers
        self.assertEqual(len(set(df_items["order_id"]) - order_id_set), 0)
        self.assertEqual(len(set(df_items["product_id"]) - prod_id_set), 0)
        self.assertEqual(len(set(df_items["seller_id"]) - seller_id_set), 0)

        # fact_order_payments -> fact_orders
        self.assertEqual(len(set(df_payments["order_id"]) - order_id_set), 0)

        # fact_order_reviews -> fact_orders
        self.assertEqual(len(set(df_reviews["order_id"]) - order_id_set), 0)

    def test_08_date_dimension_continuity_and_coverage(self):
        """Verify date dimension spans 1,827 continuous days and covers 100% of fact dates."""
        df_date = self.dfs["dim_date.csv"]

        # Continuity check
        self.assertEqual(len(df_date), 1827)
        self.assertEqual(df_date["date"].min(), "2016-01-01")
        self.assertEqual(df_date["date"].max(), "2020-12-31")

        # Check daily continuity (0 missing dates)
        date_series = pd.to_datetime(df_date["date"])
        delta_days = (date_series.iloc[-1] - date_series.iloc[0]).days + 1
        self.assertEqual(delta_days, 1827)

        date_lookup_set = set(df_date["date"])

        # Check coverage across fact_orders dates
        df_orders = self.dfs["fact_orders.csv"]
        for date_col in [
            "order_purchase_date",
            "order_approved_date",
            "order_delivered_carrier_date_only",
            "order_delivered_customer_date_only",
            "order_estimated_delivery_date",
        ]:
            present_dates = set(df_orders[date_col].dropna())
            unmapped = present_dates - date_lookup_set
            self.assertEqual(
                len(unmapped),
                0,
                f"Dates in fact_orders[{date_col}] missing from dim_date: {unmapped}"
            )

        # Check coverage across fact_order_items
        df_items = self.dfs["fact_order_items.csv"]
        item_dates = set(df_items["shipping_limit_date_only"].dropna())
        unmapped_items = item_dates - date_lookup_set
        self.assertEqual(
            len(unmapped_items),
            0,
            f"Dates in fact_order_items[shipping_limit_date_only] missing from dim_date: {unmapped_items}"
        )

        # Check coverage across fact_order_reviews
        df_reviews = self.dfs["fact_order_reviews.csv"]
        for date_col in ["review_creation_date_only", "review_answer_date_only"]:
            review_dates = set(df_reviews[date_col].dropna())
            unmapped_rev = review_dates - date_lookup_set
            self.assertEqual(
                len(unmapped_rev),
                0,
                f"Dates in fact_order_reviews[{date_col}] missing from dim_date: {unmapped_rev}"
            )

    def test_09_product_pareto_enrichment(self):
        """Verify product dimension includes Pareto classifications and category ranking."""
        df_prod = self.dfs["dim_products.csv"]
        self.assertIn("pareto_class", df_prod.columns)
        self.assertIn("category_revenue_rank", df_prod.columns)

        # Classified products have valid pareto classes
        classified = df_prod["pareto_class"].dropna().unique()
        self.assertTrue(set(classified).issubset({"Core 80% (A)", "Long Tail (B/C)"}))


if __name__ == "__main__":
    unittest.main()
