"""
Safe Read-Only Database Tool for AgentLab AI.
Queries local SQLite database (products, customers, orders) using structured operations
or strictly validated, read-only SELECT queries.
"""

import os
import re
import sqlite3
from typing import Any, Dict, List, Optional
from backend.tools.base import BaseTool

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "sample.db")

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "REPLACE", "TRUNCATE", "ATTACH", "DETACH", "REINDEX", "VACUUM", "EXEC"
}


class DatabaseTool(BaseTool):
    """Tool for querying the application's local SQLite database safely."""

    name = "database"
    description = (
        "Query the internal SQLite database containing application data tables: "
        "'products' (id, name, category, price, stock, rating, description), "
        "'customers' (id, name, email, city, country, join_date), and "
        "'orders' (id, customer_id, product_id, quantity, total_price, order_date, status). "
        "Supports structured operations or read-only SELECT queries. "
        "Destructive commands (DROP, DELETE, UPDATE, INSERT) are strictly forbidden."
    )
    parameters = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "count_products",
                    "products_above_price",
                    "total_order_value",
                    "list_tables",
                    "describe_table",
                    "top_rated_products",
                    "custom_query",
                ],
                "description": "Predefined safe structured query operation, or 'custom_query' for read-only SELECT.",
            },
            "price": {
                "type": "number",
                "description": "Price threshold for 'products_above_price' (e.g. 1000).",
            },
            "table_name": {
                "type": "string",
                "description": "Table name for 'describe_table' (e.g. 'products', 'customers', 'orders').",
            },
            "query": {
                "type": "string",
                "description": "Safe read-only SELECT SQL query when operation is 'custom_query' or when querying directly.",
            },
        },
    }

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _get_read_only_connection(self) -> sqlite3.Connection:
        """Opens a read-only SQLite URI connection to physically prevent any writes."""
        abs_path = os.path.abspath(self.db_path)
        # SQLite URI read-only connection
        uri = f"file:{abs_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _validate_sql(self, sql: str) -> Optional[str]:
        """Validates that SQL is strictly a single, read-only SELECT query."""
        cleaned = sql.strip().rstrip(";")
        # Check for multiple statements
        if ";" in cleaned:
            return "Multiple SQL statements are not permitted."

        tokens = re.findall(r"\b[A-Za-z_]+\b", cleaned)
        upper_tokens = [t.upper() for t in tokens]

        # First token must be SELECT or WITH or PRAGMA
        if not upper_tokens or upper_tokens[0] not in ("SELECT", "WITH", "PRAGMA"):
            return "Only read-only SELECT or PRAGMA queries are allowed."

        # Check for any forbidden destructive keywords
        for forbidden in FORBIDDEN_KEYWORDS:
            if forbidden in upper_tokens:
                return f"Disallowed destructive SQL operation: '{forbidden}'."

        return None

    def execute(
        self,
        operation: Optional[str] = None,
        query: Optional[str] = None,
        price: Optional[float] = None,
        table_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute safe database operation."""
        if not os.path.exists(self.db_path):
            return {
                "tool": self.name,
                "success": False,
                "error": f"Database file not found at {self.db_path}. Please initialize it.",
            }

        try:
            conn = self._get_read_only_connection()
            cursor = conn.cursor()

            # Handle structured operations
            if operation == "count_products":
                cursor.execute("SELECT COUNT(*) AS total_products FROM products;")
                row = cursor.fetchone()
                return {
                    "tool": self.name,
                    "success": True,
                    "operation": "count_products",
                    "total_products": row["total_products"] if row else 0,
                }

            elif operation == "products_above_price":
                threshold = float(price if price is not None else 1000)
                cursor.execute(
                    "SELECT id, name, category, price, stock, rating FROM products WHERE price > ? ORDER BY price DESC;",
                    (threshold,),
                )
                rows = [dict(r) for r in cursor.fetchall()]
                return {
                    "tool": self.name,
                    "success": True,
                    "operation": "products_above_price",
                    "price_threshold": threshold,
                    "count": len(rows),
                    "products": rows,
                }

            elif operation == "total_order_value":
                cursor.execute("SELECT COUNT(*) as order_count, ROUND(SUM(total_price), 2) AS total_value FROM orders;")
                row = cursor.fetchone()
                return {
                    "tool": self.name,
                    "success": True,
                    "operation": "total_order_value",
                    "order_count": row["order_count"] if row else 0,
                    "total_order_value": row["total_value"] if row else 0.0,
                }

            elif operation == "list_tables":
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [r["name"] for r in cursor.fetchall()]
                return {
                    "tool": self.name,
                    "success": True,
                    "tables": tables,
                }

            elif operation == "describe_table" and table_name:
                clean_name = re.sub(r"[^a-zA-Z0-9_]", "", table_name)
                cursor.execute(f"PRAGMA table_info({clean_name});")
                cols = [{"cid": r["cid"], "name": r["name"], "type": r["type"]} for r in cursor.fetchall()]
                return {
                    "tool": self.name,
                    "success": True,
                    "table": clean_name,
                    "columns": cols,
                }

            elif operation == "top_rated_products":
                cursor.execute(
                    "SELECT name, category, price, rating FROM products ORDER BY rating DESC, price DESC LIMIT 5;"
                )
                rows = [dict(r) for r in cursor.fetchall()]
                return {
                    "tool": self.name,
                    "success": True,
                    "top_rated_products": rows,
                }

            # Handle custom query or implicit SQL query string
            sql_to_run = query
            if not sql_to_run and operation and operation.strip().upper().startswith("SELECT"):
                sql_to_run = operation

            if sql_to_run:
                validation_error = self._validate_sql(sql_to_run)
                if validation_error:
                    return {
                        "tool": self.name,
                        "success": False,
                        "query": sql_to_run,
                        "error": validation_error,
                    }

                cursor.execute(sql_to_run)
                columns = [col[0] for col in cursor.description] if cursor.description else []
                raw_rows = cursor.fetchall()
                # Limit to 50 rows for safety
                rows_data = [dict(zip(columns, row)) for row in raw_rows[:50]]

                return {
                    "tool": self.name,
                    "success": True,
                    "query": sql_to_run,
                    "row_count": len(rows_data),
                    "columns": columns,
                    "rows": rows_data,
                }

            return {
                "tool": self.name,
                "success": False,
                "error": "No valid operation or read-only SELECT query was provided.",
            }

        except sqlite3.OperationalError as e:
            return {
                "tool": self.name,
                "success": False,
                "error": f"Database operational error: {str(e)}",
            }
        except Exception as e:
            return {
                "tool": self.name,
                "success": False,
                "error": f"Database error: {str(e)}",
            }
        finally:
            if "conn" in locals() and conn:
                conn.close()
