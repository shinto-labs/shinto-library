"""Unit tests for QC gate evaluation."""

import unittest

from shinto.qc.gates import evaluate_gates, resolve_gate_action


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


if __name__ == "__main__":
    unittest.main()
