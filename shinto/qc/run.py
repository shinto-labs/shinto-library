"""
Pack-driven QC runner for GET /juno/qc_report.

Pack + taxonomy are resolved from schema_package pins (via qc_run_context).
Rule execution lives in qc_rules; report shaping in qc_report.
"""

from __future__ import annotations

import importlib
import logging
import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any
from uuid import UUID

from shinto.mimir.data import get_project_list_async

from shinto.qc import expression_eval
from shinto.qc import report
from shinto.qc import rules

if TYPE_CHECKING:
    from shinto.pg.connection import AsyncConnection

logger = logging.getLogger(__name__)


class _RuleProfiler:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.ms: dict[str, float] = defaultdict(float)

    def tick(self, rule_id: str | None, start: float) -> None:
        if self.enabled and rule_id:
            self.ms[str(rule_id)] += (time.perf_counter() - start) * 1000

    def tick_split(self, rule_ids: list[str], start: float) -> None:
        if not self.enabled or not rule_ids:
            return
        elapsed = (time.perf_counter() - start) * 1000
        share = elapsed / len(rule_ids)
        for rule_id in rule_ids:
            self.ms[str(rule_id)] += share


def run_qc(
    project_list: list[dict],
    taxonomy: dict | None,
    pack: dict | None = None,
    profile_rules: bool = False,
) -> dict[str, Any]:
    start = time.perf_counter()
    if pack is None:
        logger.error("run_qc called without a pack")
        raise ValueError("QC pack is required; pass an explicit pack object to run_qc()")
    settings = pack.get("settings") or {}
    rules = [rule for rule in (pack.get("rules") or []) if rule.get("enabled", True)]
    project_count = len(project_list or [])
    field_count = len((taxonomy or {}).get("fields") or [])
    logger.info(
        "Starting QC run: projects=%s rules=%s taxonomy_fields=%s pack_version=%s",
        project_count,
        len(rules),
        field_count,
        pack.get("version"),
    )
    if project_count == 0:
        logger.warning("QC run has an empty project list")
    base_ctx = rules._base_context(settings, taxonomy)
    profiler = _RuleProfiler(profile_rules)

    taxonomy_issues: list[dict] = []

    # --- Taxonomy-scoped rules ---
    for rule in rules:
        t_rule = time.perf_counter()
        kind = rule.get("kind")
        scope = rule.get("scope")
        if kind == "assert" and scope == "taxonomy":
            if not rules._eval_bool(rule["expression"], base_ctx):
                on_fail = rule.get("onFail") or {}
                taxonomy_issues.append(
                    {
                        "field": on_fail.get("field") or "(taxonomy)",
                        "code": rule.get("issueCode") or rule["id"],
                        "message": on_fail.get("message") or rule["id"],
                    }
                )
        elif kind == "unique" and scope == "taxonomy":
            taxonomy_issues.extend(rules._run_unique(rule, taxonomy))
        elif kind == "unique_nested" and scope == "taxonomy":
            taxonomy_issues.extend(rules._run_unique_nested(rule, taxonomy, settings))
        elif kind == "core_fields":
            taxonomy_issues.extend(rules._run_core_fields(rule, taxonomy, settings))
        elif kind == "taxonomy_required_props":
            taxonomy_issues.extend(rules._run_taxonomy_required_props(rule, taxonomy, settings))
        elif kind == "taxonomy_categorical_schema":
            taxonomy_issues.extend(
                rules._run_taxonomy_categorical_schema(rule, taxonomy, settings)
            )
        elif kind == "taxonomy_default_type":
            taxonomy_issues.extend(rules._run_taxonomy_default_type(rule, taxonomy, settings))
        profiler.tick(rule.get("id"), t_rule)

    field_assert_rules = [
        rule
        for rule in rules
        if rule.get("kind") == "assert" and rule.get("scope") == "taxonomy_field"
    ]
    t_field_asserts = time.perf_counter()
    taxonomy_issues.extend(
        rules._run_taxonomy_field_asserts(field_assert_rules, taxonomy, settings, base_ctx)
    )
    profiler.tick_split(
        [str(rule.get("id")) for rule in field_assert_rules if rule.get("id")],
        t_field_asserts,
    )
    logger.debug(
        "Taxonomy phase done: issues=%s field_assert_rules=%s",
        len(taxonomy_issues),
        len(field_assert_rules),
    )

    project_fields, stage_fields = rules._partition_fields(taxonomy, settings)
    logger.debug(
        "Field partition: project_fields=%s stage_fields=%s",
        len(project_fields),
        len(stage_fields),
    )
    project_assert_rules = [
        rule for rule in rules if rule.get("kind") == "assert" and rule.get("scope") == "project"
    ]
    stage_assert_rules = [
        rule
        for rule in rules
        if rule.get("kind") == "assert_stages"
    ]
    flag_missing_rules = [rule for rule in rules if rule.get("kind") == "flag_missing_field"]
    validate_rules = [rule for rule in rules if rule.get("kind") == "validate_taxonomy_fields"]
    hygiene_rules = [rule for rule in rules if rule.get("kind") == "data_hygiene"]
    unknown_fields_rule = next(
        (rule for rule in rules if rule.get("kind") == "data_unknown_fields"), None
    )
    level_placement_rule = next(
        (rule for rule in rules if rule.get("kind") == "data_level_placement"), None
    )
    year_value_matrix_rules = [
        rule for rule in rules if rule.get("kind") == "year_value_matrix"
    ]
    year_field_empty_matrix_rules = [
        rule for rule in rules if rule.get("kind") == "year_field_empty_matrix"
    ]

    projects_with_issues = 0
    stages_with_issues = 0
    stages_total = 0
    project_qc_by_id: dict[str, dict] = {}

    for project in project_list or []:
        data = project.get("data")
        if not isinstance(data, dict):
            continue

        qc = report._empty_qc()
        stages = data.get("stages") if isinstance(data.get("stages"), list) else []
        stages_total += len(stages)
        geo = data.get("geo") if isinstance(data.get("geo"), list) else []

        ctx = {
            **base_ctx,
            **data,
            "geo": geo,
            "stages": stages,
            "project": project,
            "data": data,
        }

        # Taxonomy field validation (feeds D09–D14 + missingFields for D06)
        project_buckets = {
            "missingFields": set(),
            "invalidTypeFields": set(),
            "invalidValueFields": set(),
        }
        stage_buckets = {
            "missingFields": set(),
            "invalidTypeFields": set(),
            "invalidValueFields": set(),
        }
        if validate_rules:
            t_validate = time.perf_counter()
            validate_by_key = {
                (rule.get("level") or "project", rule.get("issueType")): rule
                for rule in validate_rules
            }

            def _detail_for_validate(level: str, issue_type: str, field_name: str) -> tuple[str, str, str]:
                rule = validate_by_key.get((level, issue_type)) or {}
                check_id = rule.get("id") or f"data_{level}_{issue_type}"
                check_code = rule.get("checkCode") or "D??"
                if issue_type == "missing":
                    detail = (
                        f'Verplicht projectveld "{field_name}" ontbreekt'
                        if level == "project"
                        else f'Verplicht bouwclusterveld "{field_name}" ontbreekt'
                    )
                elif issue_type == "invalid_type":
                    detail = (
                        f'Projectveld "{field_name}" heeft een ongeldig type'
                        if level == "project"
                        else f'Bouwclusterveld "{field_name}" heeft een ongeldig type'
                    )
                else:
                    detail = (
                        f'Waarde van projectveld "{field_name}" komt niet voor in de taxonomie'
                        if level == "project"
                        else f'Waarde van bouwclusterveld "{field_name}" komt niet voor in de taxonomie'
                    )
                return check_id, check_code, detail

            for field in project_fields:
                if field.get("field") == "geo":
                    continue
                rules._validate_field_value(
                    data.get(field["field"]), field, project_buckets, settings
                )

            for field_name in sorted(project_buckets["missingFields"]):
                check_id, check_code, detail = _detail_for_validate(
                    "project", "missing", field_name
                )
                rules._append_detail_issue(
                    qc,
                    check_id=check_id,
                    check_code=check_code,
                    niveau="project",
                    field=field_name,
                    path=field_name,
                    detail=detail,
                    count_issue=False,
                )
            for field_name in sorted(project_buckets["invalidTypeFields"]):
                check_id, check_code, detail = _detail_for_validate(
                    "project", "invalid_type", field_name
                )
                rules._append_detail_issue(
                    qc,
                    check_id=check_id,
                    check_code=check_code,
                    niveau="project",
                    field=field_name,
                    path=field_name,
                    detail=detail,
                    count_issue=False,
                )
            for field_name in sorted(project_buckets["invalidValueFields"]):
                check_id, check_code, detail = _detail_for_validate(
                    "project", "invalid_value", field_name
                )
                rules._append_detail_issue(
                    qc,
                    check_id=check_id,
                    check_code=check_code,
                    niveau="project",
                    field=field_name,
                    path=field_name,
                    detail=detail,
                    count_issue=False,
                )

            project_stages_with_issues = 0
            for stage_index, stage in enumerate(stages):
                per_stage = {
                    "missingFields": set(),
                    "invalidTypeFields": set(),
                    "invalidValueFields": set(),
                }
                for field in stage_fields:
                    rules._validate_field_value(
                        (stage or {}).get(field["field"]), field, per_stage, settings
                    )
                if (
                    per_stage["missingFields"]
                    or per_stage["invalidTypeFields"]
                    or per_stage["invalidValueFields"]
                ):
                    project_stages_with_issues += 1
                    stages_with_issues += 1
                stage_uuid = None
                if isinstance(stage, dict):
                    stage_uuid = stage.get("stage_uuid") or stage.get("uuid")
                    if stage_uuid is not None:
                        stage_uuid = str(stage_uuid)
                for field_name in sorted(per_stage["missingFields"]):
                    check_id, check_code, detail = _detail_for_validate(
                        "stage", "missing", field_name
                    )
                    rules._append_detail_issue(
                        qc,
                        check_id=check_id,
                        check_code=check_code,
                        niveau="bouwcluster",
                        field=field_name,
                        path=f"stages[{stage_index}].{field_name}",
                        detail=detail,
                        stage_uuid=stage_uuid,
                        stage_index=stage_index,
                        count_issue=False,
                    )
                for field_name in sorted(per_stage["invalidTypeFields"]):
                    check_id, check_code, detail = _detail_for_validate(
                        "stage", "invalid_type", field_name
                    )
                    rules._append_detail_issue(
                        qc,
                        check_id=check_id,
                        check_code=check_code,
                        niveau="bouwcluster",
                        field=field_name,
                        path=f"stages[{stage_index}].{field_name}",
                        detail=detail,
                        stage_uuid=stage_uuid,
                        stage_index=stage_index,
                        count_issue=False,
                    )
                for field_name in sorted(per_stage["invalidValueFields"]):
                    check_id, check_code, detail = _detail_for_validate(
                        "stage", "invalid_value", field_name
                    )
                    rules._append_detail_issue(
                        qc,
                        check_id=check_id,
                        check_code=check_code,
                        niveau="bouwcluster",
                        field=field_name,
                        path=f"stages[{stage_index}].{field_name}",
                        detail=detail,
                        stage_uuid=stage_uuid,
                        stage_index=stage_index,
                        count_issue=False,
                    )
                stage_buckets["missingFields"].update(per_stage["missingFields"])
                stage_buckets["invalidTypeFields"].update(per_stage["invalidTypeFields"])
                stage_buckets["invalidValueFields"].update(per_stage["invalidValueFields"])

            qc["project_qc"]["missingFields"] = sorted(project_buckets["missingFields"])
            qc["project_qc"]["invalidTypeFields"] = sorted(
                project_buckets["invalidTypeFields"]
            )
            qc["project_qc"]["invalidValueFields"] = sorted(
                project_buckets["invalidValueFields"]
            )
            qc["project_qc"]["issues"] += (
                len(qc["project_qc"]["missingFields"])
                + len(qc["project_qc"]["invalidTypeFields"])
                + len(qc["project_qc"]["invalidValueFields"])
            )
            qc["stages_qc"] = {
                "missingFields": sorted(stage_buckets["missingFields"]),
                "invalidTypeFields": sorted(stage_buckets["invalidTypeFields"]),
                "invalidValueFields": sorted(stage_buckets["invalidValueFields"]),
                "issues": (
                    len(stage_buckets["missingFields"])
                    + len(stage_buckets["invalidTypeFields"])
                    + len(stage_buckets["invalidValueFields"])
                ),
                "stagesWithIssues": project_stages_with_issues,
            }
            profiler.tick_split(
                [str(rule.get("id")) for rule in validate_rules if rule.get("id")],
                t_validate,
            )

        # Project assert expressions
        for rule in project_assert_rules:
            t_rule = time.perf_counter()
            applies = rules._when_applies(rule.get("when"), ctx)
            if applies is not False:
                if applies is None or not rules._eval_bool(rule["expression"], ctx):
                    rules._record_rule_failure(qc, rule)
                    on_fail = rule.get("onFail") or {}
                    message = on_fail.get("message") or rule.get("id")
                    # Structured row for SPA (badge + field highlight). Skip when the
                    # rule only flips a projectQcFlag without a user-facing message.
                    if message:
                        rules._emit_rule_detail_issues(
                            qc,
                            rule,
                            niveau="project",
                            detail=message,
                            path=None,
                            count_issue=not bool(on_fail.get("projectQcFlag")),
                        )
            profiler.tick(rule.get("id"), t_rule)

        # Stage assert expressions — emit detailIssues for EVERY failing stage
        for rule in stage_assert_rules:
            t_rule = time.perf_counter()
            on_fail = rule.get("onFail") or {}
            message = on_fail.get("message") or rule.get("id")
            any_failed = False
            for stage_index, stage in enumerate(stages):
                if not isinstance(stage, dict):
                    continue
                stage_ctx = {
                    **ctx,
                    **stage,
                    "stage": stage,
                }
                applies = rules._when_applies(rule.get("when"), stage_ctx)
                if applies is False:
                    continue
                if applies is None or not rules._eval_bool(rule["expression"], stage_ctx):
                    any_failed = True
                    stage_uuid = stage.get("stage_uuid") or stage.get("uuid")
                    rules._emit_rule_detail_issues(
                        qc,
                        rule,
                        niveau="bouwcluster",
                        detail=message,
                        path=f"stages[{stage_index}]",
                        stage_uuid=str(stage_uuid) if stage_uuid else None,
                        stage_index=stage_index,
                        count_issue=True,
                    )
            if any_failed:
                rules._record_rule_failure(qc, rule)
            profiler.tick(rule.get("id"), t_rule)

        # Flag missing mandatory fields as major (D06)
        for rule in flag_missing_rules:
            t_rule = time.perf_counter()
            field_name = rule.get("field")
            level = rule.get("level") or "project"
            missing = (
                qc["project_qc"]["missingFields"]
                if level == "project"
                else qc["stages_qc"]["missingFields"]
            )
            if field_name and field_name in missing:
                message = rule.get("majorMessage")
                if message and message not in qc["majorIssues"]:
                    qc["majorIssues"].append(message)
                check_id = rule.get("id")
                if check_id:
                    failed = qc.setdefault("failedCheckIds", [])
                    if check_id not in failed:
                        failed.append(check_id)
            profiler.tick(rule.get("id"), t_rule)

        t_hygiene = time.perf_counter()
        rules._scan_project_hygiene(qc, data, taxonomy, settings, hygiene_rules)
        profiler.tick_split(
            [str(rule.get("id")) for rule in hygiene_rules if rule.get("id")],
            t_hygiene,
        )
        if unknown_fields_rule:
            t_rule = time.perf_counter()
            rules._scan_unknown_fields(qc, data, taxonomy, settings, unknown_fields_rule)
            profiler.tick(unknown_fields_rule.get("id"), t_rule)
        if level_placement_rule:
            t_rule = time.perf_counter()
            rules._scan_level_placement(qc, data, taxonomy, settings, level_placement_rule)
            profiler.tick(level_placement_rule.get("id"), t_rule)
        for rule in year_value_matrix_rules:
            t_rule = time.perf_counter()
            rules._run_year_value_matrix_rules(qc, data, [rule], settings)
            profiler.tick(rule.get("id"), t_rule)
        for rule in year_field_empty_matrix_rules:
            t_rule = time.perf_counter()
            rules._run_year_field_empty_matrix_rules(qc, data, [rule], settings)
            profiler.tick(rule.get("id"), t_rule)

        report._finalize_qc(qc)
        data["qc"] = qc
        if qc["issues"] > 0 or qc["majorIssues"] or qc.get("failedCheckIds"):
            projects_with_issues += 1
            project_id = str(project.get("id") or "")
            if project_id:
                project_qc_by_id[project_id] = qc

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "QC run finished in %.2fms: projects_with_issues=%s/%s stages_with_issues=%s/%s taxonomy_issues=%s",
        elapsed_ms,
        projects_with_issues,
        project_count,
        stages_with_issues,
        stages_total,
        len(taxonomy_issues),
    )
    if profile_rules and profiler.ms:
        logger.debug("Rule timings (ms): %s", {k: round(v, 3) for k, v in sorted(profiler.ms.items())})
    return report._build_report(
        project_list or [],
        taxonomy_issues,
        rules,
        projects_with_issues,
        stages_with_issues,
        stages_total,
        elapsed_ms,
        pack,
        project_qc_by_id,
        rule_timings_ms=(
            {k: round(v, 3) for k, v in sorted(profiler.ms.items())}
            if profile_rules
            else None
        ),
    )

