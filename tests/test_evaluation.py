"""Boundary and audit checks for the public replay comparison."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from evaluation.evaluate import baseline, check_cutoff, score

ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def test_public_cases_keep_outcomes_held_out_and_observations_before_cutoff(self) -> None:
        for case in ("52", "62", "32"):
            with self.subTest(case=case):
                replay_text = (ROOT / f"data/replay-{case}.json").read_text()
                replay = json.loads(replay_text)
                outcome = json.loads((ROOT / f"evaluation/held-out-{case}.json").read_text())
                check_cutoff(replay)
                self.assertEqual(len(replay["measurement_window"]["rows"]), 144)
                self.assertNotIn(outcome["event_description"], replay_text)
                self.assertNotIn(outcome["fault_label"], replay_text)
                self.assertEqual(replay["case_id"], outcome["case_id"])
                self.assertEqual(len(replay["provenance"]["source_files_sha256"]), 4)

    def test_future_record_rejected(self) -> None:
        replay = json.loads((ROOT / "data/replay-62.json").read_text())
        replay["prior_faults"][0]["report_date"] = replay["decision_time"]
        with self.assertRaisesRegex(ValueError, "crosses cutoff"):
            check_cutoff(replay)

    def test_baseline_uses_valid_citations_and_no_outcome(self) -> None:
        replay = json.loads((ROOT / "data/replay-32.json").read_text())
        report = baseline(replay)
        audit = score(replay, report)
        self.assertTrue(audit["has_any_citation"])
        self.assertEqual(audit["invalid_citation_ids"], [])
        self.assertEqual(audit["undefined_signal_names"], [])
        self.assertTrue(audit["uncertainty_stated"])

    def test_derived_probes_are_labeled_and_separate(self) -> None:
        for name, expected_rows in (("no-report-20161210", 144), ("missing-measurements-52", 0)):
            with self.subTest(name=name):
                replay = json.loads((ROOT / f"data/derived-{name}.json").read_text())
                check_cutoff(replay)
                self.assertFalse(replay["derived_case"]["published_incident"])
                self.assertEqual(len(replay["measurement_window"]["rows"]), expected_rows)
                self.assertEqual(score(replay, baseline(replay))["case_kind"], "derived_probe")

    def test_flags_unknown_citation_and_undefined_signal(self) -> None:
        replay = json.loads((ROOT / "data/replay-52.json").read_text())
        report = deepcopy(baseline(replay))
        report["final"] += "\nCheck s_hc1_flow [PreDist-M1-fault-999]."
        audit = score(replay, report)
        self.assertEqual(audit["invalid_citation_ids"], ["PreDist-M1-fault-999"])
        self.assertEqual(audit["undefined_signal_names"], ["s_hc1_flow"])

    def test_saved_legacy_trace_exposes_known_undefined_tags(self) -> None:
        replay = json.loads((ROOT / "data/replay-52.json").read_text())
        trace = json.loads(
            (ROOT / "poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json").read_text()
        )
        audit = score(replay, trace)
        self.assertEqual(audit["invalid_citation_ids"], [])
        self.assertEqual(audit["undefined_signal_names"], ["s_hc1_flow", "s_hc1_valve_position"])


if __name__ == "__main__":
    unittest.main()
