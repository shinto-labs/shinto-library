"""
QC report shaping: per-project QC shell and aggregated report payload.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


def _empty_qc() -> dict:
    return {
        "color": "green",
        "icon": "check",
        "label": "goed",
        "issues": 0,
        "majorIssues": [],
        "failedCheckIds": [],
        "warningCheckIds": [],
        "softIssues": [],
        "project_qc": {
            "missingGeometry": False,
            "hasOnlyPointGeometry": False,
            "hasOnlyPolygonGeometry": False,
            "hasOnlyMultiPointGeometry": False,
            "missingFields": [],
            "invalidTypeFields": [],
            "invalidValueFields": [],
            "issues": 0,
            "missingStages": False,
        },
        "stages_qc": {
            "missingFields": [],
            "invalidTypeFields": [],
            "invalidValueFields": [],
            "issues": 0,
            "stagesWithIssues": 0,
        },
        "detailIssues": [],
    }


def _finalize_qc(qc: dict) -> None:
    qc["issues"] = qc["project_qc"]["issues"] + qc["stages_qc"]["issues"]
    qc["color"] = "green"
    qc["icon"] = "check"
    qc["label"] = "goed"
    if qc["issues"] > 0:
        qc["color"] = "amber"
        qc["icon"] = "x"
        qc["label"] = "matig"
    if qc["majorIssues"]:
        qc["color"] = "red"
        qc["icon"] = "x"
        qc["label"] = "slecht"


def _count_taxonomy_by_code(taxonomy_issues: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for issue in taxonomy_issues:
        counts[issue["code"]] += 1
    return counts


def _aggregate_data_check_counts(
    project_list: list[dict],
) -> tuple[dict[str, int], dict[str, int]]:
    """Return (issue_counts, projects_failing) per rule id."""
    issue_counts: dict[str, int] = defaultdict(int)
    project_counts: dict[str, int] = defaultdict(int)
    major_to_id = {
        "Ontbrekende tijdcontext in alle bouwclusters": "data_missing_time_context",
        "Geen bouwcluster heeft een positieve waarde voor bruto aantalwoningen of sloop aantalwoningen":
            "data_no_positive_counts",
        "Planologische status niet hard genoeg bij oplevering binnen 3 jaar":
            "data_near_term_hard_planstatus",
        "Planologische status past niet bij opleverjaar (matrix)":
            "data_near_term_hard_planstatus",
        "Verplicht veld ontbreekt bij dit opleverjaar (matrix)":
            "data_year_field_empty_matrix",
        "Waarde bevat 'onbekend'": "data_forbidden_onbekend",
    }
    for project in project_list:
        qc = (project.get("data") or {}).get("qc")
        if not qc:
            continue

        failed_ids = set(qc.get("failedCheckIds") or [])
        for rule_id in failed_ids:
            project_counts[rule_id] += 1

        for issue in qc.get("detailIssues") or []:
            check_id = issue.get("checkId")
            if check_id:
                issue_counts[str(check_id)] += 1

        # Assert rules that only set projectQcFlag (no detailIssues) still count once
        for rule_id in failed_ids:
            if issue_counts.get(rule_id, 0) == 0:
                issue_counts[rule_id] += 1

        major = qc.get("majorIssues") or []
        for message, rule_id in major_to_id.items():
            if message in major and rule_id not in failed_ids:
                project_counts[rule_id] += 1
                issue_counts[rule_id] += 1

    return issue_counts, project_counts


def _build_report(
    project_list,
    taxonomy_issues,
    rules,
    projects_with_issues,
    stages_with_issues,
    stages_total,
    elapsed_ms,
    pack,
    project_qc_by_id,
    rule_timings_ms: dict[str, float] | None = None,
):
    taxonomy_counts = _count_taxonomy_by_code(taxonomy_issues)
    issue_counts, project_counts = _aggregate_data_check_counts(project_list)

    check_overview = []
    for index, row in enumerate(rules):
        if row.get("category") == "taxonomy":
            fail_count = taxonomy_counts.get(row.get("issueCode"), 0)
            projects_failing = fail_count
        else:
            rule_id = row["id"]
            fail_count = issue_counts.get(rule_id, 0)
            projects_failing = min(project_counts.get(rule_id, 0), len(project_list))
        meta = {
            k: v
            for k, v in row.items()
            if k
            not in {
                "scope",
                "expression",
                "when",
                "onFail",
                "onWarn",
                "matrix",
                "collect",
                "key",
                "skipEmpty",
                "messageTemplate",
                "fieldFrom",
                "whenTypeIn",
                "nested",
                "nestedKey",
                "check",
                "level",
                "issueType",
                "field",
                "majorMessage",
            }
        }
        check_overview.append(
            {
                **meta,
                "index": index + 1,
                "pass": fail_count == 0,
                "failCount": fail_count,
                "projectsFailing": projects_failing,
            }
        )

    project_counts = {"goed": 0, "matig": 0, "slecht": 0, "total": len(project_list)}
    project_issues = 0
    for project in project_list:
        qc = (project.get("data") or {}).get("qc")
        if not qc:
            continue
        project_issues += qc.get("issues") or 0
        label = qc.get("label")
        if label == "slecht":
            project_counts["slecht"] += 1
        elif label == "matig":
            project_counts["matig"] += 1
        else:
            project_counts["goed"] += 1

    major_issues = [issue["message"] for issue in taxonomy_issues]
    issues = project_issues + len(taxonomy_issues)
    label = "goed"
    color = "green"
    icon = "check"
    if issues > 0:
        label = "matig"
        color = "amber"
        icon = "x"
    if major_issues or project_counts["slecht"] > 0:
        label = "slecht"
        color = "red"
        icon = "x"

    failing_checks = sum(1 for row in check_overview if not row["pass"])

    logger.info(
        "Built QC report: label=%s issues=%s failing_checks=%s projects=%s elapsed_ms=%s",
        label,
        issues,
        failing_checks,
        project_counts["total"],
        elapsed_ms,
    )
    logger.debug(
        "Report breakdown: goed=%s matig=%s slecht=%s taxonomy_issues=%s projects_with_issues=%s",
        project_counts["goed"],
        project_counts["matig"],
        project_counts["slecht"],
        len(taxonomy_issues),
        projects_with_issues,
    )

    return {
        "label": label,
        "color": color,
        "icon": icon,
        "issues": issues,
        "majorIssues": major_issues,
        "projectCounts": project_counts,
        "taxonomyIssues": taxonomy_issues,
        "checkOverview": check_overview,
        "summary": {
            "data": {
                "projectsWithIssues": projects_with_issues,
                "projectsTotal": len(project_list),
                "stagesWithIssues": stages_with_issues,
                "stagesTotal": stages_total,
            },
            "taxonomy": {"issueCount": len(taxonomy_issues)},
            "config": {"issueCount": failing_checks},
        },
        "elapsedMs": elapsed_ms,
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rulesVersion": pack.get("version"),
        "projectQcById": project_qc_by_id,
        **(
            {"ruleTimingsMs": rule_timings_ms}
            if rule_timings_ms is not None
            else {}
        ),
    }
