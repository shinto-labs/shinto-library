#!/usr/bin/env python3

import json
import copy
from typing import Any, Dict, List, Optional
from glom import glom, PathAccessError
import logging


TRUE_SET = {"true", "1", "yes", "y", "ja", "j", "waar", "t"}
FALSE_SET = {"false", "0", "no", "n", "nee", "onwaar", "f"}

def to_bool(v: Any) -> Optional[bool]:
    """Convert various values to boolean."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in TRUE_SET:
            return True
        if s in FALSE_SET:
            return False
    return bool(v)


def cast_value(value: Any, typ: Optional[str]) -> Any:
    """Cast value to specified type."""
    if typ is None:
        return value
    t = typ.lower()
    if t in ("string", "str", "text"):
        if value is None:
            return None
        return str(value)
    if t in ("int", "integer"):
        if value is None or value == "":
            return None
        return int(value)
    if t in ("float", "number"):
        if value is None or value == "":
            return None
        return float(value)
    if t in ("bool", "boolean"):
        return to_bool(value)
    if t in ("json", "object", "dict"):
        if isinstance(value, str):
            return json.loads(value)
        return value
    raise ValueError(f"Unknown type: {typ}")


SAFE_BUILTINS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "sorted": sorted,
    "any": any,
    "all": all,
    "next": next,
    "type": type,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "trim": str.strip,
}


class SafeContext(dict):
    """Dict that returns None for missing keys instead of raising KeyError."""
    def __missing__(self, key):
        # Don't intercept builtin lookups - let them fall through
        raise KeyError(key)

    def __getitem__(self, key):
        # Return None for missing data keys, but let KeyError propagate for others
        try:
            return super().__getitem__(key)
        except KeyError:
            # If it's not in the dict, return None (for data fields)
            return None


def eval_expr(expr: str, ctx: Dict[str, Any]) -> Any:
    """Evaluate a Python expression using row fields as variables.

    Returns None if the expression fails (e.g., missing fields in comparisons).
    """
    try:
        safe_ctx = SafeContext(ctx)
        # Add safe builtins to the context
        for k, v in SAFE_BUILTINS.items():
            safe_ctx[k] = v
        # Use SafeContext directly so __getitem__ override works
        return eval(expr, {"__builtins__": {}}, safe_ctx)
    except Exception as e:
        # If fields are missing or comparisons fail, return None
        logging.error(f"Expression evaluation failed: {expr} - Error: {type(e).__name__}: {e}")
        # raise
        return None
    # return simple_eval(expr, names=ctx, functions=SAFE_BUILTINS)


class DefaultingDict(dict):
    """Dict that returns empty string for missing keys."""
    def __missing__(self, key):
        return ""


def resolve_source(row: Dict[str, Any], source: Optional[Dict[str, Any]]) -> Any:
    """
    Resolve source specification to a value.

    Source forms:
      - {"const": 123} - constant value
      - {"path": "field_name"} - extract field from row (supports dot notation and glom paths)
      - {"template": "Text {field}"} - format template with row fields
      - {"expr": "field1 + field2"} - evaluate Python expression
    """
    if source is None:
        return None
    if "const" in source:
        return source["const"]
    if "path" in source:
        # Path extraction using glom (supports dot notation, array indexing, etc.)
        try:
            return glom(row, source["path"], default=None)
        except (PathAccessError, KeyError):
            return None
    if "template" in source:
        tmpl = source["template"]
        safe_map = {k: ("" if v is None else v) for k, v in row.items()}
        return tmpl.format_map(DefaultingDict(safe_map))
    if "expr" in source:
        return eval_expr(source["expr"], row)

    if "remap" in source:
        val = row.get(source["remap"]["value_source"], None)
        mapping = source["remap"].get("mapping", {})
        result = mapping.get(str(val), source["remap"].get("default", None))
        return result

    raise ValueError(f"Unknown source spec: {source}")


def passes_filter(row: Dict[str, Any], flt: Optional[Dict[str, Any]]) -> bool:
    """
    Check if row passes filter.

    Filter forms:
      - {"expr": "field == 'value'"} - Python expression
      - {"all": [{filter}, {filter}]} - all must pass
      - {"any": [{filter}, {filter}]} - at least one must pass
      - {"not": {filter}} - negation
      - {"exists": {"path": "field"}} - field exists
      - {"eq": [{source}, {source}]} - equality
      - {"in": [{source}, {source}]} - membership
    """
    if not flt:
        return True

    if "expr" in flt:
        return bool(eval_expr(flt["expr"], row))

    if "all" in flt:
        return all(passes_filter(row, f) for f in flt["all"])
    if "any" in flt:
        return any(passes_filter(row, f) for f in flt["any"])
    if "not" in flt:
        return not passes_filter(row, flt["not"])

    if "exists" in flt:
        p = flt["exists"]["path"]
        try:
            val = glom(row, p, default=None)
            return val is not None
        except (PathAccessError, KeyError):
            return False

    if "eq" in flt:
        left = resolve_source(row, flt["eq"][0])
        right = resolve_source(row, flt["eq"][1])
        return left == right

    if "in" in flt:
        left = resolve_source(row, flt["in"][0])
        right = resolve_source(row, flt["in"][1])
        if right is None:
            return False
        return left in right

    raise ValueError(f"Unknown filter spec: {flt}")


def apply_action(out_row: Dict[str, Any], in_row: Dict[str, Any], action: Dict[str, Any]) -> None:
    """
    Apply a single transformation action.

    Actions:
      - add_field: Add field if it doesn't exist
      - set_field: Set field (overwrite if exists)
      - remove_field: Remove field
      - rename_field: Rename field
      - copy_field: Copy field to another name
      - remap_field: Remap categorical field value using mapping
    """
    kind = action.get("action")

    if kind in ("add_field", "set_field"):
        key = action["key"]
        typ = action.get("type")
        src = action.get("source")

        val = resolve_source(in_row, src)
        val = cast_value(val, typ)

        # add_field does not overwrite if key exists
        if kind == "add_field" and key in out_row:
            return
        out_row[key] = val
        return

    if kind == "remove_field":
        key = action["key"]
        out_row.pop(key, None)
        return

    if kind == "rename_field":
        src = action["from"]
        dst = action["to"]
        if src in out_row:
            out_row[dst] = out_row.pop(src)
        return

    if kind == "copy_field":
        src = action["from"]
        dst = action["to"]
        if src in in_row:
            out_row[dst] = copy.deepcopy(in_row[src])
        return

    raise ValueError(f"Unknown action: {kind}")


def transform_data(data: List[Dict[str, Any]], transformation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply transformation pipeline to stage data.

    Args:
        data: List of stage dictionaries
        transformation: Pipeline configuration (list of transformation steps)

    Returns:
        Transformed stage data
    """
    cur = data

    for step in transformation:
        init = step.get("init", "copy")
        actions = step.get("transformations", [])
        flt = step.get("filter")

        nxt: List[Dict[str, Any]] = []
        for r in cur:
            # Initialize output row
            base = copy.deepcopy(r) if init == "copy" else {"_metadata": r.get("_metadata", {})}

            # Apply actions in order
            in_view = {**r, **base}
            for a in actions:
                apply_action(base, in_view, a)
                # Refresh in_view so later actions can see earlier outputs
                in_view = {**r, **base}

            # Apply filter
            if passes_filter(base, flt):
                nxt.append(base)

        cur = nxt

    return cur


