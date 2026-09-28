"""Protect the retrospective replay from leaking its outcome to the agent."""

from __future__ import annotations

import datetime as dt
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReplayBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.replay_text = (ROOT / "data/replay-52.json").read_text()
        self.replay = json.loads(self.replay_text)
        self.held_out = json.loads((ROOT / "evaluation/held-out-52.json").read_text())

    def test_all_visible_records_precede_report(self) -> None:
        decision = dt.datetime.fromisoformat(self.replay["decision_time"])
        for row in self.replay["measurement_window"]["rows"]:
            self.assertLessEqual(dt.datetime.fromisoformat(row["timestamp"]), decision)
        for row in self.replay["prior_faults"]:
            self.assertLess(dt.datetime.fromisoformat(row["report_date"]), decision)
        for row in self.replay["prior_disturbances"]:
            self.assertLess(dt.datetime.fromisoformat(row["event_start"]), decision)

    def test_current_diagnosis_is_held_out(self) -> None:
        self.assertEqual(self.replay["current_report"]["problem"], "no heat")
        self.assertNotIn(self.held_out["event_description"], self.replay_text)
        self.assertNotIn(self.held_out["fault_label"], self.replay_text)


if __name__ == "__main__":
    unittest.main()
