"""
Database Seeding Script for AgentLab AI
Creates SQLite database with realistic tables: products, customers, orders.
"""

import os
import sqlite3

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "sample.db")


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize and seed the SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Products Table
    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        rating REAL NOT NULL,
        description TEXT
    );
    """)

    # 2. Customers Table
    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        city TEXT NOT NULL,
        country TEXT NOT NULL,
        join_date TEXT NOT NULL
    );
    """)

    # 3. Orders Table
    cursor.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
    """)

    # Seed Products
    products = [
        ("MacBook Pro M3 Max", "Electronics", 1999.99, 25, 4.9, "Apple 16-inch high-performance laptop"),
        ("Dell XPS 15 OLED", "Electronics", 1399.00, 30, 4.7, "Premium ultrabook with 4K OLED display"),
        ("Sony WH-1000XM5", "Audio", 349.99, 85, 4.8, "Industry leading noise-canceling headphones"),
        ("Samsung Galaxy S24 Ultra", "Electronics", 1199.99, 45, 4.8, "Flagship AI-powered Android smartphone"),
        ("Apple iPad Air 11-inch", "Tablets", 599.00, 60, 4.6, "M2 chip portable tablet for creatives"),
        ("Keychron Q1 Pro Keyboard", "Accessories", 199.99, 120, 4.7, "Wireless custom mechanical keyboard"),
        ("Logitech MX Master 3S", "Accessories", 99.99, 150, 4.9, "Ergonomic performance wireless mouse"),
        ("LG UltraFine 32-inch 4K", "Displays", 1099.00, 18, 4.5, "Professional color-accurate designer monitor"),
        ("Anker 737 Power Bank", "Accessories", 109.99, 90, 4.7, "24,000mAh 140W fast charger"),
        ("Sony A7 IV Mirrorless", "Photography", 2498.00, 12, 4.9, "Full-frame 33MP hybrid photo/video camera"),
        ("Bose QuietComfort Ultra", "Audio", 429.00, 40, 4.6, "Immersive spatial audio noise-canceling headphones"),
        ("Kindle Paperwhite", "Tablets", 149.99, 110, 4.8, "Waterproof e-reader with warm light"),
        ("Asus ROG Zephyrus G16", "Electronics", 1799.00, 15, 4.6, "Ultra-thin high-power gaming laptop"),
        ("DJI Mini 4 Pro Drone", "Photography", 759.00, 22, 4.8, "Sub-249g lightweight 4K HDR camera drone"),
        ("Herman Miller Aeron Chair", "Furniture", 1250.00, 8, 4.9, "Ergonomic executive mesh office chair"),
    ]

    cursor.executemany("""
    INSERT INTO products (name, category, price, stock, rating, description)
    VALUES (?, ?, ?, ?, ?, ?);
    """, products)

    # Seed Customers
    customers = [
        ("Aarav Sharma", "aarav.sharma@example.com", "Hyderabad", "India", "2024-01-15"),
        ("Elena Rostova", "elena.rostova@example.com", "London", "UK", "2024-02-10"),
        ("David Miller", "david.miller@example.com", "New York", "USA", "2024-02-28"),
        ("Priya Patel", "priya.patel@example.com", "Mumbai", "India", "2024-03-05"),
        ("Kenji Sato", "kenji.sato@example.com", "Tokyo", "Japan", "2024-03-12"),
        ("Sarah Jenkins", "sarah.j@example.com", "London", "UK", "2024-04-01"),
        ("Rahul Verma", "rahul.v@example.com", "Delhi", "India", "2024-04-18"),
        ("Sophia Müller", "sophia.m@example.com", "Berlin", "Germany", "2024-05-02"),
        ("Lucas Silva", "lucas.silva@example.com", "São Paulo", "Brazil", "2024-05-20"),
        ("Amina Al-Mansoor", "amina.m@example.com", "Dubai", "UAE", "2024-06-11"),
    ]

    cursor.executemany("""
    INSERT INTO customers (name, email, city, country, join_date)
    VALUES (?, ?, ?, ?, ?);
    """, customers)

    # Seed Orders
    orders = [
        (1, 1, 1, 1999.99, "2024-06-15", "Delivered"),
        (2, 3, 2, 699.98, "2024-06-18", "Delivered"),
        (3, 4, 1, 1199.99, "2024-06-22", "Shipped"),
        (4, 7, 1, 99.99, "2024-06-25", "Delivered"),
        (5, 10, 1, 2498.00, "2024-07-01", "Delivered"),
        (6, 2, 1, 1399.00, "2024-07-04", "Delivered"),
        (7, 6, 2, 399.98, "2024-07-10", "Processing"),
        (8, 8, 1, 1099.00, "2024-07-12", "Delivered"),
        (9, 9, 1, 759.00, "2024-07-15", "Delivered"),
        (10, 15, 1, 1250.00, "2024-07-18", "Shipped"),
        (1, 7, 2, 199.98, "2024-07-20", "Delivered"),
        (4, 14, 1, 759.00, "2024-07-22", "Delivered"),
    ]

    cursor.executemany("""
    INSERT INTO orders (customer_id, product_id, quantity, total_price, order_date, status)
    VALUES (?, ?, ?, ?, ?, ?);
    """, orders)

    conn.commit()
    conn.close()
    print(f"Database successfully initialized and seeded at: {db_path}")


if __name__ == "__main__":
    init_db()
