"""
QC rule helpers: taxonomy/data rule runners, scans, and issue recording.

Used by qc.run_qc. Leaf deps: expression_eval, hygiene, matrix.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Any

from shinto.qc import expression_eval
from shinto.qc import hygiene
from shinto.qc import matrix

logger = logging.getLogger(__name__)


def _is_empty(value: Any) -> bool:
    return expression_eval._is_empty(value)  # noqa: SLF001


def _allowed_values(field: dict) -> set[str]:
    return {
        str(entry.get("value"))
        for entry in (field.get("values") or [])
        if entry is not None and entry.get("value") is not None
    }


def _multi_separators(field: dict, settings: dict) -> list[str]:
    separator = field.get("separator")
    if isinstance(separator, str) and separator:
        return [separator]
    return list(settings.get("multiCategoricalSeparators") or [";", ","])


def _core_field(settings: dict, field_name: str) -> dict | None:
    for entry in settings.get("coreFields") or []:
        if entry.get("field") == field_name:
            return entry
    return None


def _effective_type(field: dict, settings: dict) -> str | None:
    core = _core_field(settings, field.get("field"))
    if core and core.get("type"):
        return core["type"]
    return field.get("type")


def parse_multi_categorical(raw: Any, field: dict, settings: dict) -> Any:
    if _is_empty(raw):
        return None
    if isinstance(raw, list):
        return [entry for entry in raw if not _is_empty(entry)]
    if isinstance(raw, str):
        separators = _multi_separators(field, settings)
        parts = [raw]
        for separator in separators:
            if separator in raw:
                parts = raw.split(separator)
                break
        return [part.strip() for part in parts if part.strip()]
    return {"invalidType": True}


def _base_context(settings: dict, taxonomy: dict | None) -> dict[str, Any]:
    reference_year = settings.get("referenceYear")
    if reference_year is None:
        reference_year = date.today().year
    return {
        "settings": settings,
        "taxonomy": taxonomy,
        "stageTimeFields": settings.get("stageTimeFields") or [],
        "stageCountFields": settings.get("stageCountFields") or [],
        "validLevels": settings.get("validLevels") or [],
        "referenceYear": reference_year,
    }


def _eval_bool(expression: str, context: dict[str, Any]) -> bool:
    try:
        return expression_eval.evaluate_bool(expression, context)
    except expression_eval.ExpressionError as exc:
        logger.warning("Expression failed (%s): %s", expression, exc)
        return False


def _when_applies(when: str | None, context: dict[str, Any]) -> bool | None:
    """
    Evaluate an optional when-clause.

    Returns:
      True  — rule applies
      False — rule skipped
      None  — expression error (caller should fail closed)
    """
    if not when:
        return True
    try:
        return bool(expression_eval.evaluate_bool(when, context))
    except expression_eval.ExpressionError as exc:
        logger.warning(
            "When-clause failed (%s): %s — failing rule closed", when, exc
        )
        return None


def _resolve_on_fail_fields(on_fail: dict | None) -> list[str]:
    """Fields to highlight from onFail.fields or onFail.field."""
    on_fail = on_fail or {}
    fields = on_fail.get("fields")
    if isinstance(fields, list):
        return [str(item) for item in fields if item not in (None, "")]
    field = on_fail.get("field")
    if field not in (None, ""):
        return [str(field)]
    return []


def _record_rule_failure(qc: dict, rule: dict) -> None:
    """Stamp major message + stable check id used by overview aggregation."""
    on_fail = rule.get("onFail") or {}
    flag = on_fail.get("projectQcFlag")
    if flag:
        qc["project_qc"][flag] = True
        qc["project_qc"]["issues"] += 1
    message = on_fail.get("message")
    if on_fail.get("major") and message and message not in qc["majorIssues"]:
        qc["majorIssues"].append(message)
    check_id = rule.get("id")
    if check_id:
        failed = qc.setdefault("failedCheckIds", [])
        if check_id not in failed:
            failed.append(check_id)
    logger.debug(
        "Rule failure: id=%s checkCode=%s major=%s",
        rule.get("id"),
        rule.get("checkCode"),
        bool(on_fail.get("major")),
    )


def _append_detail_issue(
    qc: dict,
    *,
    check_id: str,
    check_code: str,
    niveau: str,
    field: str,
    detail: str,
    path: str | None = None,
    stage_uuid: str | None = None,
    stage_index: int | None = None,
    severity: str = "fail",
    count_issue: bool = True,
) -> None:
    issues = qc.setdefault("detailIssues", [])
    entry: dict[str, Any] = {
        "checkId": check_id,
        "checkCode": check_code,
        "niveau": niveau,
        "field": field,
        "path": path or field,
        "detail": detail,
        "severity": severity,
    }
    if stage_uuid:
        entry["stageUuid"] = stage_uuid
    if stage_index is not None:
        entry["stageIndex"] = stage_index
    issues.append(entry)
    failed = qc.setdefault("failedCheckIds", [])
    if check_id and check_id not in failed:
        failed.append(check_id)
    if count_issue:
        qc["project_qc"]["issues"] = int(qc["project_qc"].get("issues") or 0) + 1


def _emit_rule_detail_issues(
    qc: dict,
    rule: dict,
    *,
    niveau: str,
    detail: str,
    path: str | None = None,
    stage_uuid: str | None = None,
    stage_index: int | None = None,
    count_issue: bool = True,
) -> None:
    """Emit one detailIssue per onFail field (or a single row when fields are empty)."""
    on_fail = rule.get("onFail") or {}
    fields = _resolve_on_fail_fields(on_fail)
    check_id = rule.get("id") or ""
    check_code = rule.get("checkCode") or "D??"
    if not fields:
        _append_detail_issue(
            qc,
            check_id=check_id,
            check_code=check_code,
            niveau=niveau,
            field="—",
            detail=detail,
            path=path or "—",
            stage_uuid=stage_uuid,
            stage_index=stage_index,
            count_issue=count_issue,
        )
        return
    for field in fields:
        if stage_index is not None:
            field_path = f"stages[{stage_index}].{field}"
        else:
            field_path = field
        _append_detail_issue(
            qc,
            check_id=check_id,
            check_code=check_code,
            niveau=niveau,
            field=field,
            detail=detail,
            path=field_path,
            stage_uuid=stage_uuid,
            stage_index=stage_index,
            count_issue=count_issue,
        )


def _record_rule_warning(qc: dict, rule: dict, detail: dict | None = None) -> None:
    """Record soft matrix/policy warning without failing binary QC."""
    check_id = rule.get("id")
    if check_id:
        warnings = qc.setdefault("warningCheckIds", [])
        if check_id not in warnings:
            warnings.append(check_id)
    on_warn = rule.get("onWarn") or {}
    message = on_warn.get("message")
    if message:
        soft = qc.setdefault("softIssues", [])
        if message not in soft:
            soft.append(message)
    if detail:
        issues = qc.setdefault("detailIssues", [])
        issues.append(
            {
                "checkId": check_id,
                "checkCode": rule.get("checkCode"),
                "niveau": "project",
                "field": detail.get("rowField"),
                "path": detail.get("rowField"),
                "detail": message or rule.get("id"),
                "severity": "warn",
                "matrix": {
                    "rowValue": detail.get("rowValue"),
                    "year": detail.get("year"),
                    "relativeYear": detail.get("relativeYear"),
                    "binIndex": detail.get("binIndex"),
                },
            }
        )
    logger.debug(
        "Rule warning: id=%s checkCode=%s",
        rule.get("id"),
        rule.get("checkCode"),
    )


def _run_year_value_matrix_rules(
    qc: dict,
    data: dict,
    rules: list[dict],
    settings: dict,
) -> None:
    if not rules:
        return
    for rule in rules:
        matrix = rule.get("matrix") or {}
        result = matrix.evaluate_year_value_matrix(data, matrix, settings)
        severity = result.get("severity") or "ok"
        if severity == "fail":
            _record_rule_failure(qc, rule)
            on_fail = rule.get("onFail") or {}
            issues = qc.setdefault("detailIssues", [])
            issues.append(
                {
                    "checkId": rule.get("id"),
                    "checkCode": rule.get("checkCode"),
                    "niveau": "project",
                    "field": result.get("rowField"),
                    "path": result.get("rowField"),
                    "detail": on_fail.get("message") or rule.get("id"),
                    "severity": "fail",
                    "matrix": {
                        "rowValue": result.get("rowValue"),
                        "year": result.get("year"),
                        "relativeYear": result.get("relativeYear"),
                        "binIndex": result.get("binIndex"),
                    },
                }
            )
        elif severity == "warn":
            _record_rule_warning(qc, rule, result)


def _run_year_field_empty_matrix_rules(
    qc: dict,
    data: dict,
    rules: list[dict],
    settings: dict,
) -> None:
    if not rules:
        return
    for rule in rules:
        matrix = rule.get("matrix") or {}
        result = matrix.evaluate_year_field_empty_matrix(data, matrix, settings)
        hits = result.get("hits") or []
        fail_hits = [h for h in hits if h.get("severity") == "fail"]
        warn_hits = [h for h in hits if h.get("severity") == "warn"]

        if fail_hits:
            _record_rule_failure(qc, rule)
            on_fail = rule.get("onFail") or {}
            issues = qc.setdefault("detailIssues", [])
            for hit in fail_hits:
                issues.append(
                    {
                        "checkId": rule.get("id"),
                        "checkCode": rule.get("checkCode"),
                        "niveau": hit.get("level") or "project",
                        "field": hit.get("field"),
                        "path": hit.get("field"),
                        "detail": on_fail.get("message")
                        or f"{hit.get('field')} mag niet leeg zijn",
                        "severity": "fail",
                        "matrix": {
                            "rowValue": hit.get("field"),
                            "year": hit.get("year"),
                            "binIndex": hit.get("binIndex"),
                            "stageIndex": hit.get("stageIndex"),
                        },
                    }
                )

        if warn_hits:
            warn_detail = {
                **result,
                "rowField": "fields",
                "rowValue": ", ".join(
                    str(h.get("field")) for h in warn_hits if h.get("field")
                ),
            }
            _record_rule_warning(qc, rule, warn_detail)


def _run_unique(rule: dict, taxonomy: dict | None) -> list[dict]:
    fields = (taxonomy or {}).get("fields") or []
    collect = rule.get("collect") or "fields"
    if collect != "fields":
        return []
    key_name = rule.get("key") or "field"
    skip_empty = bool(rule.get("skipEmpty"))
    counts: dict[Any, list[str]] = defaultdict(list)
    for field in fields:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        key = field.get(key_name)
        if skip_empty and (key is None or key == ""):
            continue
        if key is None:
            continue
        counts[key].append(field["field"])

    issues = []
    template = rule.get("messageTemplate") or 'Duplicate "{key}" ({count})'
    issue_code = rule.get("issueCode") or rule["id"]
    for key, names in counts.items():
        if len(names) <= 1:
            continue
        message = template.format(key=key, count=len(names), fields=", ".join(names))
        field_value = ", ".join(names) if rule.get("fieldFrom") == "fields" else str(key)
        issues.append({"field": field_value, "code": issue_code, "message": message})
    return issues


def _run_unique_nested(rule: dict, taxonomy: dict | None, settings: dict) -> list[dict]:
    fields = (taxonomy or {}).get("fields") or []
    type_filter = set(rule.get("whenTypeIn") or [])
    nested = rule.get("nested") or "values"
    nested_key = rule.get("nestedKey") or "value"
    issue_code = rule.get("issueCode") or rule["id"]
    template = rule.get("messageTemplate") or 'Duplicate "{key}" in {field}'
    issues = []
    for field in fields:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        if type_filter and field.get("type") not in type_filter:
            continue
        value_counts: dict[str, int] = defaultdict(int)
        for entry in field.get(nested) or []:
            if not isinstance(entry, dict) or entry.get(nested_key) is None:
                continue
            value_counts[str(entry[nested_key])] += 1
        for key, count in value_counts.items():
            if count > 1:
                issues.append(
                    {
                        "field": field["field"],
                        "code": issue_code,
                        "message": template.format(
                            field=field["field"], key=key, count=count
                        ),
                    }
                )
    return issues


def _run_core_fields(rule: dict, taxonomy: dict | None, settings: dict) -> list[dict]:
    check = rule.get("check")
    issue_code = rule.get("issueCode") or rule["id"]
    by_name = {
        field["field"]: field
        for field in ((taxonomy or {}).get("fields") or [])
        if isinstance(field, dict) and field.get("field")
    }
    issues = []
    for core in settings.get("coreFields") or []:
        found = by_name.get(core["field"])
        if check == "missing":
            if not found:
                issues.append(
                    {
                        "field": core["field"],
                        "code": issue_code,
                        "message": (
                            f'Core veld "{core["field"]}" ontbreekt in de taxonomie '
                            f'(verwacht type "{core["type"]}", level "{core["level"]}")'
                        ),
                    }
                )
            continue
        if not found:
            continue
        if check == "type" and found.get("type") != core["type"]:
            issues.append(
                {
                    "field": core["field"],
                    "code": issue_code,
                    "message": (
                        f'Core veld "{core["field"]}" heeft type "{found.get("type") or "—"}", '
                        f'verwacht "{core["type"]}"'
                    ),
                }
            )
        if check == "level":
            level = found.get("level")
            if level and level != core["level"]:
                issues.append(
                    {
                        "field": core["field"],
                        "code": issue_code,
                        "message": (
                            f'Core veld "{core["field"]}" heeft level "{level}", '
                            f'verwacht "{core["level"]}"'
                        ),
                    }
                )
    return issues


def _run_taxonomy_field_asserts(
    rules: list[dict], taxonomy: dict | None, settings: dict, base_ctx: dict
) -> list[dict]:
    issues = []
    fields = (taxonomy or {}).get("fields") or []
    for field in fields:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        ctx = {
            **base_ctx,
            **field,
            "field": field.get("field"),
            "level": field.get("level"),
            "type": field.get("type"),
            "label": field.get("label"),
        }
        for rule in rules:
            applies = _when_applies(rule.get("when"), ctx)
            if applies is False:
                continue
            if applies is not None and _eval_bool(rule["expression"], ctx):
                continue
            on_fail = rule.get("onFail") or {}
            template = on_fail.get("messageTemplate")
            message = (
                template.format(**{k: ctx.get(k) for k in ("field", "level", "type", "label")})
                if template
                else on_fail.get("message") or f'Check failed: {rule["id"]}'
            )
            issues.append(
                {
                    "field": field["field"],
                    "code": rule.get("issueCode") or rule["id"],
                    "message": message,
                }
            )
    return issues


def _run_taxonomy_required_props(rule: dict, taxonomy: dict | None, settings: dict) -> list[dict]:
    props = list(rule.get("props") or settings.get("requiredTaxonomyFieldProps") or [
        "field", "type", "label", "level"
    ])
    issue_code = rule.get("issueCode") or rule["id"]
    issues: list[dict] = []
    for index, field in enumerate((taxonomy or {}).get("fields") or []):
        if not isinstance(field, dict):
            issues.append(
                {
                    "field": f"(index {index})",
                    "code": issue_code,
                    "message": f"Taxonomie-entry op index {index} is geen object",
                }
            )
            continue
        field_name = field.get("field") or f"(index {index})"
        missing = [p for p in props if _is_empty(field.get(p))]
        if missing:
            issues.append(
                {
                    "field": str(field_name),
                    "code": issue_code,
                    "message": (
                        f'Taxonomieveld "{field_name}" mist verplichte properties: '
                        + ", ".join(missing)
                    ),
                }
            )
    return issues


def _run_taxonomy_categorical_schema(
    rule: dict, taxonomy: dict | None, settings: dict
) -> list[dict]:
    type_filter = set(rule.get("whenTypeIn") or ["categorical", "multi_categorical"])
    issue_code = rule.get("issueCode") or rule["id"]
    issues: list[dict] = []
    for field in (taxonomy or {}).get("fields") or []:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        if field.get("type") not in type_filter:
            continue
        name = field["field"]
        values = field.get("values")
        if not isinstance(values, list):
            issues.append(
                {
                    "field": name,
                    "code": issue_code,
                    "message": f'Veld "{name}": values moet een array van objecten zijn',
                }
            )
            continue
        if len(values) == 0:
            issues.append(
                {
                    "field": name,
                    "code": issue_code,
                    "message": f'Veld "{name}": values[] mag niet leeg zijn',
                }
            )
            continue
        ranks: dict[Any, int] = defaultdict(int)
        for entry_index, entry in enumerate(values):
            if not isinstance(entry, dict):
                issues.append(
                    {
                        "field": name,
                        "code": issue_code,
                        "message": (
                            f'Veld "{name}": values[{entry_index}] moet een object zijn '
                            f"met label, rank, value"
                        ),
                    }
                )
                continue
            for prop in ("label", "rank", "value"):
                if prop not in entry or entry.get(prop) is None or entry.get(prop) == "":
                    issues.append(
                        {
                            "field": name,
                            "code": issue_code,
                            "message": (
                                f'Veld "{name}": values[{entry_index}] mist "{prop}"'
                            ),
                        }
                    )
            rank = entry.get("rank")
            if rank is not None:
                if not isinstance(rank, int) or isinstance(rank, bool):
                    issues.append(
                        {
                            "field": name,
                            "code": issue_code,
                            "message": (
                                f'Veld "{name}": values[{entry_index}].rank moet een integer zijn'
                            ),
                        }
                    )
                else:
                    ranks[rank] += 1
        for rank, count in ranks.items():
            if count > 1:
                issues.append(
                    {
                        "field": name,
                        "code": issue_code,
                        "message": (
                            f'Veld "{name}": rank {rank} komt {count} keer voor in values'
                        ),
                    }
                )
    return issues


def _run_taxonomy_default_type(rule: dict, taxonomy: dict | None, settings: dict) -> list[dict]:
    issue_code = rule.get("issueCode") or rule["id"]
    issues: list[dict] = []
    for field in (taxonomy or {}).get("fields") or []:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        if "default" not in field:
            continue
        field_type = _effective_type(field, settings)
        if hygiene.default_matches_type(field.get("default"), field_type, field, settings):
            continue
        issues.append(
            {
                "field": field["field"],
                "code": issue_code,
                "message": (
                    f'Veld "{field["field"]}": default past niet bij type '
                    f'"{field_type or "—"}"'
                ),
            }
        )
    return issues


def _scan_project_hygiene(
    qc: dict,
    data: dict,
    taxonomy: dict | None,
    settings: dict,
    hygiene_rules: list[dict],
) -> None:
    if not hygiene_rules:
        return
    before = len(qc.get("detailIssues") or [])
    type_map = hygiene.build_field_type_map(taxonomy)
    string_cfg = settings.get("stringHygiene") or {}
    text_cfg = settings.get("textHygiene") or {}
    image_cfg = settings.get("embeddedImageDetection") or {}
    allowed_tags = {t.lower() for t in (text_cfg.get("allowedHtmlTags") or [])}
    forbidden_tags = {t.lower() for t in (text_cfg.get("forbiddenHtmlTags") or [])}
    temporal_types = set(settings.get("temporalTypes") or ["date", "time", "datetime"])
    min_len = int(image_cfg.get("minLength") or 256)
    checks = {rule.get("check"): rule for rule in hygiene_rules}

    for path, text in hygiene.iter_string_leaves(data, skip_keys={"qc"}):
        field_name = hygiene.path_field_name(path) or "—"
        field_type = type_map.get(field_name)
        niveau = "bouwcluster" if path.startswith("stages[") or path.startswith("stages.") else "project"

        ws_rule = checks.get("whitespace")
        if ws_rule and hygiene.has_leading_or_trailing_whitespace(text):
            _append_detail_issue(
                qc,
                check_id=ws_rule["id"],
                check_code=ws_rule.get("checkCode") or "D19",
                niveau=niveau,
                field=field_name,
                path=path,
                detail=f'Leading/trailing whitespace in "{path}"',
            )

        html_rule = checks.get("html")
        if html_rule:
            for message in hygiene.html_violations(
                text,
                field_type=field_type,
                string_forbid_html=bool(string_cfg.get("forbidHtml", True)),
                allowed_tags=allowed_tags,
                forbidden_tags=forbidden_tags,
            ):
                _append_detail_issue(
                    qc,
                    check_id=html_rule["id"],
                    check_code=html_rule.get("checkCode") or "D20",
                    niveau=niveau,
                    field=field_name,
                    path=path,
                    detail=f'{message} in "{path}"',
                )

        img_rule = checks.get("embedded_image")
        if img_rule:
            for hit in hygiene.find_embedded_images(text, min_length=min_len):
                _append_detail_issue(
                    qc,
                    check_id=img_rule["id"],
                    check_code=img_rule.get("checkCode") or "D21",
                    niveau=niveau,
                    field=field_name,
                    path=path,
                    detail=(
                        f'Ingebedde {hit["imageType"]}-afbeelding in "{path}" '
                        f'({hit["via"]}, {hit["encodedLength"]} tekens)'
                    ),
                )

        iso_rule = checks.get("temporal_iso")
        if iso_rule and field_type in temporal_types:
            if not hygiene.is_iso_temporal(text, field_type):
                _append_detail_issue(
                    qc,
                    check_id=iso_rule["id"],
                    check_code=iso_rule.get("checkCode") or "D22",
                    niveau=niveau,
                    field=field_name,
                    path=path,
                    detail=f'Waarde op "{path}" is geen geldige ISO {field_type} (zonder offset)',
                )
    added = len(qc.get("detailIssues") or []) - before
    if added:
        logger.debug("Hygiene scan added %s detail issue(s)", added)


def _scan_unknown_fields(
    qc: dict,
    data: dict,
    taxonomy: dict | None,
    settings: dict,
    rule: dict | None,
) -> None:
    if not rule:
        return
    reserved = set(settings.get("reservedProjectDataKeys") or [])
    known = {
        str(f["field"])
        for f in ((taxonomy or {}).get("fields") or [])
        if isinstance(f, dict) and f.get("field")
    }
    allowed = known | reserved
    for key in data.keys():
        if key in allowed or key == "qc":
            continue
        _append_detail_issue(
            qc,
            check_id=rule["id"],
            check_code=rule.get("checkCode") or "D23",
            niveau="project",
            field=str(key),
            path=str(key),
            detail=f'Veld "{key}" komt niet voor in de taxonomie',
        )
    stages = data.get("stages") if isinstance(data.get("stages"), list) else []
    stage_allow = known | {"id", "qc"}
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        for key in stage.keys():
            if key in stage_allow:
                continue
            _append_detail_issue(
                qc,
                check_id=rule["id"],
                check_code=rule.get("checkCode") or "D23",
                niveau="bouwcluster",
                field=str(key),
                path=f"stages[{index}].{key}",
                detail=f'Stage-veld "{key}" komt niet voor in de taxonomie',
            )


def _scan_level_placement(
    qc: dict,
    data: dict,
    taxonomy: dict | None,
    settings: dict,
    rule: dict | None,
) -> None:
    if not rule:
        return
    project_names: set[str] = set()
    stage_names: set[str] = set()
    valid = set(settings.get("validLevels") or ["project", "stage"])
    for field in (taxonomy or {}).get("fields") or []:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        level = field.get("level")
        if level not in valid:
            continue
        name = str(field["field"])
        if level == "project":
            project_names.add(name)
        else:
            stage_names.add(name)

    reserved = set(settings.get("reservedProjectDataKeys") or [])
    for key in data.keys():
        if key in reserved or key == "qc":
            continue
        if key in stage_names:
            _append_detail_issue(
                qc,
                check_id=rule["id"],
                check_code=rule.get("checkCode") or "D24",
                niveau="project",
                field=str(key),
                path=str(key),
                detail=f'Stage-veld "{key}" staat op projectniveau',
            )

    stages = data.get("stages") if isinstance(data.get("stages"), list) else []
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            continue
        for key in stage.keys():
            if key in project_names:
                _append_detail_issue(
                    qc,
                    check_id=rule["id"],
                    check_code=rule.get("checkCode") or "D24",
                    niveau="bouwcluster",
                    field=str(key),
                    path=f"stages[{index}].{key}",
                    detail=f'Projectveld "{key}" staat in een bouwcluster',
                )


def _validate_field_value(raw: Any, field: dict, buckets: dict, settings: dict) -> None:
    if _is_empty(raw):
        if field.get("mandatory"):
            buckets["missingFields"].add(field["field"])
        return

    field_type = _effective_type(field, settings)
    string_like = set(settings.get("stringLikeTypes") or [])
    object_types = set(settings.get("objectTypes") or [])
    array_types = set(settings.get("arrayTypes") or [])
    categorical_types = set(settings.get("categoricalTypes") or [])
    multi_types = set(settings.get("multiCategoricalTypes") or [])

    if field_type in string_like:
        if not isinstance(raw, str):
            buckets["invalidTypeFields"].add(field["field"])
        return
    if field_type in object_types:
        if not isinstance(raw, dict):
            buckets["invalidTypeFields"].add(field["field"])
        return
    if field_type in array_types:
        if not isinstance(raw, list):
            buckets["invalidTypeFields"].add(field["field"])
        return
    if field_type in categorical_types:
        if isinstance(raw, (dict, list)):
            buckets["invalidTypeFields"].add(field["field"])
            return
        if str(raw) not in _allowed_values(field):
            buckets["invalidValueFields"].add(field["field"])
        return
    if field_type in multi_types:
        parsed = parse_multi_categorical(raw, field, settings)
        if isinstance(parsed, dict) and parsed.get("invalidType"):
            buckets["invalidTypeFields"].add(field["field"])
            return
        if not parsed:
            if field.get("mandatory"):
                buckets["missingFields"].add(field["field"])
            return
        allowed = _allowed_values(field)
        if any(str(entry) not in allowed for entry in parsed):
            buckets["invalidValueFields"].add(field["field"])


def _partition_fields(taxonomy: dict | None, settings: dict) -> tuple[list[dict], list[dict]]:
    """Split taxonomy fields by valid level (invalid/missing level excluded from data checks)."""
    project_fields: list[dict] = []
    stage_fields: list[dict] = []
    valid = set(settings.get("validLevels") or ["project", "stage"])
    for field in (taxonomy or {}).get("fields") or []:
        if not isinstance(field, dict) or not field.get("field"):
            continue
        level = field.get("level")
        if level not in valid:
            continue
        if level == "project":
            project_fields.append(field)
        else:
            stage_fields.append(field)
    return project_fields, stage_fields
