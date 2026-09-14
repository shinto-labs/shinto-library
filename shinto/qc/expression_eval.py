"""
Safe QC expression evaluator.

Dialect (portable pack expressions):
  - Literals: null/None, true/false, numbers, strings
  - Operators: and, or, not, ==, !=, <, <=, >, >=, in, not in
  - Attribute / subscript: geo, stages[0], settings.validLevels
  - Calls: only helpers listed below (no arbitrary Python)

Helpers:
  is_empty(value)           — None, "", []
  len(value)                — length of str/list/dict (0 if None)
  trim(value)               — strip string ("" if not str)
  coalesce(a, b, ...)       — first non-empty
  has(obj, key)             — key in mapping
  str(value), num(value)    — conversions (num → None on failure)
  has_point_geometry(geo)   — Point with non-empty coordinates
  single_geo_type(geo)      — geometry.type when len(geo)==1 else None
  any_field_set(rows, keys) — any row has any key non-None
  any_positive(rows, keys)  — any row has any key with number > 0
  min_num(rows, key)        — min numeric value of key across rows (None if none)
  in_year_window(year, start, end) — True when year is numeric and start<=year<=end
  any_value_contains(value, needle) — recursive case-insensitive substring search
  starts_with(value, prefix) — str(value).startswith(prefix)
  str_contains(value, needle) — case-insensitive substring
  values_unique(rows, key) — non-empty values of key across row dicts are unique
"""

from __future__ import annotations

import ast
import logging
import operator
from typing import Any, Callable

logger = logging.getLogger(__name__)

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_CMP_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.And,
    ast.Or,
    ast.Not,
    ast.USub,
    ast.UAdd,
    *tuple(_BIN_OPS.keys()),
    *tuple(_CMP_OPS.keys()),
    ast.Index,  # py3.8 compat if present
)


