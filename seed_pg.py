import psycopg2
import random
from datetime import datetime, timedelta

def seed_postgres():
    conn = psycopg2.connect(dbname='analytics_db', user='postgres', password='mayank', host='localhost', port='5432')
    cursor = conn.cursor()
    
    # Drop tables if they exist
    tables_to_drop = ['order_items', 'orders', 'sales_targets', 'customers', 'sales_reps', 'products', 'regions', 'categories']
    for t in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
    
    # 1. Categories
    cursor.execute('''
    CREATE TABLE categories (
        category_id SERIAL PRIMARY KEY,
        category_name TEXT NOT NULL,
        department TEXT NOT NULL
    );
    ''')
    categories_data = [
        ('Enterprise Laptops', 'Hardware'),
        ('Cloud Accessories', 'Hardware'),
        ('SaaS Licenses', 'Software'),
        ('Developer Tools', 'Software'),
        ('Security Hardware', 'Security'),
        ('Workstation Displays', 'Hardware')
    ]
    cursor.executemany("INSERT INTO categories (category_name, department) VALUES (%s, %s);", categories_data)

    # 2. Products
    cursor.execute('''
    CREATE TABLE products (
        product_id SERIAL PRIMARY KEY,
        product_name TEXT NOT NULL,
        category_id INTEGER REFERENCES categories (category_id),
        unit_price REAL NOT NULL,
        cost_price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL
    );
    ''')
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
    cursor.executemany("INSERT INTO products (product_name, category_id, unit_price, cost_price, stock_quantity) VALUES (%s, %s, %s, %s, %s);", products_data)

    # 3. Regions
    cursor.execute('''
    CREATE TABLE regions (
        region_id SERIAL PRIMARY KEY,
        region_name TEXT NOT NULL,
        country TEXT NOT NULL
    );
    ''')
    regions_data = [
        ('North America East', 'USA'),
        ('North America West', 'USA'),
        ('EMEA Central', 'Germany'),
        ('APAC East', 'Japan'),
        ('LATAM South', 'Brazil')
    ]
    cursor.executemany("INSERT INTO regions (region_name, country) VALUES (%s, %s);", regions_data)

    # 4. Sales Reps
    cursor.execute('''
    CREATE TABLE sales_reps (
        rep_id SERIAL PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        region_id INTEGER REFERENCES regions (region_id),
        hire_date DATE
    );
    ''')
    reps_data = [
        ('Sarah', 'Jenkins', 's.jenkins@company.com', 1, '2022-03-15'),
        ('Michael', 'Chang', 'm.chang@company.com', 2, '2021-08-01'),
        ('Elena', 'Rostova', 'e.rostova@company.com', 3, '2023-01-10'),
        ('Kenji', 'Takahashi', 'k.takahashi@company.com', 4, '2022-11-20'),
        ('Carlos', 'Silva', 'c.silva@company.com', 5, '2023-05-12')
    ]
    cursor.executemany("INSERT INTO sales_reps (first_name, last_name, email, region_id, hire_date) VALUES (%s, %s, %s, %s, %s);", reps_data)

    # 5. Customers
    cursor.execute('''
    CREATE TABLE customers (
        customer_id SERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        contact_name TEXT NOT NULL,
        contact_email TEXT NOT NULL,
        segment TEXT NOT NULL,
        region_id INTEGER REFERENCES regions (region_id)
    );
    ''')
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
    cursor.executemany("INSERT INTO customers (company_name, contact_name, contact_email, segment, region_id) VALUES (%s, %s, %s, %s, %s);", customers_data)

    # 6. Sales Targets
    cursor.execute('''
    CREATE TABLE sales_targets (
        target_id SERIAL PRIMARY KEY,
        rep_id INTEGER REFERENCES sales_reps (rep_id),
        quarter TEXT NOT NULL,
        year INTEGER NOT NULL,
        target_amount REAL NOT NULL
    );
    ''')
    targets_data = []
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    years = [2024, 2025, 2026]
    for year in years:
        for q in quarters:
            for rep_id in range(1, 6):
                target_amount = random.randint(120, 250) * 1000.0
                targets_data.append((rep_id, q, year, target_amount))
    cursor.executemany("INSERT INTO sales_targets (rep_id, quarter, year, target_amount) VALUES (%s, %s, %s, %s);", targets_data)

    # 7. Orders
    cursor.execute('''
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER REFERENCES customers (customer_id),
        rep_id INTEGER REFERENCES sales_reps (rep_id),
        order_date DATE NOT NULL,
        status TEXT NOT NULL,
        discount_percent REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0
    );
    ''')

    # 8. Order Items
    cursor.execute('''
    CREATE TABLE order_items (
        item_id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders (order_id),
        product_id INTEGER REFERENCES products (product_id),
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        line_total REAL NOT NULL
    );
    ''')

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 6, 30)
    total_days = (end_date - start_date).days
    random.seed(42)

    orders_data = []
    order_items_data = []
    order_id = 1
    for _ in range(350):
        rand_days = random.randint(0, total_days)
        o_date = start_date + timedelta(days=rand_days)
        date_str = o_date.strftime("%Y-%m-%d")
        
        customer_id = random.randint(1, len(customers_data))
        rep_id = random.randint(1, len(reps_data))
        status = random.choice(['Completed', 'Completed', 'Completed', 'Completed', 'Processing', 'Shipped'])
        discount_percent = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])

        num_items = random.randint(1, 4)
        selected_products = random.sample(range(1, len(products_data) + 1), num_items)
        
        subtotal = 0.0
        for pid in selected_products:
            prod_info = products_data[pid - 1]
            unit_price = prod_info[2]
            quantity = random.randint(1, 15) if prod_info[2] < 500 else random.randint(1, 5)
            line_total = round(unit_price * quantity, 2)
            subtotal += line_total
            order_items_data.append((order_id, pid, quantity, unit_price, line_total))

        total_amount = round(subtotal * (1 - discount_percent), 2)
        orders_data.append((order_id, customer_id, rep_id, date_str, status, discount_percent, total_amount))
        order_id += 1

    cursor.executemany("INSERT INTO orders (order_id, customer_id, rep_id, order_date, status, discount_percent, total_amount) VALUES (%s, %s, %s, %s, %s, %s, %s);", orders_data)
    cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total) VALUES (%s, %s, %s, %s, %s);", order_items_data)

    conn.commit()
    cursor.close()
    conn.close()
    print("PostgreSQL seeded successfully!")

if __name__ == "__main__":
    seed_postgres()
