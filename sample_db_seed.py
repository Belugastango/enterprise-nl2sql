import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_company.db")

def create_and_seed_db(db_path=DB_PATH):
    """Creates a comprehensive sample SQLite database representing an enterprise retail/e-commerce business."""
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Categories Table
    cursor.execute("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL,
        department TEXT NOT NULL
    );
    """)

    categories_data = [
        ('Enterprise Laptops', 'Hardware'),
        ('Cloud Accessories', 'Hardware'),
        ('SaaS Licenses', 'Software'),
        ('Developer Tools', 'Software'),
        ('Security Hardware', 'Security'),
        ('Workstation Displays', 'Hardware')
    ]
    cursor.executemany("INSERT INTO categories (category_name, department) VALUES (?, ?);", categories_data)

    # 2. Products Table
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category_id INTEGER,
        unit_price REAL NOT NULL,
        cost_price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    );
    """)

    products_data = [
        ('ProBook X1 Carbon', 1, 1499.99, 950.00, 140),
        ('UltraBook Pro 15', 1, 1899.99, 1200.00, 85),
        ('ErgoDock Thunderbolt 4', 2, 249.99, 110.00, 320),
        ('4K Curved Monitor 32"', 6, 699.99, 420.00, 95),
        ('Cloud Analytics Enterprise (1-Yr)', 3, 2999.00, 300.00, 500),
        ('AI Copilot Team Subscription', 4, 499.00, 50.00, 1200),
        ('Hardware Security Key Pro', 5, 59.99, 18.00, 850),
        ('Noise-Canceling Executive Headset', 2, 199.99, 75.00, 210),
        ('Developer Workstation Tower', 1, 3299.99, 2100.00, 45),
        ('Zero-Trust Gateway License', 3, 1499.00, 200.00, 400)
    ]
    cursor.executemany("""
    INSERT INTO products (product_name, category_id, unit_price, cost_price, stock_quantity)
    VALUES (?, ?, ?, ?, ?);
    """, products_data)

    # 3. Regions Table
    cursor.execute("""
    CREATE TABLE regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL,
        country TEXT NOT NULL
    );
    """)
    regions_data = [
        ('North America East', 'USA'),
        ('North America West', 'USA'),
        ('EMEA Central', 'Germany'),
        ('APAC East', 'Japan'),
        ('LATAM South', 'Brazil')
    ]
    cursor.executemany("INSERT INTO regions (region_name, country) VALUES (?, ?);", regions_data)

    # 4. Sales Reps Table
    cursor.execute("""
    CREATE TABLE sales_reps (
        rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        region_id INTEGER,
        hire_date DATE,
        FOREIGN KEY (region_id) REFERENCES regions (region_id)
    );
    """)
    reps_data = [
        ('Sarah', 'Jenkins', 's.jenkins@company.com', 1, '2022-03-15'),
        ('Michael', 'Chang', 'm.chang@company.com', 2, '2021-08-01'),
        ('Elena', 'Rostova', 'e.rostova@company.com', 3, '2023-01-10'),
        ('Kenji', 'Takahashi', 'k.takahashi@company.com', 4, '2022-11-20'),
        ('Carlos', 'Silva', 'c.silva@company.com', 5, '2023-05-12')
    ]
    cursor.executemany("""
    INSERT INTO sales_reps (first_name, last_name, email, region_id, hire_date)
    VALUES (?, ?, ?, ?, ?);
    """, reps_data)

    # 5. Customers Table
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        contact_name TEXT NOT NULL,
        contact_email TEXT NOT NULL,
        segment TEXT NOT NULL,
        region_id INTEGER,
        FOREIGN KEY (region_id) REFERENCES regions (region_id)
    );
    """)
    customers_data = [
        ('Acme Corp', 'Alice Vance', 'alice@acme.com', 'Enterprise', 1),
        ('TechStart Solutions', 'Bob Smith', 'bob@techstart.io', 'SMB', 2),
        ('Global Logistics AG', 'Hans Mueller', 'h.mueller@globallog.de', 'Enterprise', 3),
        ('Tokyo FinTech Inc', 'Yuki Sato', 'y.sato@tokyofintech.jp', 'Enterprise', 4),
        ('Apex Healthcare', 'David Ross', 'd.ross@apexhealth.org', 'Mid-Market', 1),
        ('BioGen Labs', 'Emma Watson', 'e.watson@biogenlabs.com', 'Mid-Market', 2),
        ('Quantum Dynamics', 'Siddharth Patel', 'spatel@quantumdyn.in', 'Enterprise', 4),
        ('Rio Retail Digital', 'Lucia Fernandez', 'lucia@rioretail.br', 'SMB', 5)
    ]
    cursor.executemany("""
    INSERT INTO customers (company_name, contact_name, contact_email, segment, region_id)
    VALUES (?, ?, ?, ?, ?);
    """, customers_data)

    # 6. Sales Targets Table
    cursor.execute("""
    CREATE TABLE sales_targets (
        target_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rep_id INTEGER,
        quarter TEXT NOT NULL,
        year INTEGER NOT NULL,
        target_amount REAL NOT NULL,
        FOREIGN KEY (rep_id) REFERENCES sales_reps (rep_id)
    );
    """)
    targets_data = []
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    years = [2024, 2025, 2026]
    for year in years:
        for q in quarters:
            for rep_id in range(1, 6):
                target_amount = random.randint(120, 250) * 1000.0
                targets_data.append((rep_id, q, year, target_amount))
    cursor.executemany("""
    INSERT INTO sales_targets (rep_id, quarter, year, target_amount)
    VALUES (?, ?, ?, ?);
    """, targets_data)

    # 7. Orders Table
    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        rep_id INTEGER,
        order_date DATE NOT NULL,
        status TEXT NOT NULL,
        discount_percent REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (rep_id) REFERENCES sales_reps (rep_id)
    );
    """)

    # 8. Order Items Table
    cursor.execute("""
    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    );
    """)

    # Generate realistic orders over 2024 - 2026
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 6, 30)
    total_days = (end_date - start_date).days

    random.seed(42) # Consistent realistic data generation

    order_id = 1
    for _ in range(350): # 350 transactions
        rand_days = random.randint(0, total_days)
        o_date = start_date + timedelta(days=rand_days)
        date_str = o_date.strftime("%Y-%m-%d")
        
        customer_id = random.randint(1, len(customers_data))
        # rep associated with customer region or random
        rep_id = random.randint(1, len(reps_data))
        status = random.choice(['Completed', 'Completed', 'Completed', 'Completed', 'Processing', 'Shipped'])
        discount_percent = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])

        # Pick 1 to 4 items per order
        num_items = random.randint(1, 4)
        selected_products = random.sample(range(1, len(products_data) + 1), num_items)
        
        order_items_rows = []
        subtotal = 0.0

        for pid in selected_products:
            prod_info = products_data[pid - 1]
            unit_price = prod_info[2]
            quantity = random.randint(1, 15) if prod_info[2] < 500 else random.randint(1, 5)
            line_total = round(unit_price * quantity, 2)
            subtotal += line_total
            order_items_rows.append((order_id, pid, quantity, unit_price, line_total))

        total_amount = round(subtotal * (1 - discount_percent), 2)

        cursor.execute("""
        INSERT INTO orders (order_id, customer_id, rep_id, order_date, status, discount_percent, total_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (order_id, customer_id, rep_id, date_str, status, discount_percent, total_amount))

        cursor.executemany("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
        VALUES (?, ?, ?, ?, ?);
        """, order_items_rows)

        order_id += 1

    conn.commit()
    conn.close()
    print(f"Sample database created successfully at: {db_path}")

if __name__ == "__main__":
    create_and_seed_db()
