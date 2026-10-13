"""Unit tests for Limburg QC dialect helpers."""

from shinto.qc.expression_eval import evaluate_bool


def test_all_equal_and_sum_helpers():
    ctx = {
        "stages": [
            {
                "planstatus": "gereed",
                "bruto_aantalwoningen": 5,
                "plantype": "uitbreiding_uitleg",
            },
            {
                "planstatus": "gereed",
                "bruto_aantalwoningen": 10,
                "plantype": "uitbreiding_uitleg",
            },
        ],
        "geo": [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                }
            }
        ],
    }
    assert evaluate_bool("all_equal(stages, 'planstatus', 'gereed')", ctx)
    assert not evaluate_bool("all_equal(stages, 'planstatus', 'actief')", ctx)
    assert evaluate_bool("sum_num(stages, 'bruto_aantalwoningen') == 15", ctx)
    assert evaluate_bool(
        "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'uitbreiding_uitleg') == 15",
        ctx,
    )
    assert evaluate_bool("has_polygon_geometry(geo)", ctx)
