"""
QC gate evaluation for create/update save flows.

Gates are metadata on pack rules (`onCreate` / `onUpdate` / `onLegacy`).
This module turns a per-project QC result into structured gate decisions
so HTTP handlers / UIs can block or warn without re-running rules.
"""

from __future__ import annotations

from typing import Any


def _rule_index(pack: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rules = (pack or {}).get("rules") or []
    out: dict[str, dict[str, Any]] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("id")
        if rule_id:
            out[str(rule_id)] = rule
    return out


def _previous_failed_ids(previous_qc: dict[str, Any] | None) -> set[str]:
    if not isinstance(previous_qc, dict):
        return set()
    return {str(x) for x in (previous_qc.get("failedCheckIds") or []) if x}


def resolve_gate_action(
    *,
    mode: str,
    gates: dict[str, Any] | None,
    check_id: str,
    previous_failed: set[str],
) -> str:
    """
    Resolve the effective gate action for one failing check.

    mode: 'create' | 'update' | 'legacy'
    """
    gates = gates if isinstance(gates, dict) else {}
    if mode == "create":
        return str(gates.get("onCreate") or "report")
    if mode == "legacy":
        return str(gates.get("onLegacy") or "report")

    # update
    action = str(gates.get("onUpdate") or "report")
    if action == "block_if_introduced":
        if check_id in previous_failed:
            return "report"
        return "block"
    return action


def evaluate_gates(
    qc: dict[str, Any] | None,
    pack: dict[str, Any] | None,
    *,
    mode: str = "create",
    previous_qc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Map failed checks to gate decisions.

    Returns:
      {
        ok: bool,              # False when any action == block
        mode: str,
        blocking: [...],       # failing checks that block save
        warnings: [...],       # failing checks that warn
        reports: [...],        # failing checks that only report
        issues: [...],         # all gated failures with action
      }
    """
    qc = qc if isinstance(qc, dict) else {}
    failed_ids = [str(x) for x in (qc.get("failedCheckIds") or []) if x]
    by_id = _rule_index(pack)
    previous_failed = _previous_failed_ids(previous_qc)

    detail_by_check: dict[str, list[dict[str, Any]]] = {}
    for detail in qc.get("detailIssues") or []:
        if not isinstance(detail, dict):
            continue
        check_id = detail.get("checkId")
        if not check_id:
            continue
        detail_by_check.setdefault(str(check_id), []).append(detail)

    blocking: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for check_id in failed_ids:
        rule = by_id.get(check_id) or {}
        action = resolve_gate_action(
            mode=mode,
            gates=rule.get("gates"),
            check_id=check_id,
            previous_failed=previous_failed,
        )
        item = {
            "checkId": check_id,
            "checkCode": rule.get("checkCode"),
            "name": rule.get("name") or rule.get("regel") or check_id,
            "action": action,
            "fields": ((rule.get("onFail") or {}).get("fields") or []),
            "message": ((rule.get("onFail") or {}).get("message") or rule.get("regel") or check_id),
            "detailIssues": detail_by_check.get(check_id) or [],
            "gates": rule.get("gates") or {},
        }
        issues.append(item)
        if action == "block":
            blocking.append(item)
        elif action == "warn":
            warnings.append(item)
        else:
            reports.append(item)

    return {
        "ok": len(blocking) == 0,
        "mode": mode,
        "blocking": blocking,
        "warnings": warnings,
        "reports": reports,
        "issues": issues,
    }


async def evaluate_qc_project(
    project: dict[str, Any],
    taxonomy: dict[str, Any] | None,
    pack: dict[str, Any] | None,
    *,
    mode: str = "create",
    previous_qc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run pack QC for a single draft project and apply gates for save.

    `project` should look like a mimir project record: `{id?, data:{...}}`.
    """
    from shinto.qc.run import run_qc

    if not isinstance(project, dict):
        raise ValueError("project must be an object")
    data = project.get("data")
    if not isinstance(data, dict):
        raise ValueError("project.data must be an object")

    # Avoid mutating caller draft: shallow-copy project/data before run_qc writes qc.
    project_copy = {**project, "data": {**data}}
    if "id" not in project_copy or project_copy.get("id") in (None, ""):
        project_copy["id"] = "draft"

    report = await run_qc([project_copy], taxonomy, pack)
    qc = (project_copy.get("data") or {}).get("qc") or {}
    gates = evaluate_gates(qc, pack, mode=mode, previous_qc=previous_qc)

    return {
        "ok": gates["ok"],
        "mode": mode,
        "qc": qc,
        "gates": gates,
        "blocking": gates["blocking"],
        "warnings": gates["warnings"],
        "reports": gates["reports"],
        "issues": gates["issues"],
        "checkOverview": report.get("checkOverview"),
        "summary": report.get("summary"),
        "rulesVersion": pack.get("version") if isinstance(pack, dict) else None,
        "elapsedMs": report.get("elapsedMs"),
    }
