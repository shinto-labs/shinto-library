# integration_tests/qc_run_perf.py
"""Soft-budget timing for a complex Limburg-shaped QC run over a large project set."""

from __future__ import annotations

import asyncio
import logging

from shinto.qc import run_qc

PROJECT_COUNT = 10_000
# Generous soft ceiling for Docker/CI; logged elapsed_ms is the useful signal.
BUDGET_MS = 30_000.0

_PLANTTYPES = (
    "uitbreiding_uitleg",
    "uitbreiding_uitleg",
    "inbreiding",
    "transformatie",
)
_STATUSES = ("gereed", "gereed", "gereed", "gereed")


def _make_stages(index: int) -> list[dict]:
    stages: list[dict] = []
    stage_count = 4 + (index % 3)  # 4–6 stages per project
    for stage_index in range(stage_count):
        plantype = _PLANTTYPES[stage_index % len(_PLANTTYPES)]
        bruto = 8 + ((index + stage_index) % 13)
        netto = max(1, bruto - (1 + (stage_index % 3)))
        jaar_start = 2020 + (stage_index % 5)
        stages.append(
            {
                "planstatus": _STATUSES[stage_index % len(_STATUSES)],
                "bruto_aantalwoningen": bruto,
                "netto_aantalwoningen": netto,
                "plantype": plantype,
                "code": f"P{index}-S{stage_index}",
                "jaar_start": jaar_start,
                "jaar_eind": jaar_start + 4 + (stage_index % 3),
                "gemeente": f"Gemeente-{index % 50}",
                "opmerkingen": f"Cluster {index} stage {stage_index} limburg weert",
            }
        )
    return stages


def _make_geo(index: int) -> list[dict]:
    # Always include a valid polygon; half also carry a point (multi-geo).
    geo = [
        {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [5.0 + (index % 10) * 0.01, 51.0],
                        [5.1 + (index % 10) * 0.01, 51.0],
                        [5.1 + (index % 10) * 0.01, 51.1],
                        [5.0 + (index % 10) * 0.01, 51.0],
                    ]
                ],
            }
        }
    ]
    if index % 2 == 0:
        geo.append(
            {
                "geometry": {
                    "type": "Point",
                    "coordinates": [5.05 + (index % 10) * 0.01, 51.05],
                }
            }
        )
    return geo


def _make_project(index: int) -> dict:
    return {
        "id": str(index),
        "data": {
            "name": f"NL-LIM-{index:05d} Weert Noord",
            "project_code": f"NL{index:05d}",
            "provincie": "Limburg",
            "jaar": 2024 + (index % 3),
            "settings_note": "basisset limburg pack",
            "meta": {
                "bron": "gemeente",
                "tags": ["woningbouw", "limburg", f"batch-{index % 20}"],
            },
            "stages": _make_stages(index),
            "geo": _make_geo(index),
        },
    }


