"""Continuity, cutoff, and provenance checks for replay timing evidence."""

from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from poc.temporal_evidence import build_temporal_evidence

ROOT = Path(__file__).resolve().parents[1]


def replay(gaps: list[float | None], *, timestamps: list[str] | None = None) -> dict:
    times = timestamps or [f"2020-01-01 00:{i * 10:02d}:00" for i in range(len(gaps))]
    return {
        "case_id": "synthetic",
        "decision_time": "2020-01-01 01:00:00",
        "asset": {"substation_id": "12"},
        "measurement_window": {
            "start": "2020-01-01 00:00:00",
            "end": "2020-01-01 01:00:00",
            "source_id": "synthetic-operational-data",
            "rows": [
                {
                    "timestamp": time,
                    "s_hc1_supply_temperature": 50 + gap if gap is not None else None,
                    "s_hc1_supply_temperature_setpoint": 50,
                }
                for time, gap in zip(times, gaps, strict=True)
            ],
        },
        "provenance": {"source_files_sha256": {"substation_12.csv": "abc"}},
        "source": {"dataset": "synthetic"},
    }


class TemporalEvidenceTests(unittest.TestCase):
    def test_single_outlier_and_matched_peak(self) -> None:
        result = build_temporal_evidence(replay([0.5, 2.5, 1.0]))
        self.assertEqual(result["episode_count"], 1)
        episode = result["episodes"][0]
        self.assertEqual(episode["sample_count"], 1)
        self.assertEqual(episode["first"]["timestamp"], "2020-01-01 00:10:00")
        self.assertEqual(episode["peak"]["supply_c"], 52.5)
        self.assertEqual(episode["peak"]["setpoint_c"], 50)
        self.assertEqual(result["paired_series"]["peak_gap"], episode["peak"])
        self.assertEqual(result["provenance"]["operational_csv_sha256"], "abc")

    def test_adjacent_and_separated_episodes(self) -> None:
        result = build_temporal_evidence(replay([2, 2.5, 3, 2, 4]))
        self.assertEqual(result["episode_count"], 2)
        self.assertEqual([item["sample_count"] for item in result["episodes"]], [2, 1])
        self.assertEqual(result["episodes"][0]["last"]["timestamp"], "2020-01-01 00:20:00")
        self.assertEqual(result["episodes"][1]["first"]["timestamp"], "2020-01-01 00:40:00")
        self.assertEqual(result["counts"]["above_threshold_samples"], 3)

    def test_missing_nonfinite_and_invalid_time_break_continuity(self) -> None:
        case = replay(
            [3, None, 4, math.inf, 5, 6],
            timestamps=[
                "2020-01-01 00:00:00",
                "2020-01-01 00:10:00",
                "2020-01-01 00:20:00",
                "2020-01-01 00:30:00",
                "bad time",
                "2020-01-01 00:50:00",
            ],
        )
        result = build_temporal_evidence(case)
        self.assertEqual(result["episode_count"], 3)
        self.assertEqual(result["counts"]["missing_or_nonfinite_pair"], 2)
        self.assertEqual(result["counts"]["invalid_timestamp"], 1)
        self.assertEqual(result["counts"]["valid_paired_samples"], 3)

    def test_irregular_and_duplicate_times_break_continuity(self) -> None:
        result = build_temporal_evidence(
            replay(
                [3, 4, 5, 6],
                timestamps=[
                    "2020-01-01 00:00:00",
                    "2020-01-01 00:20:00",
                    "2020-01-01 00:20:00",
                    "2020-01-01 00:30:00",
                ],
            )
        )
        self.assertEqual(result["episode_count"], 3)
        self.assertEqual(result["counts"]["irregular_intervals"], 2)
        self.assertEqual([item["sample_count"] for item in result["episodes"]], [1, 1, 2])

    def test_decision_cutoff_and_window_selection(self) -> None:
        case = replay([3, 4, 5, 6])
        case["decision_time"] = "2020-01-01 00:20:00"
        result = build_temporal_evidence(case, window_start="2020-01-01 00:10:00")
        self.assertEqual(result["counts"]["valid_paired_samples"], 2)
        self.assertEqual(result["counts"]["outside_selected_window_or_after_cutoff"], 2)
        self.assertEqual(result["episodes"][0]["first"]["timestamp"], "2020-01-01 00:10:00")
        self.assertEqual(result["episodes"][0]["last"]["timestamp"], "2020-01-01 00:20:00")
        with self.assertRaises(ValueError):
            build_temporal_evidence(case, window_start="2019-12-31 23:50:00")

    def test_bounded_output_retains_largest_episode_and_reports_omission(self) -> None:
        result = build_temporal_evidence(replay([3, 0, 5, 0, 4]), max_episodes=1)
        self.assertEqual(result["episode_count"], 3)
        self.assertEqual(result["episodes_returned"], 1)
        self.assertTrue(result["episodes_truncated"])
        self.assertEqual(result["episodes"][0]["peak"]["timestamp"], "2020-01-01 00:20:00")

    def test_public_inputs_only_and_no_mutation(self) -> None:
        for path in sorted((ROOT / "data").glob("*.json")):
            original = json.loads(path.read_text())
            before = copy.deepcopy(original)
            result = build_temporal_evidence(original)
            self.assertEqual(original, before)
            self.assertEqual(result["case_id"], original["case_id"])
            self.assertEqual(
                result["counts"]["source_rows"], len(original["measurement_window"]["rows"])
            )
            self.assertEqual(result["source_id"], original["measurement_window"]["source_id"])
            self.assertNotIn("fault_label", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
