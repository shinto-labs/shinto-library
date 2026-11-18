"""Unit tests for QC gate evaluation."""

import unittest

from shinto.qc.gates import evaluate_gates, evaluate_qc_project, resolve_gate_action


class TestQcGates(unittest.TestCase):
    def test_block_if_introduced_only_blocks_new_failures(self):
        self.assertEqual(
            resolve_gate_action(
                mode="update",
                gates={"onUpdate": "block_if_introduced"},
                check_id="data_missing_name",
                previous_failed=set(),
            ),
            "block",
        )
        self.assertEqual(
            resolve_gate_action(
                mode="update",
                gates={"onUpdate": "block_if_introduced"},
                check_id="data_missing_name",
                previous_failed={"data_missing_name"},
            ),
            "report",
        )

    def test_evaluate_gates_groups_actions(self):
        pack = {
            "rules": [
                {
                    "id": "data_hard_plan_not_vertrouwelijk",
                    "checkCode": "D40",
                    "name": "Harde plannen mogen niet vertrouwelijk zijn",
                    "gates": {
                        "onCreate": "block",
                        "onUpdate": "block_if_introduced",
                        "onLegacy": "report",
                    },
                    "onFail": {
                        "message": "Harde planologische status mag niet vertrouwelijk zijn",
                        "fields": ["planologische_status", "vertrouwelijk"],
                    },
                },
                {
                    "id": "data_start_before_end",
                    "checkCode": "D35",
                    "name": "Start project vóór einde",
                    "gates": {"onCreate": "warn", "onUpdate": "warn", "onLegacy": "report"},
                    "onFail": {"message": "Start vóór einde", "fields": ["startjaar"]},
                },
            ]
        }
        qc = {
            "failedCheckIds": [
                "data_hard_plan_not_vertrouwelijk",
                "data_start_before_end",
            ],
            "detailIssues": [],
        }
        result = evaluate_gates(qc, pack, mode="create")
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["blocking"]), 1)
        self.assertEqual(result["blocking"][0]["checkCode"], "D40")
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0]["checkCode"], "D35")

    def test_unknown_mode_raises(self):
        for mode in ("save", "Create"):
            with self.assertRaises(ValueError):
                resolve_gate_action(
                    mode=mode,
                    gates={"onCreate": "block"},
                    check_id="data_missing_name",
                    previous_failed=set(),
                )
        with self.assertRaises(ValueError):
            evaluate_gates(
                {"failedCheckIds": ["data_missing_name"]},
                {"rules": []},
                mode="save",
            )

    def test_unknown_action_blocks(self):
        pack = {
            "rules": [
                {
                    "id": "data_missing_name",
                    "checkCode": "D01",
                    "gates": {"onCreate": "blok"},
                }
            ]
        }
        result = evaluate_gates(
            {"failedCheckIds": ["data_missing_name"], "detailIssues": []},
            pack,
            mode="create",
        )
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["blocking"]), 1)
        self.assertEqual(result["blocking"][0]["action"], "block")

    def test_block_if_introduced_on_create(self):
        for mode, gate_key in (("create", "onCreate"), ("legacy", "onLegacy")):
            self.assertEqual(
                resolve_gate_action(
                    mode=mode,
                    gates={gate_key: "block_if_introduced"},
                    check_id="data_missing_name",
                    previous_failed=set(),
                ),
                "block",
            )
            self.assertEqual(
                resolve_gate_action(
                    mode=mode,
                    gates={gate_key: "block_if_introduced"},
                    check_id="data_missing_name",
                    previous_failed={"data_missing_name"},
                ),
                "report",
            )

    def test_missing_gates_defaults_to_report(self):
        pack = {"rules": [{"id": "data_missing_name", "checkCode": "D01"}]}
        result = evaluate_gates(
            {"failedCheckIds": ["data_missing_name"]},
            pack,
            mode="create",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["blocking"], [])
        self.assertEqual(len(result["reports"]), 1)
        self.assertEqual(result["reports"][0]["action"], "report")


class TestEvaluateQcProject(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_mode_raises_before_run(self):
        with self.assertRaises(ValueError):
            await evaluate_qc_project(
                {"id": "draft", "data": {}},
                None,
                {"version": "t", "rules": []},
                mode="save",
            )


if __name__ == "__main__":
    unittest.main()
