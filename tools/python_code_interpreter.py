from __future__ import annotations

import ast
import math
from typing import Any


class PythonCodeInterpreter:
    """Execute calculation-oriented Python with imports and file access blocked."""

    _allowed_builtins = {"abs", "max", "min", "pow", "round", "sum"}

    def execute(self, code: str, variables: dict[str, Any] | None = None) -> Any:
        tree = ast.parse(code, mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute, ast.Lambda)):
                raise ValueError("Only simple calculation expressions are allowed")
            if isinstance(node, ast.Name) and node.id.startswith("__"):
                raise ValueError("Private names are not allowed")
        scope = {name: getattr(math, name) for name in ("ceil", "floor", "sqrt")}
        scope.update(variables or {})
        return eval(compile(tree, "<assistant-calculation>", "eval"), {"__builtins__": {}}, scope)
