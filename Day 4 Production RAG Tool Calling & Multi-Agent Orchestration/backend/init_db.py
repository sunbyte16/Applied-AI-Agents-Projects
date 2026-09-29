"""
Database initialization script for OrchestraRAG AI.
Creates and populates the SQLite application database with structured corporate records.
"""

import os
import sqlite3
from backend.config import settings

def init_app_database(db_path: str = settings.SQLITE_DB_PATH):
    """Initialize structured SQLite database tables with sample data."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Employees table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        salary REAL NOT NULL,
        leave_balance INTEGER NOT NULL,
        hire_date TEXT NOT NULL
    );
    """)

    # 2. Leave records table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_name TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        days_requested INTEGER NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 3. Company Metrics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS company_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric_name TEXT NOT NULL,
        quarter TEXT NOT NULL,
        value REAL NOT NULL,
        unit TEXT NOT NULL
    );
    """)

    # 4. Products table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    );
    """)

    # Check if empty before seeding
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        employees = [
            ("Alice Smith", "Engineering", "Principal AI Architect", 165000.0, 22, "2021-03-15"),
            ("Bob Jones", "Engineering", "Senior ML Engineer", 140000.0, 18, "2022-06-01"),
            ("Carlos Diaz", "Product", "Staff Product Manager", 150000.0, 20, "2020-01-10"),
            ("Diana Prince", "HR", "Director of People Ops", 135000.0, 25, "2019-11-20"),
            ("Evan Wright", "Security", "Lead Security Engineer", 145000.0, 16, "2023-02-01"),
            ("Fiona Gallagher", "Finance", "Senior Financial Analyst", 120000.0, 15, "2022-09-15"),
        ]
        cur.executemany(
            "INSERT INTO employees (name, department, role, salary, leave_balance, hire_date) VALUES (?, ?, ?, ?, ?, ?)",
            employees,
        )

        leaves = [
            ("Alice Smith", "Annual", 5, "Approved"),
            ("Bob Jones", "Sick", 2, "Approved"),
            ("Carlos Diaz", "Parental", 10, "Pending"),
            ("Diana Prince", "Annual", 3, "Approved"),
        ]
        cur.executemany(
            "INSERT INTO leave_requests (employee_name, leave_type, days_requested, status) VALUES (?, ?, ?, ?)",
            leaves,
        )

        metrics = [
            ("RAG Retrieval Latency P95", "Q3 2026", 185.0, "ms"),
            ("Multi-Agent Accuracy Score", "Q3 2026", 96.4, "%"),
            ("Hallucination Rate", "Q3 2026", 0.8, "%"),
            ("Total Corporate Leave Days Taken", "Q3 2026", 342.0, "days"),
        ]
        cur.executemany(
            "INSERT INTO company_metrics (metric_name, quarter, value, unit) VALUES (?, ?, ?, ?)",
            metrics,
        )

        products = [
            ("OrchestraRAG Enterprise License", "Software", 4999.0, 100),
            ("Vector Indexing Cloud Appliance", "Hardware", 12500.0, 15),
            ("LLM Guardrail Security Suite", "Security", 1899.0, 50),
        ]
        cur.executemany(
            "INSERT INTO products (product_name, category, price, stock) VALUES (?, ?, ?, ?)",
            products,
        )

    conn.commit()
    conn.close()
    print(f"Initialized application database at: {db_path}")

if __name__ == "__main__":
    init_app_database()
