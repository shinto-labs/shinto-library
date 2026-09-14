"""Year × value / field-emptiness matrix helpers for QC pack rules."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SEVERITIES = frozenset({"ok", "warn", "fail"})


def reference_year(settings: dict | None = None) -> int:
    settings = settings or {}
    explicit = settings.get("referenceYear")
    if explicit is not None:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            pass
    return datetime.now(timezone.utc).year


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def resolve_year_value(data: dict, matrix: dict) -> int | None:
    """Resolve absolute calendar year from project data per matrix.yearMode."""
    year_field = matrix.get("yearField") or "opleverjaar"
    mode = matrix.get("yearMode") or "min_stages"
    if mode == "min_stages":
        stages = data.get("stages") if isinstance(data.get("stages"), list) else []
        years = [_to_int(stage.get(year_field)) for stage in stages if isinstance(stage, dict)]
        years = [y for y in years if y is not None]
        return min(years) if years else None
    if mode == "project_field":
        return _to_int(data.get(year_field))
    return _to_int(data.get(year_field))


def year_bin_index(year: int | None, matrix: dict, ref_year: int) -> int | None:
    """Return cell column index, or None when year missing."""
    if year is None:
        return None
    bins = matrix.get("bins") or {}
    start = int(bins.get("start", 0))
    end_inclusive = int(bins.get("endInclusive", 15))
    overflow_from = int(bins.get("overflowFrom", end_inclusive + 1))
    relative = int(year) - int(ref_year)
    if relative < start:
        # Past / before window: treat as first bin (lopend) for policy lookup
        return 0
    if relative >= overflow_from:
        return end_inclusive - start + 1  # overflow column
    return relative - start


def lookup_severity(
    row_value: Any,
    bin_index: int | None,
    matrix: dict,
) -> str:
    """Return ok|warn|fail for a matrix cell."""
    default = matrix.get("defaultCell") or "fail"
    if default not in SEVERITIES:
        default = "fail"

    if bin_index is None:
        sev = matrix.get("missingYear") or default
        return sev if sev in SEVERITIES else default

    if row_value is None or row_value == "":
        sev = matrix.get("missingRowValue") or default
        return sev if sev in SEVERITIES else default

    row_key = str(row_value)
    cells = matrix.get("cells") or {}
    row_cells = cells.get(row_key)
    if not isinstance(row_cells, list):
        sev = matrix.get("unknownRowValue") or default
        return sev if sev in SEVERITIES else default

    if bin_index < 0 or bin_index >= len(row_cells):
        return default

    sev = row_cells[bin_index]
    return sev if sev in SEVERITIES else default


def evaluate_year_value_matrix(
    data: dict,
    matrix: dict,
    settings: dict | None = None,
) -> dict[str, Any]:
    """Evaluate one year_value_matrix rule against project data."""
    ref = reference_year(settings)
    year = resolve_year_value(data, matrix)
    bin_index = year_bin_index(year, matrix, ref)
    row_field = matrix.get("rowField") or "planologische_status"
    row_value = data.get(row_field)
    severity = lookup_severity(row_value, bin_index, matrix)
    relative = None if year is None else int(year) - ref
    result = {
        "severity": severity,
        "rowField": row_field,
        "rowValue": row_value,
        "yearField": matrix.get("yearField") or "opleverjaar",
        "year": year,
        "referenceYear": ref,
        "relativeYear": relative,
        "binIndex": bin_index,
    }
    if severity != "ok":
        logger.debug(
            "year_value_matrix %s: field=%s value=%s year=%s bin=%s",
            severity,
            row_field,
            row_value,
            year,
            bin_index,
        )
    return result


_SEVERITY_RANK = {"ok": 0, "warn": 1, "fail": 2}


def _worse_severity(a: str, b: str) -> str:
    return a if _SEVERITY_RANK.get(a, 0) >= _SEVERITY_RANK.get(b, 0) else b


def _is_empty_value(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _field_level(matrix: dict, field: str) -> str:
    levels = matrix.get("fieldLevel") or {}
    return str(levels.get(field) or "project")


def _lookup_empty_severity(field: str, bin_index: int | None, matrix: dict) -> str:
    """Severity when a field is empty at the given year bin."""
    return lookup_severity(field, bin_index, matrix)


def evaluate_year_field_empty_matrix(
    data: dict,
    matrix: dict,
    settings: dict | None = None,
) -> dict[str, Any]:
    """
    Evaluate emptiness policy: cells say ok|warn|fail when the field is empty
    at a relative opleverjaar bin. Filled fields always pass for that cell.
    """
    ref = reference_year(settings)
    year_field = matrix.get("yearField") or "opleverjaar"
    project_year = resolve_year_value(data, matrix)
    project_bin = year_bin_index(project_year, matrix, ref)
    stages = data.get("stages") if isinstance(data.get("stages"), list) else []
    rows = matrix.get("rows") or []

    overall = "ok"
    hits: list[dict[str, Any]] = []

    for field in rows:
        field_key = str(field)
        level = _field_level(matrix, field_key)

        if level == "year":
            # "May opleverjaar be empty?" — empty means no resolvable year.
            if project_year is not None:
                continue
            sev = _lookup_empty_severity(field_key, None, matrix)
            if sev == "ok":
                continue
            overall = _worse_severity(overall, sev)
            hits.append(
                {
                    "field": field_key,
                    "level": "year",
                    "severity": sev,
                    "year": None,
                    "binIndex": None,
                }
            )
            continue

        if level == "stage":
            if not stages:
                # No stages: treat as empty at project year bin (or missing year).
                sev = _lookup_empty_severity(field_key, project_bin, matrix)
                if sev != "ok":
                    overall = _worse_severity(overall, sev)
                    hits.append(
                        {
                            "field": field_key,
                            "level": "stage",
                            "severity": sev,
                            "year": project_year,
                            "binIndex": project_bin,
                            "stageIndex": None,
                        }
                    )
                continue
            for stage_index, stage in enumerate(stages):
                if not isinstance(stage, dict):
                    continue
                stage_year = _to_int(stage.get(year_field))
                bin_index = year_bin_index(stage_year, matrix, ref)
                if not _is_empty_value(stage.get(field_key)):
                    continue
                sev = _lookup_empty_severity(field_key, bin_index, matrix)
                if sev == "ok":
                    continue
                overall = _worse_severity(overall, sev)
                hits.append(
                    {
                        "field": field_key,
                        "level": "stage",
                        "severity": sev,
                        "year": stage_year,
                        "binIndex": bin_index,
                        "stageIndex": stage_index,
                    }
                )
            continue

        # project-level field
        if not _is_empty_value(data.get(field_key)):
            continue
        sev = _lookup_empty_severity(field_key, project_bin, matrix)
        if sev == "ok":
            continue
        overall = _worse_severity(overall, sev)
        hits.append(
            {
                "field": field_key,
                "level": "project",
                "severity": sev,
                "year": project_year,
                "binIndex": project_bin,
            }
        )

    relative = None if project_year is None else int(project_year) - ref
    result = {
        "severity": overall,
        "yearField": year_field,
        "year": project_year,
        "referenceYear": ref,
        "relativeYear": relative,
        "binIndex": project_bin,
        "hits": hits,
        "rowField": "fields",
        "rowValue": None,
    }
    if hits:
        logger.debug(
            "year_field_empty_matrix %s: hits=%s year=%s",
            overall,
            len(hits),
            project_year,
        )
    return result
