"""Cycle-3 freeze and public-input checks; no inference in these tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from evaluation.run_system2_cycle import MANIFEST, PROTOCOL, checked_cases, run_cycle


class Cycle3Test(unittest.TestCase):
    def test_manifest_points_to_frozen_cycle_protocol(self) -> None:
        import json

        self.assertEqual(PROTOCOL.name, "PROTOCOL.md")
        self.assertEqual(
            json.loads(MANIFEST.read_text())["protocol"], "evaluation/cycle3/PROTOCOL.md"
        )

    def test_manifest_has_exposed_development_and_two_fresh_assets(self) -> None:
        cases = checked_cases()
        self.assertEqual(len(cases), 7)
        self.assertEqual(
            [row["case_id"] for row, _ in cases[-2:]],
            ["PreDist-M1-fault-37", "PreDist-M1-fault-5"],
        )
        self.assertEqual(
            {replay["asset"]["substation_id"] for _, replay in cases[-2:]},
            {"19", "11"},
        )

    def test_wrong_protocol_hash_prevents_provider_calls(self) -> None:
        with (
            patch("evaluation.run_system2_cycle.run_system2") as domain,
            patch("evaluation.run_system2_cycle.run_public_bundle") as general,
            self.assertRaisesRegex(ValueError, "protocol SHA-256"),
        ):
            run_cycle(expected_protocol_sha256="0" * 64)
        domain.assert_not_called()
        general.assert_not_called()


if __name__ == "__main__":
    unittest.main()
