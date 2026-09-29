"""
Safe AST-Based Calculator Tool for OrchestraRAG AI.
Evaluates mathematical expressions without using unrestricted eval().
Guarantees complete protection against arbitrary code execution.
"""

import ast
import math
import operator
from typing import Any, Dict
from backend.tools.base import BaseTool


class SafeCalculator(BaseTool):
    """Tool for performing deterministic arithmetic calculations safely."""

    name = "calculator"
    description = (
        "Perform exact mathematical and arithmetic calculations safely. "
        "Supports addition (+), subtraction (-), multiplication (*), division (/), "
        "modulo (%), exponentiation (**), and functions like abs, round, min, max, sqrt."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression string, e.g., '8492 * 372' or '((90 - 60) / 60) * 100'.",
            }
        },
        "required": ["expression"],
    }

    # Whitelisted operators
    _BINARY_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    _UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    _SAFE_FUNCS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "pow": pow,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    def _eval_node(self, node: ast.AST) -> float:
        """Recursively evaluate an AST node strictly against safe whitelist."""
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type not in self._BINARY_OPS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division or modulo by zero is not allowed.")

            # Guard against resource exhaustion via massive exponents
            if op_type == ast.Pow:
                if right > 100 or left > 10000:
                    raise ValueError("Exponent or base too large for safe evaluation.")

            result = self._BINARY_OPS[op_type](left, right)
            return float(result)

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self._UNARY_OPS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return float(self._UNARY_OPS[op_type](operand))

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only whitelisted top-level math functions are allowed.")
            func_name = node.func.id
            if func_name not in self._SAFE_FUNCS:
                raise ValueError(f"Function '{func_name}' is not in safe function whitelist.")

            args = [self._eval_node(arg) for arg in node.args]
            return float(self._SAFE_FUNCS[func_name](*args))

        else:
            raise ValueError(f"Unsafe or forbidden expression node: {type(node).__name__}")

    def execute(self, expression: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Safely parse and evaluate the mathematical expression."""
        if not expression or not isinstance(expression, str) or not expression.strip():
            return {
                "tool_name": self.name,
                "success": False,
                "error": "Expression must be a non-empty string.",
            }

        cleaned = expression.strip()
        # Clean common formatting like commas in numbers (e.g. 8,492 -> 8492)
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.replace("×", "*").replace("÷", "/")

        try:
            tree = ast.parse(cleaned, mode="eval")
            result = self._eval_node(tree)
            # Format nicely if integer
            formatted_result = int(result) if result.is_integer() else round(result, 6)
            return {
                "tool_name": self.name,
                "success": True,
                "expression": cleaned,
                "result": formatted_result,
            }
        except ZeroDivisionError as e:
            return {
                "tool_name": self.name,
                "success": False,
                "expression": cleaned,
                "error": f"Math error: {str(e)}",
            }
        except Exception as e:
            return {
                "tool_name": self.name,
                "success": False,
                "expression": cleaned,
                "error": f"Invalid expression: {str(e)}",
            }