def _is_empty(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _len(value: Any) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 0


def _trim(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _coalesce(*values: Any) -> Any:
    for value in values:
        if not _is_empty(value):
            return value
    return None


def _has(obj: Any, key: Any) -> bool:
    if isinstance(obj, dict):
        return key in obj
    return False


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_point_geometry(geo: Any) -> bool:
    if not isinstance(geo, list):
        return False
    for item in geo:
        geometry = (item or {}).get("geometry") or {}
        if geometry.get("type") == "Point":
            coordinates = geometry.get("coordinates")
            return isinstance(coordinates, list) and len(coordinates) > 0
    return False


def _single_geo_type(geo: Any) -> str | None:
    if not isinstance(geo, list) or len(geo) != 1:
        return None
    return ((geo[0] or {}).get("geometry") or {}).get("type")


def _any_field_set(rows: Any, keys: Any) -> bool:
    if not isinstance(rows, list) or not isinstance(keys, (list, tuple)):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in keys:
            if row.get(key) is not None:
                return True
    return False


def _any_positive(rows: Any, keys: Any) -> bool:
    if not isinstance(rows, list) or not isinstance(keys, (list, tuple)):
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in keys:
            number = _num(row.get(key))
            if number is not None and number > 0:
                return True
    return False


def _min_num(rows: Any, key: Any) -> float | None:
    if not isinstance(rows, list) or key is None:
        return None
    values: list[float] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        number = _num(row.get(key))
        if number is not None:
            values.append(number)
    if not values:
        return None
    return min(values)


def _in_year_window(year: Any, start: Any, end: Any) -> bool:
    value = _num(year)
    low = _num(start)
    high = _num(end)
    if value is None or low is None or high is None:
        return False
    return low <= value <= high


def _any_value_contains(value: Any, needle: Any, _depth: int = 0) -> bool:
    if _depth > 24 or needle is None:
        return False
    text = str(needle).lower()
    if not text:
        return False
    if isinstance(value, str):
        return text in value.lower()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "qc":
                continue
            if _any_value_contains(child, needle, _depth + 1):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(
            _any_value_contains(child, needle, _depth + 1) for child in value
        )
    return False


def _starts_with(value: Any, prefix: Any) -> bool:
    if value is None or prefix is None:
        return False
    return str(value).startswith(str(prefix))


def _str_contains(value: Any, needle: Any) -> bool:
    if value is None or needle is None:
        return False
    return str(needle).lower() in str(value).lower()


def _values_unique(rows: Any, key: Any) -> bool:
    """True when non-empty values of key across rows are unique."""
    if not isinstance(rows, list):
        return True
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = row.get(key)
        if _is_empty(raw):
            continue
        text = str(raw).strip()
        if not text:
            continue
        if text in seen:
            return False
        seen.add(text)
    return True


HELPERS: dict[str, Callable[..., Any]] = {
    "is_empty": _is_empty,
    "len": _len,
    "trim": _trim,
    "coalesce": _coalesce,
    "has": _has,
    "str": lambda value: "" if value is None else str(value),
    "num": _num,
    "has_point_geometry": _has_point_geometry,
    "single_geo_type": _single_geo_type,
    "any_field_set": _any_field_set,
    "any_positive": _any_positive,
    "min_num": _min_num,
    "in_year_window": _in_year_window,
    "any_value_contains": _any_value_contains,
    "starts_with": _starts_with,
    "str_contains": _str_contains,
    "values_unique": _values_unique,
}


class ExpressionError(ValueError):
    """Raised when an expression is invalid or unsafe."""


def _validate_ast(node: ast.AST) -> None:
    for child in ast.walk(node):
        if not isinstance(child, _ALLOWED_NODES):
            # ast.Index removed in 3.9+; ignore unknown Index-like
            if type(child).__name__ == "Index":
                continue
            raise ExpressionError(f"Disallowed expression node: {type(child).__name__}")
        if isinstance(child, ast.Call):
            if not isinstance(child.func, ast.Name):
                raise ExpressionError("Only direct helper calls are allowed")
            if child.func.id not in HELPERS:
                raise ExpressionError(f"Unknown helper: {child.func.id}")
            if child.keywords:
                raise ExpressionError("Keyword arguments are not allowed")


def _eval(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, context)

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        if node.id in ("null", "None"):
            return None
        if node.id in ("true", "True"):
            return True
        if node.id in ("false", "False"):
            return False
        if node.id in context:
            return context[node.id]
        if node.id in HELPERS:
            return HELPERS[node.id]
        # Missing project/stage fields are omitted from JSON; treat as empty.
        return None

    if isinstance(node, ast.Attribute):
        value = _eval(node.value, context)
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(node.attr)
        return getattr(value, node.attr, None)

    if isinstance(node, ast.Subscript):
        value = _eval(node.value, context)
        sl = node.slice
        # py3.9+: slice is the expression directly
        key = _eval(sl, context) if not isinstance(sl, ast.Slice) else None
        if isinstance(sl, ast.Slice):
            raise ExpressionError("Slices are not allowed")
        if value is None:
            return None
        try:
            return value[key]
        except (KeyError, IndexError, TypeError):
            return None

    if isinstance(node, ast.List):
        return [_eval(elt, context) for elt in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_eval(elt, context) for elt in node.elts)

    if isinstance(node, ast.Dict):
        return {
            _eval(k, context): _eval(v, context)
            for k, v in zip(node.keys, node.values)
            if k is not None
        }

    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand, context)
        if isinstance(node.op, ast.Not):
            return not bool(operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ExpressionError("Unsupported unary operator")

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = _eval(value, context)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _eval(value, context)
                if result:
                    return result
            return result
        raise ExpressionError("Unsupported boolean operator")

    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if not op:
            raise ExpressionError("Unsupported binary operator")
        return op(_eval(node.left, context), _eval(node.right, context))

    if isinstance(node, ast.Compare):
        left = _eval(node.left, context)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _CMP_OPS.get(type(op_node))
            if not op:
                raise ExpressionError("Unsupported comparison")
            right = _eval(comparator, context)
            if not op(left, right):
                return False
            left = right
        return True

    if isinstance(node, ast.Call):
        assert isinstance(node.func, ast.Name)
        func = HELPERS[node.func.id]
        args = [_eval(arg, context) for arg in node.args]
        return func(*args)

    raise ExpressionError(f"Cannot evaluate node: {type(node).__name__}")


def evaluate(expression: str, context: dict[str, Any] | None = None) -> Any:
    """Evaluate a pack expression against a context dict."""
    if not isinstance(expression, str) or not expression.strip():
        logger.error("Empty or non-string expression")
        raise ExpressionError("Expression must be a non-empty string")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        logger.debug("Expression syntax error (%r): %s", expression, exc)
        raise ExpressionError(f"Syntax error: {exc}") from exc
    try:
        _validate_ast(tree)
        return _eval(tree, context or {})
    except ExpressionError as exc:
        logger.debug("Expression evaluation failed (%r): %s", expression, exc)
        raise


def evaluate_bool(expression: str, context: dict[str, Any] | None = None) -> bool:
    """Evaluate expression and coerce to bool."""
    return bool(evaluate(expression, context))
