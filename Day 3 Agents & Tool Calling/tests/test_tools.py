"""
Unit Tests for AgentLab AI Tools.
Tests Calculator, Database, SkillGap, Weather, and Search tools for accuracy, safety, and validation.
"""

import os
import pytest
from backend.tools.calculator import CalculatorTool, evaluate_expression
from backend.tools.custom_tool import SkillGapTool
from backend.tools.database import DatabaseTool
from backend.tools.search import SearchTool
from backend.tools.weather import WeatherTool


class TestCalculatorTool:
    """Test suite for CalculatorTool safe AST evaluation."""

    def setup_method(self) -> None:
        self.tool = CalculatorTool()

    def test_basic_arithmetic(self) -> None:
        assert evaluate_expression("48392 * 274") == 13259408
        assert evaluate_expression("(1250 / 5) + 73") == 323
        assert evaluate_expression("100 - 45 + 12") == 67

    def test_percentage_calculation(self) -> None:
        assert evaluate_expression("15% of 84750") == 12712.5
        assert evaluate_expression("50% of 200") == 100

    def test_division_by_zero(self) -> None:
        res = self.tool.execute(expression="100 / 0")
        assert res["success"] is False
        assert "Division or modulo by zero" in res["error"]

    def test_malicious_code_blocked(self) -> None:
        # Should cleanly refuse function calls and imports
        res1 = self.tool.execute(expression="__import__('os').system('dir')")
        assert res1["success"] is False
        assert "Disallowed" in res1["error"] or "Invalid" in res1["error"]

        res2 = self.tool.execute(expression="open('/etc/passwd')")
        assert res2["success"] is False

    def test_empty_expression(self) -> None:
        res = self.tool.execute(expression="")
        assert res["success"] is False


class TestDatabaseTool:
    """Test suite for DatabaseTool read-only queries and security."""

    def setup_method(self) -> None:
        self.tool = DatabaseTool()

    def test_count_products(self) -> None:
        res = self.tool.execute(operation="count_products")
        assert res["success"] is True
        assert res["total_products"] >= 10

    def test_products_above_price(self) -> None:
        res = self.tool.execute(operation="products_above_price", price=1000)
        assert res["success"] is True
        assert res["count"] > 0
        for p in res["products"]:
            assert p["price"] > 1000

    def test_total_order_value(self) -> None:
        res = self.tool.execute(operation="total_order_value")
        assert res["success"] is True
        assert res["order_count"] > 0
        assert res["total_order_value"] > 0

    def test_safe_select_query(self) -> None:
        res = self.tool.execute(query="SELECT name, price FROM products LIMIT 3;")
        assert res["success"] is True
        assert res["row_count"] == 3
        assert "name" in res["columns"]

    def test_disallowed_destructive_sql(self) -> None:
        # Must block DROP, DELETE, UPDATE, INSERT
        drop_res = self.tool.execute(query="DROP TABLE products;")
        assert drop_res["success"] is False
        assert "Only read-only SELECT" in drop_res["error"]

        delete_res = self.tool.execute(query="DELETE FROM customers WHERE id = 1;")
        assert delete_res["success"] is False

        insert_res = self.tool.execute(query="INSERT INTO products (name) VALUES ('Hacked');")
        assert insert_res["success"] is False

        multi_res = self.tool.execute(query="SELECT * FROM products; DROP TABLE products;")
        assert multi_res["success"] is False


class TestSkillGapTool:
    """Test suite for SkillGapTool custom function."""

    def setup_method(self) -> None:
        self.tool = SkillGapTool()

    def test_ml_engineer_skill_analysis(self) -> None:
        res = self.tool.execute(
            target_role="Machine Learning Engineer",
            skills=["Python", "SQL", "TensorFlow"],
        )
        assert res["success"] is True
        assert "Python" in res["matched_core_skills"]
        assert "Docker" in res["missing_core_skills"]
        assert res["match_percentage"] > 0
        assert "readiness_level" in res

    def test_empty_arguments(self) -> None:
        res1 = self.tool.execute(target_role="", skills=["Python"])
        assert res1["success"] is False

        res2 = self.tool.execute(target_role="Data Scientist", skills=[])
        assert res2["success"] is False


class TestWeatherTool:
    """Test suite for WeatherTool argument validation."""

    def setup_method(self) -> None:
        self.tool = WeatherTool()

    def test_empty_location(self) -> None:
        res = self.tool.execute(location="")
        assert res["success"] is False
        assert "Location parameter is required" in res["error"]

    def test_valid_location_structure(self) -> None:
        res = self.tool.execute(location="Hyderabad")
        # Should return structured data if online
        if res["success"]:
            assert "temperature" in res
            assert "condition" in res
            assert res["unit"] == "Celsius"


class TestSearchTool:
    """Test suite for SearchTool argument validation."""

    def setup_method(self) -> None:
        self.tool = SearchTool()

    def test_empty_query(self) -> None:
        res = self.tool.execute(query="")
        assert res["success"] is False

    def test_valid_query_structure(self) -> None:
        res = self.tool.execute(query="artificial intelligence agents", max_results=2)
        if res["success"]:
            assert "results" in res
            assert len(res["results"]) > 0
            assert "title" in res["results"][0]
