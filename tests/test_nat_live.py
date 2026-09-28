"""Exercise the registered NAT live reader functions without model inference."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from poc.live_investigation import _read_tool

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("nat"), "NAT optional environment unavailable")
class NatLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from integrations.live_nat_adapter import NatLiveReader

        cls.replay = json.loads((ROOT / "data/replay-52.json").read_text())
        cls.reader = NatLiveReader()

    def test_all_six_readers_match_direct_results_and_facts(self) -> None:
        rows = self.replay["measurement_window"]["rows"]
        calls = [
            ("get_recent_measurements", {}),
            ("get_prior_incidents", {}),
            ("get_maintenance_timeline", {}),
            ("get_signal_definitions", {}),
            ("get_temporal_episodes", {}),
            (
                "query_measurement_window",
                {"start": rows[0]["timestamp"], "end": rows[2]["timestamp"]},
            ),
        ]
        for name, arguments in calls:
            with self.subTest(name=name):
                self.assertEqual(
                    self.reader.read(self.replay, name, arguments, True),
                    _read_tool(self.replay, name, arguments, True),
                )

    def test_nat_rejects_post_decision_and_extra_arguments(self) -> None:
        with self.assertLogs(level="ERROR"), self.assertRaisesRegex(ValueError, "cutoff"):
            self.reader.read(
                self.replay,
                "query_measurement_window",
                {"start": "2000-01-01", "end": "2099-01-01"},
                True,
            )
        with self.assertLogs(level="ERROR"), self.assertRaisesRegex(ValueError, "empty arguments"):
            self.reader.read(self.replay, "get_recent_measurements", {"extra": 1}, True)


if __name__ == "__main__":
    unittest.main()
