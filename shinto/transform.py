#!/usr/bin/env python3

import logging
import json
import copy
from typing import Any, Dict, List, Optional


def projects_to_stage_data(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ transform projects_data to stage_data.
    stage_data is a list of stages, each stage is a dict with stage info
    and a list of projects in that stage."""
    projects_data = []
    for project in projects:
        # add id and timestamp to project data
        project_data = project.get("data", {})
        for key,value in project.items():
            if key not in ["data"]:
                if "_metadata" not in project_data:
                    project_data["_metadata"] = {}
                project_data["_metadata"][key] = value
        projects_data.append(project_data)

    stage_data = []
    for project in projects_data:
        for stage in project.get("stages", []):
            stage_info = stage.copy()
            for project_key, project_value in project.items():
                if project_key in stage_info:
                    logging.warning(
                        f"Key {project_key} in project data conflicts with stage data. Stage data will take precedence.")
                elif project_key != "stages":
                    stage_info[project_key] = project_value
            stage_data.append(stage_info)
    return stage_data

def stage_data_to_projects(stage_data: List[Dict[str, Any]], taxonomy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """ stage_data_to_projects takes stage_data and taxonomy as input
    and reconstructs the original projects_data structure."""

    # Build field level mapping from taxonomy
    field_level_map = {}
    if taxonomy and "fields" in taxonomy:
        for field_def in taxonomy["fields"]:
            field_name = field_def.get("field")
            level = field_def.get("level", "stage")  # Default to stage if not specified
            field_level_map[field_name] = level

    projects_dict = {}
    for stage in stage_data:
        # Extract project_id from _metadata
        metadata = stage.get("_metadata", {})
        project_id = metadata.get("id")

        if project_id not in projects_dict:
            # Initialize project with metadata
            projects_dict[project_id] = {
                "id": project_id,
                "timestamp": metadata.get("timestamp"),
                "data": {}
            }
            # Copy other metadata fields to the project level
            for meta_key, meta_value in metadata.items():
                if meta_key not in ["id", "timestamp"]:
                    projects_dict[project_id][meta_key] = meta_value

        project_data = projects_dict[project_id]["data"]

        # Initialize stages array if not present
        if "stages" not in project_data:
            project_data["stages"] = []

        # Create a new stage dict for this stage's fields
        stage_dict = {}

        for key, value in stage.items():
            if key not in ["_metadata"]:
                # Check if field has a defined level in taxonomy
                level = field_level_map.get(key, "stage")  # Default to stage if not in taxonomy

                if level == "stage":
                    # Add to stage dict
                    stage_dict[key] = value
                elif level == "project":
                    # Add to project data (only once, from first stage)
                    if key not in project_data:
                        project_data[key] = value

        # Add the stage to the stages array
        if stage_dict:  # Only add if there are stage fields
            project_data["stages"].append(stage_dict)

    return list(projects_dict.values())


# ---------------------------
# Transformation functions
# ---------------------------

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
}


def eval_expr(expr: str, ctx: Dict[str, Any]) -> Any:
    """Evaluate a Python expression using row fields as variables."""
    locals_ = dict(ctx)
    return eval(expr, {"__builtins__": SAFE_BUILTINS}, locals_)


class DefaultingDict(dict):
    """Dict that returns empty string for missing keys."""
    def __missing__(self, key):
        return ""


def resolve_source(row: Dict[str, Any], source: Optional[Dict[str, Any]]) -> Any:
    """
    Resolve source specification to a value.

    Source forms:
      - {"const": 123} - constant value
      - {"path": "field_name"} - extract field from row
      - {"template": "Text {field}"} - format template with row fields
      - {"expr": "field1 + field2"} - evaluate Python expression
    """
    if source is None:
        return None
    if "const" in source:
        return source["const"]
    if "path" in source:
        # Simple path extraction
        return row.get(source["path"])
    if "template" in source:
        tmpl = source["template"]
        safe_map = {k: ("" if v is None else v) for k, v in row.items()}
        return tmpl.format_map(DefaultingDict(safe_map))
    if "expr" in source:
        return eval_expr(source["expr"], row)
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
        return row.get(p) is not None

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
        if src in out_row:
            out_row[dst] = copy.deepcopy(out_row[src])
        return

    raise ValueError(f"Unknown action: {kind}")


def transform_stage_data(stage_data: List[Dict[str, Any]], transformation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply transformation pipeline to stage data.

    Args:
        stage_data: List of stage dictionaries
        transformation: Pipeline configuration (list of transformation steps)

    Returns:
        Transformed stage data
    """
    cur = stage_data

    for step in transformation:
        init = step.get("init", "copy")
        actions = step.get("transformations", [])
        flt = step.get("filter")

        nxt: List[Dict[str, Any]] = []
        for r in cur:
            # Initialize output row
            base = copy.deepcopy(r) if init == "copy" else {}

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