def _make_pack() -> dict:
    return {
        "version": "perf-test-complex",
        "rules": [
            {
                "id": "all_stages_gereed",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "len(stages) >= 4 and all_equal(stages, 'planstatus', 'gereed')"
                ),
                "onFail": {"message": "Not all stages are gereed"},
            },
            {
                "id": "capacity_sums",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "sum_num(stages, 'bruto_aantalwoningen') > 0 "
                    "and sum_num(stages, 'netto_aantalwoningen') > 0 "
                    "and sum_num(stages, 'bruto_aantalwoningen') "
                    ">= sum_num(stages, 'netto_aantalwoningen')"
                ),
                "onFail": {"message": "Invalid woning capacity sums"},
            },
            {
                "id": "uitbreiding_capacity",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', "
                    "'uitbreiding_uitleg') > 0 "
                    "and any_positive(stages, ['bruto_aantalwoningen', 'netto_aantalwoningen'])"
                ),
                "onFail": {"message": "Expected uitbreiding capacity"},
            },
            {
                "id": "geometry_ok",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "has_polygon_geometry(geo) "
                    "and (has_point_geometry(geo) or single_geo_type(geo) == 'Polygon') "
                    "and len(geo) >= 1"
                ),
                "onFail": {"message": "Expected polygon (and optional point) geometry"},
            },
            {
                "id": "codes_and_fields",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "values_unique(stages, 'code') "
                    "and any_field_set(stages, ['plantype', 'gemeente', 'jaar_start']) "
                    "and not is_empty(project_code) "
                    "and starts_with(project_code, 'NL') "
                    "and str_contains(name, 'weert')"
                ),
                "onFail": {"message": "Codes/fields/name checks failed"},
            },
            {
                "id": "year_and_window",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "in_year_window(jaar, 2020, 2030) "
                    "and min_num(stages, 'jaar_start') >= 2020 "
                    "and min_num(stages, 'jaar_eind') >= min_num(stages, 'jaar_start')"
                ),
                "onFail": {"message": "Year window checks failed"},
            },
            {
                "id": "text_and_coalesce",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "any_value_contains(meta, 'limburg') "
                    "and str_contains(coalesce(settings_note, ''), 'limburg') "
                    "and trim(provincie) == 'Limburg' "
                    "and has(meta, 'bron') "
                    "and num(str(jaar)) >= 2024"
                ),
                "onFail": {"message": "Text/coalesce/meta checks failed"},
            },
            {
                "id": "combined_gate",
                "kind": "assert",
                "scope": "project",
                "expression": (
                    "all_equal(stages, 'planstatus', 'gereed') "
                    "and has_polygon_geometry(geo) "
                    "and sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', "
                    "'uitbreiding_uitleg') "
                    "+ sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'inbreiding') "
                    "+ sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'transformatie') "
                    "== sum_num(stages, 'bruto_aantalwoningen') "
                    "and len(stages) == len(stages)"
                ),
                "onFail": {"message": "Combined capacity/geometry gate failed"},
            },
        ],
    }


def run_integration_test(conn) -> None:
    """conn is unused; kept for parity with other integration tests."""
    del conn
    logging.info(
        "Starting QC perf integration test: projects=%s budget_ms=%s",
        PROJECT_COUNT,
        BUDGET_MS,
    )

    project_list = [_make_project(index) for index in range(PROJECT_COUNT)]
    taxonomy = {
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "project_code", "type": "string"},
            {"name": "provincie", "type": "string"},
            {"name": "jaar", "type": "number"},
        ]
    }
    pack = _make_pack()

    result = asyncio.run(run_qc(project_list, taxonomy, pack, profile_rules=True))
    elapsed_ms = float(result["elapsedMs"])

    logging.info(
        "QC perf result: projects=%s rules=%s stages_total=%s elapsed_ms=%.2f "
        "budget_ms=%s label=%s issues=%s",
        PROJECT_COUNT,
        len(pack["rules"]),
        result["summary"]["data"]["stagesTotal"],
        elapsed_ms,
        BUDGET_MS,
        result.get("label"),
        result.get("issues"),
    )
    rule_timings = result.get("ruleTimingsMs") or {}
    if rule_timings:
        logging.info("QC perf rule timings (ms): %s", rule_timings)

    if result["issues"] != 0:
        raise AssertionError(f"expected 0 issues, got {result['issues']}")
    if result["majorIssues"] != []:
        raise AssertionError(f"expected no majorIssues, got {result['majorIssues']}")
    if result["summary"]["data"]["projectsWithIssues"] != 0:
        raise AssertionError(
            "expected no projectsWithIssues, "
            f"got {result['summary']['data']['projectsWithIssues']}"
        )
    failing = [row for row in result["checkOverview"] if not row["pass"]]
    if failing:
        raise AssertionError(f"expected all checks to pass, failing={failing}")
    if elapsed_ms > BUDGET_MS:
        raise AssertionError(
            f"QC perf budget exceeded: elapsed_ms={elapsed_ms:.2f} > budget_ms={BUDGET_MS}"
        )

    logging.info("QC perf integration test completed")
