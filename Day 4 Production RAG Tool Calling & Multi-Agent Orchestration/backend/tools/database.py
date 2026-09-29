"""
Read-Only Database Tool for OrchestraRAG AI.
Queries structured application SQLite data safely.
Rejects destructive DDL/DML, multi-statement injection, and unvetted SQL operations.
"""

import os
import re
import sqlite3
import time
from typing import Any, Dict, List
from backend.config import settings
from backend.tools.base import BaseTool


class DatabaseTool(BaseTool):
    """Tool for querying structured enterprise data stored in the application database."""

    name = "database"
    description = (
        "Execute read-only SQL queries against the corporate database to retrieve structured information. "
        "Available tables: "
        "'employees' (id, name, department, role, salary, leave_balance, hire_date), "
        "'leave_requests' (id, employee_name, leave_type, days_requested, status), "
        "'company_metrics' (id, metric_name, quarter, value, unit), "
        "'products' (id, product_name, category, price, stock). "
        "Only SELECT queries are permitted."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL SELECT query to execute, e.g. 'SELECT name, role, leave_balance FROM employees WHERE department = \"Engineering\"'.",
            }
        },
        "required": ["query"],
    }

    # Forbidden DDL/DML tokens
    _FORBIDDEN_KEYWORDS = {
        "insert", "update", "delete", "drop", "alter", "create", "truncate",
        "replace", "attach", "detach", "pragma", "reindex", "vacuum", "grant", "revoke"
    }

    def __init__(self, db_path: str = settings.SQLITE_DB_PATH):
        self.db_path = db_path

    def _validate_sql(self, sql: str) -> None:
        """Strictly validate SQL query for read-only safety."""
        clean = sql.strip().rstrip(";")
        if ";" in clean:
            raise ValueError("Multi-statement SQL queries are strictly prohibited.")

        # Match first word
        match = re.match(r"^\s*([a-zA-Z]+)", clean, re.IGNORECASE)
        if not match:
            raise ValueError("Empty or malformed SQL statement.")

        first_word = match.group(1).lower()
        if first_word not in ("select", "with", "explain"):
            raise ValueError(f"Only SELECT or WITH queries are permitted. Got: '{first_word.upper()}'.")

        # Scan for dangerous mutation keywords in words
        words = re.findall(r"\b([a-zA-Z_]+)\b", clean.lower())
        for w in words:
            if w in self._FORBIDDEN_KEYWORDS:
                # Disallow forbidden keywords unless strictly part of SELECT context (e.g. column names)
                # But safer to reject outright to prevent side-channel updates
                raise ValueError(f"Disallowed SQL keyword detected: '{w.upper()}'. Modifications are forbidden.")

    def execute(self, query: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Execute validated read-only SQL query against SQLite."""
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "tool_name": self.name,
                "success": False,
                "error": "Query parameter must be a non-empty string.",
            }

        cleaned_sql = query.strip()
        try:
            self._validate_sql(cleaned_sql)
        except ValueError as ve:
            return {
                "tool_name": self.name,
                "success": False,
                "query": cleaned_sql,
                "error": str(ve),
            }

        if not os.path.exists(self.db_path):
            return {
                "tool_name": self.name,
                "success": False,
                "query": cleaned_sql,
                "error": "Application database file does not exist.",
            }

        try:
            # Connect in read-only URI mode if supported
            conn = sqlite3.connect(f"file:{os.path.abspath(self.db_path)}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            start_time = time.perf_counter()
            cursor.execute(cleaned_sql)
            rows = cursor.fetchmany(50)  # Safe bounded fetch limit
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            data_rows = [dict(row) for row in rows]
            conn.close()

            return {
                "tool_name": self.name,
                "success": True,
                "query": cleaned_sql,
                "columns": columns,
                "row_count": len(data_rows),
                "data": data_rows,
                "query_time_ms": duration_ms,
            }
        except sqlite3.Error as e:
            return {
                "tool_name": self.name,
                "success": False,
                "query": cleaned_sql,
                "error": f"SQLite execution error: {str(e)}",
            }
        except Exception as e:
            return {
                "tool_name": self.name,
                "success": False,
                "query": cleaned_sql,
                "error": f"Database query error: {str(e)}",
            }
