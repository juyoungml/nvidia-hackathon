"""Check structured routing and trace boundaries without hosted API calls."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from poc.run import (
    NANO_MODEL,
    REPLAY,
    nano_gate,
    run,
    run_case,
    save_trace,
    unsupported_certainty_markers,
    validate_gate,
)


class RuntimeTests(unittest.TestCase):
    def test_gate_accepts_only_known_evidence_kinds_and_consistent_decision(self) -> None:
        valid = '{"escalate":true,"priority":"review","reason":"No heat report","evidence_kinds":["customer_report"]}'
        self.assertTrue(validate_gate(valid)["escalate"])
        with self.assertRaises(ValueError):
            validate_gate(valid.replace('customer_report"]', 'invented"]'))
        with self.assertRaises(ValueError):
            validate_gate(valid.replace('"review"', '"routine"'))

    @patch("poc.run.call_model")
    def test_nano_receives_no_heldout_diagnosis_and_falls_back(self, call_model) -> None:
        call_model.return_value = ({"message": {"content": "bad format"}}, 0.1)
        gate = nano_gate(REPLAY, "test-key")
        self.assertEqual(gate["model"], NANO_MODEL)
        self.assertTrue(gate["decision"]["escalate"])
        self.assertTrue(gate["validation_status"].startswith("fallback:"))
        user_input = call_model.call_args.args[0][1]["content"]
        self.assertNotIn("fault_label", user_input)
        self.assertNotIn("remedy", user_input)
        self.assertNotIn("prior_faults", user_input)

    @patch("poc.run.call_model")
    def test_undefined_tag_is_repaired_before_final(self, call_model) -> None:
        call_model.side_effect = [
            (
                {
                    "message": {
                        "content": "Check s_hc1_flow and source PreDist-M1-fault-52-problem-only."
                    }
                },
                1.0,
            ),
            ({"message": {"content": "현장 엔지니어가 고객측 유량을 별도 확인하십시오."}}, 0.5),
        ]
        trace = run_case(REPLAY, key="test-key")
        self.assertEqual(trace["undefined_signal_names"], [])
        self.assertIn("고객측 유량", trace["final"])
        self.assertEqual(
            trace["events"][-1]["output_repair"]["original_invalid_tags"], ["s_hc1_flow"]
        )

    def test_confident_component_claim_is_detected(self) -> None:
        self.assertEqual(unsupported_certainty_markers("밸브 고장 가능성 높음"), ["가능성 높음"])

    @patch("poc.run.nano_gate")
    def test_no_escalation_makes_no_ultra_call(self, nano_gate_mock) -> None:
        nano_gate_mock.return_value = {
            "decision": {"escalate": False, "priority": "routine"},
            "effective_decision": {"escalate": False, "priority": "routine"},
        }
        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / "case.json"
            replay.write_text(json.dumps(REPLAY))
            with patch("poc.run.run_case") as ultra_mock:
                trace = run(replay, key="test-key")
            ultra_mock.assert_not_called()
        self.assertIsNone(trace["final"])
        self.assertEqual(trace["events"], [])

    def test_trace_names_are_unique_and_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = save_trace({"case_id": "one/two", "final": "a"}, directory)
            second = save_trace({"case_id": "one/two", "final": "b"}, directory)
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first.read_text())["final"], "a")
            self.assertEqual(json.loads(second.read_text())["final"], "b")


if __name__ == "__main__":
    unittest.main()
