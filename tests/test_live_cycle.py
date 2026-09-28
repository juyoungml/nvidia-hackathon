"""Frozen cycle manifest and no-overwrite preflight."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.run_live_cycle import MANIFEST, checked_cases, run_cycle


class LiveCycleTest(unittest.TestCase):
    def test_checked_cases_match_four_frozen_inputs_and_live_corpus(self) -> None:
        rows = checked_cases()
        self.assertEqual(
            [row["case_id"] for row, _, _ in rows],
            [
                "PreDist-M1-fault-52",
                "PreDist-M1-fault-3",
                "PreDist-M1-fault-29",
                "PreDist-M1-fault-47",
            ],
        )
        for row, replay, bundle in rows:
            self.assertEqual(row["case_id"], replay["case_id"])
            self.assertEqual(row["public_corpus_sha256"], bundle["corpus_sha256"])

    def test_manifest_hash_change_is_rejected_before_inference(self) -> None:
        data = json.loads(MANIFEST.read_text())
        data["cases"][0]["plan_schema_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "plan schema mismatch"):
                checked_cases(path)

    def test_existing_trace_refused_before_key_or_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "traces"
            output.mkdir()
            (output / "domain-52.json").write_text("original")
            with (
                patch("evaluation.run_live_cycle.sha256", return_value="frozen"),
                patch("evaluation.run_live_cycle.checked_cases", return_value=[]),
                patch("evaluation.run_live_cycle.load_key") as key,
                patch("evaluation.run_live_cycle.run_live_case") as model,
                self.assertRaisesRegex(ValueError, "already contains results"),
            ):
                run_cycle(expected_protocol_sha256="frozen", output_dir=output)
            key.assert_not_called()
            model.assert_not_called()
            self.assertEqual((output / "domain-52.json").read_text(), "original")


if __name__ == "__main__":
    unittest.main()
