"""Unit tests for Limburg QC dialect helpers and expression AST cache."""

import unittest

from shinto.qc.expression_eval import (
    ExpressionError,
    _AST_CACHE,
    clear_expression_cache,
    evaluate,
    evaluate_bool,
)

_STAGES = [
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
]

_GEO_POLYGON = [
    {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
        }
    }
]


class TestLimburgHelpers(unittest.TestCase):
    """Limburg dialect helpers + compile cache."""

    def setUp(self):
        clear_expression_cache()

    def tearDown(self):
        clear_expression_cache()

    def test_all_equal_and_sum_helpers_happy_path(self):
        ctx = {"stages": _STAGES, "geo": _GEO_POLYGON}
        self.assertTrue(evaluate_bool("all_equal(stages, 'planstatus', 'gereed')", ctx))
        self.assertFalse(evaluate_bool("all_equal(stages, 'planstatus', 'actief')", ctx))
        self.assertTrue(evaluate_bool("sum_num(stages, 'bruto_aantalwoningen') == 15", ctx))
        self.assertTrue(
            evaluate_bool(
                "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'uitbreiding_uitleg') == 15",
                ctx,
            )
        )
        self.assertTrue(evaluate_bool("has_polygon_geometry(geo)", ctx))

    def test_all_equal_edge_cases(self):
        self.assertFalse(
            evaluate_bool("all_equal(stages, 'planstatus', 'gereed')", {"stages": []})
        )
        self.assertFalse(
            evaluate_bool("all_equal(stages, 'planstatus', 'gereed')", {"stages": None})
        )
        self.assertFalse(
            evaluate_bool(
                "all_equal(stages, 'planstatus', 'gereed')",
                {"stages": [{"planstatus": "gereed"}, "not-a-dict"]},
            )
        )
        self.assertFalse(
            evaluate_bool(
                "all_equal(stages, 'planstatus', 'gereed')",
                {"stages": [{"planstatus": "gereed"}, {"planstatus": None}]},
            )
        )

    def test_sum_num_skips_non_numeric_and_empty(self):
        ctx = {
            "stages": [
                {"bruto_aantalwoningen": 5},
                {"bruto_aantalwoningen": "x"},
                {"bruto_aantalwoningen": None},
                {"other": 99},
                "skip-me",
            ]
        }
        self.assertEqual(evaluate("sum_num(stages, 'bruto_aantalwoningen')", ctx), 5.0)
        self.assertEqual(
            evaluate("sum_num(stages, 'bruto_aantalwoningen')", {"stages": []}), 0.0
        )
        self.assertEqual(evaluate("sum_num(stages, null)", {"stages": _STAGES}), 0.0)

    def test_sum_num_if_filters_and_skips_bad_rows(self):
        stages = [
            {"plantype": "uitbreiding_uitleg", "bruto_aantalwoningen": 5},
            {"plantype": "inbreiding", "bruto_aantalwoningen": 7},
            {"plantype": "uitbreiding_uitleg", "bruto_aantalwoningen": "nope"},
            {"plantype": "uitbreiding_uitleg"},
        ]
        ctx = {"stages": stages}
        self.assertEqual(
            evaluate(
                "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'uitbreiding_uitleg')",
                ctx,
            ),
            5.0,
        )
        self.assertEqual(
            evaluate(
                "sum_num_if(stages, 'bruto_aantalwoningen', 'plantype', 'missing')",
                ctx,
            ),
            0.0,
        )

    def test_has_polygon_geometry_edge_cases(self):
        self.assertTrue(evaluate_bool("has_polygon_geometry(geo)", {"geo": _GEO_POLYGON}))
        self.assertTrue(
            evaluate_bool(
                "has_polygon_geometry(geo)",
                {
                    "geo": [
                        {
                            "geometry": {
                                "type": "MultiPolygon",
                                "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 0]]]],
                            }
                        }
                    ]
                },
            )
        )
        self.assertFalse(
            evaluate_bool(
                "has_polygon_geometry(geo)",
                {"geo": [{"geometry": {"type": "Point", "coordinates": [1, 2]}}]},
            )
        )
        self.assertFalse(
            evaluate_bool(
                "has_polygon_geometry(geo)",
                {"geo": [{"geometry": {"type": "Polygon", "coordinates": []}}]},
            )
        )
        self.assertFalse(evaluate_bool("has_polygon_geometry(geo)", {"geo": []}))
        self.assertFalse(evaluate_bool("has_polygon_geometry(geo)", {"geo": None}))

    def test_unknown_helper_raises(self):
        with self.assertRaises(ExpressionError) as ctx:
            evaluate("not_a_real_helper(1)", {})
        self.assertIn("Unknown helper", str(ctx.exception))

    def test_ast_cache_reuses_compiled_tree(self):
        expr = "sum_num(stages, 'bruto_aantalwoningen') == 15"
        ctx = {"stages": _STAGES}
        self.assertNotIn(expr, _AST_CACHE)
        self.assertTrue(evaluate_bool(expr, ctx))
        self.assertIn(expr, _AST_CACHE)
        cached = _AST_CACHE[expr]
        self.assertTrue(evaluate_bool(expr, ctx))
        self.assertIs(_AST_CACHE[expr], cached)

    def test_clear_expression_cache(self):
        expr = "1 + 1"
        evaluate(expr, {})
        self.assertIn(expr, _AST_CACHE)
        clear_expression_cache()
        self.assertNotIn(expr, _AST_CACHE)


if __name__ == "__main__":
    unittest.main()
