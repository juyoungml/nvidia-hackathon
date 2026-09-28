"""Bounds and provenance checks for public temporal readers."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from poc.temporal_tools import (
    MAX_WINDOW_ROWS,
    permitted_window_fields,
    query_window,
    temporal_episodes,
    temporal_facts,
    validate_public_replay,
    window_facts,
)

ROOT = Path(__file__).resolve().parents[1]


class TemporalToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay = json.loads((ROOT / "data/replay-52.json").read_text())

    def test_window_rejects_cutoff_and_oversize(self) -> None:
        replay = self.replay
        with self.assertRaisesRegex(ValueError, "cutoff"):
            query_window(replay, start=replay["measurement_window"]["start"], end="2099-01-01")
        with self.assertRaisesRegex(ValueError, str(MAX_WINDOW_ROWS)):
            query_window(
                replay,
                start=replay["measurement_window"]["start"],
                end=replay["measurement_window"]["end"],
            )
        with self.assertRaisesRegex(ValueError, "ISO"):
            query_window(replay, start="not-a-date", end=replay["measurement_window"]["end"])

    def test_public_replay_rejects_later_source_records(self) -> None:
        for field, value in (
            ("measurement", {"timestamp": "2099-01-01"}),
            ("prior_fault", {"report_date": "2099-01-01"}),
            ("prior_disturbance", {"event_start": "2099-01-01"}),
        ):
            replay = copy.deepcopy(self.replay)
            if field == "measurement":
                replay["measurement_window"]["rows"].append(value)
            elif field == "prior_fault":
                replay["prior_faults"].append(value)
            else:
                replay["prior_disturbances"].append(value)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "decision|window"):
                validate_public_replay(replay)

    def test_query_facts_are_subset_of_full_public_window(self) -> None:
        full = permitted_window_fields(self.replay)
        first = full["rows"][0]["timestamp"]
        third = full["rows"][2]["timestamp"]
        part = query_window(self.replay, start=first, end=third)
        self.assertEqual(part["row_count"], 3)
        full_facts = {fact["id"] for fact in window_facts(full)}
        part_facts = window_facts(part)
        self.assertTrue({fact["id"] for fact in part_facts} <= full_facts)
        for fact in part_facts:
            self.assertEqual(fact["source_id"], full["source_id"])
            self.assertIn("supply_c", fact["value"]["sample"])
            self.assertIn("setpoint_c", fact["value"]["sample"])

    def test_episode_composites_preserve_endpoint_values(self) -> None:
        episodes = temporal_episodes(self.replay)
        facts = temporal_facts(self.replay, episodes)
        self.assertTrue(facts)
        for fact in facts:
            self.assertEqual(fact["source_id"], episodes["source_id"])
            self.assertNotIn("fault", fact["text"].lower())
            self.assertNotIn("cause", fact["text"].lower())
            if ".episode." in fact["source_field"]:
                value = fact["value"]
                self.assertIn("timestamp", value["first"])
                self.assertIn("timestamp", value["last"])
                self.assertIn("timestamp", value["peak"])


if __name__ == "__main__":
    unittest.main()
