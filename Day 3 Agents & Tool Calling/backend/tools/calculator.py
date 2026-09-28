"""
Safe Calculator Tool for AgentLab AI.
Evaluates mathematical expressions using Python's AST parser without unrestricted eval().
"""

import ast
import operator
import re
from typing import Any, Dict
from backend.tools.base import BaseTool

# Mapping of allowed binary operators to operator functions
ALLOWED_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Mapping of allowed unary operators
ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval_ast(node: ast.AST) -> float | int:
    """Recursively evaluates an AST node containing only safe arithmetic."""
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body)

    if isinstance(node, ast.Constant):  # Python 3.8+ numbers/constants
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp):
        left_val = _safe_eval_ast(node.left)
        right_val = _safe_eval_ast(node.right)
        op_type = type(node.op)

        if op_type not in ALLOWED_BINARY_OPS:
            raise ValueError(f"Operator '{op_type.__name__}' is not allowed.")

        # Guard against zero division
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right_val == 0:
            raise ZeroDivisionError("Division or modulo by zero is undefined.")

        # Guard against excessive exponentiation (DoS prevention)
        if op_type == ast.Pow:
            if abs(left_val) > 1000 or right_val > 100:
                raise ValueError("Exponentiation values exceed safety limits.")

        return ALLOWED_BINARY_OPS[op_type](left_val, right_val)

    if isinstance(node, ast.UnaryOp):
        operand_val = _safe_eval_ast(node.operand)
        op_type = type(node.op)

        if op_type not in ALLOWED_UNARY_OPS:
            raise ValueError(f"Unary operator '{op_type.__name__}' is not allowed.")

        return ALLOWED_UNARY_OPS[op_type](operand_val)

    raise ValueError(f"Disallowed expression element: {type(node).__name__}")


def evaluate_expression(expr: str) -> float | int:
    """Preprocesses arithmetic strings (including percentages) and safely evaluates them."""
    cleaned = expr.strip()

    # Preprocess percentage patterns: "X% of Y" -> "(X / 100) * Y"
    cleaned = re.sub(
        r'(\d+(?:\.\d+)?)\s*%\s*(?:of|\*)\s*(\d+(?:\.\d+)?)',
        r'((\1 / 100) * \2)',
        cleaned,
        flags=re.IGNORECASE
    )

    # Preprocess standalone percentage: "X%" -> "(X / 100)"
    cleaned = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1 / 100)', cleaned)

    # Replace common unicode math symbols
    cleaned = cleaned.replace('×', '*').replace('÷', '/').replace('^', '**')

    # Parse into AST
    tree = ast.parse(cleaned, mode='eval')
    result = _safe_eval_ast(tree)

    # Format cleanly (return int if whole number)
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return round(result, 6) if isinstance(result, float) else result


class CalculatorTool(BaseTool):
    """Tool for performing deterministic arithmetic calculations."""

    name = "calculator"
    description = (
        "Perform exact mathematical calculations and arithmetic operations (addition, "
        "subtraction, multiplication, division, powers, percentages, and complex expressions). "
        "Use this tool whenever calculation or arithmetic precision is required instead of guessing."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to calculate, e.g., '48392 * 274', '15% of 84750', '(1250 / 5) + 73'.",
            }
        },
        "required": ["expression"],
    }

    def execute(self, expression: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Execute calculator arithmetic."""
        if not expression or not isinstance(expression, str):
            return {
                "tool": self.name,
                "success": False,
                "error": "Expression parameter must be a non-empty string.",
            }

        try:
            result = evaluate_expression(expression)
            return {
                "tool": self.name,
                "success": True,
                "expression": expression,
                "result": result,
            }
        except ZeroDivisionError as e:
            return {
                "tool": self.name,
                "success": False,
                "expression": expression,
                "error": str(e),
            }
        except Exception as e:
            return {
                "tool": self.name,
                "success": False,
                "expression": expression,
                "error": f"Invalid mathematical expression: {str(e)}",
            }
