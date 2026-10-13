# integration_tests/qc_expression_helpers.py
"""Exercise every QC expression helper one by one."""

import logging

from shinto.qc.expression_eval import HELPERS, evaluate, evaluate_bool

# Shared fixture data for row/geo helpers.
_STAGES = [
    {
        "planstatus": "gereed",
        "bruto_aantalwoningen": 5,
        "plantype": "uitbreiding_uitleg",
        "code": "A",
    },
    {
        "planstatus": "gereed",
        "bruto_aantalwoningen": 10,
        "plantype": "uitbreiding_uitleg",
        "code": "B",
    },
    {
        "planstatus": "actief",
        "bruto_aantalwoningen": 3,
        "plantype": "inbreiding",
        "code": "C",
    },
]

_GEO_POINT = [{"geometry": {"type": "Point", "coordinates": [5.0, 52.0]}}]
_GEO_POLYGON = [
    {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
    }
]

# Each helper → list of (expression, context, expected) exercised one by one.
# Expected may be bool (via evaluate_bool) or any other value (via evaluate).
HELPER_CASES: dict[str, list[tuple[str, dict, object]]] = {
    "is_empty": [
        ("is_empty(empty_str)", {"empty_str": ""}, True),
        ("is_empty(value)", {"value": "x"}, False),
        ("is_empty(items)", {"items": []}, True),
        ("is_empty(missing)", {}, True),
    ],
    "len": [
        ("len(text) == 3", {"text": "abc"}, True),
        ("len(items) == 2", {"items": [1, 2]}, True),
        ("len(missing) == 0", {}, True),
    ],
    "trim": [
        ("trim(text) == 'ab'", {"text": "  ab  "}, True),
        ("trim(num) == ''", {"num": 12}, True),
    ],
    "coalesce": [
        ("coalesce('', null, 'ok') == 'ok'", {}, True),
        ("coalesce('first', 'second') == 'first'", {}, True),
    ],
    "has": [
        ("has(obj, 'a')", {"obj": {"a": 1}}, True),
        ("has(obj, 'b')", {"obj": {"a": 1}}, False),
        ("has(missing, 'a')", {}, False),
    ],
    "str": [
        ("str(n) == '12'", {"n": 12}, True),
        ("str(missing) == ''", {}, True),
    ],
    "num": [
        ("num('3.5') == 3.5", {}, True),
        ("num('x') == null", {}, True),
        ("num(null) == null", {}, True),
    ],
    "has_point_geometry": [
        ("has_point_geometry(geo)", {"geo": _GEO_POINT}, True),
        ("has_point_geometry(geo)", {"geo": _GEO_POLYGON}, False),
        ("has_point_geometry(geo)", {"geo": []}, False),
    ],
    "single_geo_type": [
        ("single_geo_type(geo) == 'Point'", {"geo": _GEO_POINT}, True),
        ("single_geo_type(geo) == null", {"geo": _GEO_POINT + _GEO_POLYGON}, True),
        ("single_geo_type(geo) == null", {"geo": []}, True),
    ],
    "any_field_set": [
        ("any_field_set(stages, ['plantype'])", {"stages": _STAGES}, True),
        ("any_field_set(stages, ['missing_field'])", {"stages": _STAGES}, False),
        ("any_field_set(stages, ['x'])", {"stages": []}, False),
    ],
    "any_positive": [
        (
            "any_positive(stages, ['bruto_aantalwoningen'])",
            {"stages": _STAGES},
            True,
        ),
        (
            "any_positive(stages, ['bruto_aantalwoningen'])",
            {"stages": [{"bruto_aantalwoningen": 0}]},
            False,
        ),
    ],
    "min_num": [
        ("min_num(stages, 'bruto_aantalwoningen') == 3", {"stages": _STAGES}, True),
        ("min_num(stages, 'bruto_aantalwoningen') == null", {"stages": []}, True),
    ],
    "in_year_window": [
        ("in_year_window(2024, 2020, 2030)", {}, True),
        ("in_year_window(2019, 2020, 2030)", {}, False),
        ("in_year_window(null, 2020, 2030)", {}, False),
    ],
    "any_value_contains": [
        ("any_value_contains(payload, 'weert')", {"payload": {"name": "Weert-Noord"}}, True),
        ("any_value_contains(payload, 'missing')", {"payload": {"name": "Weert"}}, False),
    ],
    "starts_with": [
        ("starts_with(code, 'NL')", {"code": "NL123"}, True),
        ("starts_with(code, 'BE')", {"code": "NL123"}, False),
    ],
    "str_contains": [
        ("str_contains(name, 'LIM')", {"name": "limburg"}, True),
        ("str_contains(name, 'xyz')", {"name": "limburg"}, False),
    ],
    "values_unique": [
        ("values_unique(stages, 'code')", {"stages": _STAGES}, True),
        (
            "values_unique(stages, 'planstatus')",
            {"stages": _STAGES},
            False,
        ),
    ],
    "all_equal": [
        (
            "all_equal(stages, 'planstatus', 'gereed')",
            {"stages": _STAGES[:2]},
            True,
        ),
        (
            "all_equal(stages, 'planstatus', 'gereed')",
            {"stages": _STAGES},
            False,
        ),
        ("all_equal(stages, 'planstatus', 'gereed')", {"stages": []}, False),
    ],
    "sum_num": [
        ("sum_num(stages, 'bruto_aantalwoningen') == 18", {"stages": _STAGES}, True),
        ("sum_num(stages, 'bruto_aantalwoningen') == 0", {"stages": []}, True),
    ],
    "sum_num_if": [
        (
            "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'uitbreiding_uitleg') == 15",
            {"stages": _STAGES},
            True,
        ),
        (
            "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'unknown') == 0",
            {"stages": _STAGES},
            True,
        ),
    ],
    "has_polygon_geometry": [
        ("has_polygon_geometry(geo)", {"geo": _GEO_POLYGON}, True),
        ("has_polygon_geometry(geo)", {"geo": _GEO_POINT}, False),
        ("has_polygon_geometry(geo)", {"geo": []}, False),
    ],
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_integration_test(conn) -> None:
    """conn is unused; kept for parity with other integration tests."""
    del conn
    logging.info("Starting QC expression helper integration test")

    registered = set(HELPERS)
    covered = set(HELPER_CASES)
    missing = registered - covered
    unexpected = covered - registered
    _assert(not missing, f"helpers without cases: {sorted(missing)}")
    _assert(not unexpected, f"cases for unknown helpers: {sorted(unexpected)}")

    for helper_name in sorted(HELPER_CASES):
        cases = HELPER_CASES[helper_name]
        logging.info("Helper %s: %s case(s)", helper_name, len(cases))
        for index, (expression, context, expected) in enumerate(cases):
            if isinstance(expected, bool):
                actual = evaluate_bool(expression, context)
            else:
                actual = evaluate(expression, context)
            _assert(
                actual == expected,
                (
                    f"helper={helper_name!r} case={index} expr={expression!r} "
                    f"expected={expected!r} actual={actual!r}"
                ),
            )

    logging.info("QC expression helper integration test completed (%s helpers)", len(HELPER_CASES))
