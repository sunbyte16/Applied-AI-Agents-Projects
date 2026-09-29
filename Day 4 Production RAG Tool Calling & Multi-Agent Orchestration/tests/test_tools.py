"""
Unit tests for OrchestraRAG AI tools suite.
Verifies safety, deterministic execution, and error handling.
"""

import pytest
from backend.tools.calculator import SafeCalculator
from backend.tools.database import DatabaseTool
from backend.tools.weather import WeatherTool
from backend.tools.search import SearchTool
from backend.tools.custom_tool import CustomAnalyticsTool
from backend.tools.registry import ToolRegistry


class TestTools:
    """Test suite for tools layer."""

    def test_calculator_basic_arithmetic(self):
        calc = SafeCalculator()
        res = calc.execute("8492 * 372")
        assert res["success"] is True
        assert res["result"] == 3159024

    def test_calculator_complex_expression(self):
        calc = SafeCalculator()
        res = calc.execute("((90 - 60) / 60) * 100")
        assert res["success"] is True
        assert res["result"] == 50.0

    def test_calculator_zero_division(self):
        calc = SafeCalculator()
        res = calc.execute("100 / 0")
        assert res["success"] is False
        assert "Division or modulo by zero" in res["error"]

    def test_calculator_blocks_eval_injection(self):
        calc = SafeCalculator()
        # Attempt code execution
        res = calc.execute("__import__('os').system('echo hacked')")
        assert res["success"] is False
        assert "Invalid expression" in res["error"] or "safe function" in res["error"]

    def test_database_read_only_select(self):
        db = DatabaseTool()
        res = db.execute("SELECT name, department, role FROM employees WHERE department = 'Engineering';")
        assert res["success"] is True
        assert res["row_count"] >= 1
        assert "name" in res["columns"]

    def test_database_blocks_destructive_dml(self):
        db = DatabaseTool()
        res = db.execute("DROP TABLE employees;")
        assert res["success"] is False
        assert "Only SELECT or WITH queries are permitted" in res["error"]

    def test_database_blocks_multi_statement(self):
        db = DatabaseTool()
        res = db.execute("SELECT * FROM employees; DELETE FROM employees;")
        assert res["success"] is False
        assert "Multi-statement SQL queries are strictly prohibited" in res["error"]

    def test_weather_location_validation(self):
        w = WeatherTool()
        # Invalid location with symbols
        res = w.execute("San Francisco <script>alert(1)</script>")
        assert res["success"] is False
        assert "invalid characters" in res["error"].lower()

    def test_custom_analytics_percentage_improvement(self):
        analytics = CustomAnalyticsTool()
        res = analytics.execute(
            operation="percentage_improvement",
            baseline_value=60.0,
            new_value=90.0,
        )
        assert res["success"] is True
        assert res["percentage_change"] == 50.0
        assert res["percentage_improvement_formatted"] == "+50.00%"

    def test_custom_analytics_summary_statistics(self):
        analytics = CustomAnalyticsTool()
        res = analytics.execute(
            operation="summary_statistics",
            values=[10.0, 20.0, 30.0, 40.0, 50.0],
        )
        assert res["success"] is True
        assert res["count"] == 5
        assert res["mean"] == 30.0
        assert res["min"] == 10.0
        assert res["max"] == 50.0

    def test_tool_registry_discovery(self):
        reg = ToolRegistry()
        schemas = reg.get_tool_schemas()
        assert len(schemas) >= 4
        names = [s["function"]["name"] for s in schemas]
        assert "calculator" in names
        assert "database" in names
        assert "weather" in names
        assert "analytics" in names
