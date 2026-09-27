import ast
import re
from decimal import Decimal, localcontext
from typing import Any

from areal.utils import logging

from .base import BaseTool, ToolCallStatus, ToolDescription, ToolMarkers, ToolType

logger = logging.getLogger("Calculator Tool")


class CalculatorTool(BaseTool):
    """Basic calculator tool"""

    @property
    def tool_type(self) -> ToolType:
        return ToolType.CALCULATOR

    @property
    def description(self) -> ToolDescription:
        return ToolDescription(
            name="python calculator",
            description="Perform basic mathematical calculations, supporting addition, subtraction, multiplication, division, and parentheses.",
            parameters={"expression": "Mathematical expression string"},
            parameter_prompt="Please provide a mathematical expression. Supports addition, subtraction, multiplication, division, and parentheses.",
            example="<calculator>1 + 2 * 3</calculator>",
        )

    @property
    def markers(self) -> ToolMarkers:
        return ToolMarkers(
            start_markers=["<calculator>"], end_markers=["</calculator>"]
        )

    def parse_parameters(self, text: str) -> dict[str, Any]:
        """Extract mathematical expression from <calculator> tags"""
        pattern = r"<calculator>(.*?)</calculator>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            expression = match.group(1).strip()
            logger.debug(f"Extracted expression: {expression}")
            return {"expression": expression}
        else:
            logger.warning("No <calculator> tag found")
            return {"expression": ""}

    def execute(self, parameters: dict[str, Any]) -> tuple[str, ToolCallStatus]:
        """Execute mathematical calculation"""
        expression = parameters.get("expression", "")
        if not expression:
            return "Error: No expression provided", ToolCallStatus.ERROR

        if self.debug_mode:
            logger.debug(f"[FAKE] Executing calculator: {expression}")
            return "dummy calculator output", ToolCallStatus.SUCCESS

        try:
            if len(expression) > 200 or not re.fullmatch(
                r"[0-9+\-*/().\s]+", expression
            ):
                return "Error: Invalid expression", ToolCallStatus.ERROR
            tree = ast.parse(expression, mode="eval")
            if sum(1 for _ in ast.walk(tree)) > 64:
                return "Error: Expression is too complex", ToolCallStatus.ERROR
            with localcontext() as context:
                context.prec = 32
                result = self._eval_ast(tree.body)
                return format(result.normalize(), "f"), ToolCallStatus.SUCCESS

        except Exception as e:
            return f"Error: {str(e)}", ToolCallStatus.ERROR

    @classmethod
    def _eval_ast(cls, node: ast.AST) -> Decimal:
        limit = Decimal("1e12")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = Decimal(str(node.value))
        elif isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            operand = cls._eval_ast(node.operand)
            result = operand if isinstance(node.op, ast.UAdd) else -operand
        elif isinstance(node, ast.BinOp):
            left, right = cls._eval_ast(node.left), cls._eval_ast(node.right)
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                result = left / right
            else:
                raise ValueError("Unsupported calculator operator")
        else:
            raise ValueError("Unsupported calculator syntax")
        if not result.is_finite() or abs(result) > limit:
            raise ValueError("Calculator value exceeds its limit")
        return result
