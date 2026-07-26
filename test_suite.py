import unittest
import os
import pandas as pd
from db_manager import DatabaseManager
from chart_builder import auto_detect_chart_config
from sample_db_seed import create_and_seed_db, DB_PATH

class TestNL2SQLApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test sample database
        create_and_seed_db(DB_PATH)
        cls.db_mgr = DatabaseManager(db_type="sqlite", db_path=DB_PATH)

    def test_database_connection(self):
        ok, msg = self.db_mgr.test_connection()
        self.assertTrue(ok, f"Database connection failed: {msg}")

    def test_connection_failure_handling(self):
        bad_db = DatabaseManager(db_type="postgresql", pg_config={"host": "invalid_host_12345", "port": 5432, "dbname": "none", "user": "bad", "password": "bad"})
        ok, msg = bad_db.test_connection()
        self.assertFalse(ok)
        schema_summary = bad_db.get_schema_summary()
        self.assertIn("Unable to connect", schema_summary)

    def test_security_guardrails(self):
        # Safe queries
        safe_sql_1 = "SELECT * FROM products LIMIT 5;"
        safe_sql_2 = "WITH top_cust AS (SELECT customer_id, SUM(total_amount) as total FROM orders GROUP BY customer_id) SELECT * FROM top_cust ORDER BY total DESC LIMIT 3;"
        
        ok, msg = self.db_mgr.validate_sql_safety(safe_sql_1)
        self.assertTrue(ok, f"Safe query blocked: {msg}")
        
        ok, msg = self.db_mgr.validate_sql_safety(safe_sql_2)
        self.assertTrue(ok, f"Safe CTE query blocked: {msg}")

        # Dangerous queries
        dangerous_queries = [
            "DROP TABLE products;",
            "DELETE FROM orders WHERE order_id = 1;",
            "UPDATE sales_targets SET target_amount = 0;",
            "INSERT INTO categories VALUES (99, 'Hacked', 'Hacked');",
            "ALTER TABLE customers ADD COLUMN secret TEXT;",
            "SELECT * FROM products; DROP TABLE products;"
        ]

        for sql in dangerous_queries:
            ok, msg = self.db_mgr.validate_sql_safety(sql)
            self.assertFalse(ok, f"Dangerous SQL was allowed! Query: {sql}")

    def test_schema_summary(self):
        schema_summary = self.db_mgr.get_schema_summary()
        self.assertIn("categories", schema_summary)
        self.assertIn("products", schema_summary)
        self.assertIn("orders", schema_summary)
        self.assertIn("PRIMARY KEY", schema_summary)

    def test_query_execution(self):
        sql = "SELECT category_name, COUNT(*) as prod_count FROM products p JOIN categories c ON p.category_id = c.category_id GROUP BY category_name;"
        df, elapsed, error = self.db_mgr.execute_query(sql)
        
        self.assertIsNone(error, f"Execution failed with error: {error}")
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertIn("category_name", df.columns)
        self.assertIn("prod_count", df.columns)

    def test_chart_builder_auto_detect(self):
        df_time = pd.DataFrame({"month": ["2025-01", "2025-02"], "revenue": [1000, 2000]})
        config = auto_detect_chart_config(df_time)
        self.assertEqual(config["chart_type"], "line")

        df_cat = pd.DataFrame({"category": ["Laptops", "Software", "Security"], "revenue": [5000, 3000, 2000]})
        config_cat = auto_detect_chart_config(df_cat)
        self.assertIn(config_cat["chart_type"], ["bar", "donut", "pie"])

if __name__ == "__main__":
    unittest.main()
