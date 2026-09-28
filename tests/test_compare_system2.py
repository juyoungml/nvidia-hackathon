"""Offline comparison guards for the shared v2 display contract."""

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.compare_system2 import compare_pairs


def _trace(*, domain: bool, corpus: str = "same", withheld: bool = False) -> dict:
    trace = {
        "case_id": "case-1",
        "corpus_sha256": corpus,
        "contract_version": 2,
        "validation": {
            "status": "invalid" if withheld else "valid",
            "selection": {"next_checks": [{"id": "C-sensor", "because_fact_ids": ["F-1"]}]},
        },
        "display": {
            "status": "withheld" if withheld else "reference_checked",
            "observations": [{"id": "F-1", "text": "Measured value", "source_id": "source-1"}],
            "limits": [],
            "suggested_next_checks": [
                {
                    "id": "C-sensor",
                    "text": "Check sensor",
                    "because_facts": [{"id": "F-1"}],
                    "model_authored_suggestion_rationale": "Based on F-1",
                }
            ],
        },
        "tool_calls": [],
    }
    trace.update(
        {"method": "system2-tools", "wall_seconds": 2.0}
        if domain
        else {"mode": "file_agent", "latency_seconds": 3.0}
    )
    return trace


def _paths(tmp_path, domain: dict, general: dict):
    d, g = tmp_path / "d.json", tmp_path / "g.json"
    d.write_text(json.dumps(domain))
    g.write_text(json.dumps(general))
    return [(d, g)]


class ComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def test_mismatched_corpus_rejected(self) -> None:
        pairs = _paths(self.path, _trace(domain=True), _trace(domain=False, corpus="other"))
        with self.assertRaisesRegex(ValueError, "corpus_sha256"):
            compare_pairs(pairs)

    def test_withheld_is_not_reference_checked_success(self) -> None:
        pairs = _paths(self.path, _trace(domain=True, withheld=True), _trace(domain=False))
        summary, blind, _ = compare_pairs(pairs)
        domain = summary["pairs"][0]["domain"]
        self.assertTrue(domain["withheld"])
        self.assertFalse(domain["reference_checked"])
        self.assertIsNone(domain["canonical_observation_source_count"])
        self.assertIn("Response withheld", blind)

    def test_missing_usage_remains_null(self) -> None:
        pairs = _paths(self.path, _trace(domain=True), _trace(domain=False))
        summary, _, _ = compare_pairs(pairs)
        self.assertIsNone(summary["pairs"][0]["domain"]["usage"])
        self.assertIsNone(summary["pairs"][0]["general"]["usage"])

    def test_blind_review_excludes_provider_and_source_filename(self) -> None:
        domain = _trace(domain=True)
        domain["display"]["suggested_next_checks"][0]["model_authored_suggestion_rationale"] = (
            "Claude checked tools/get_recent_measurements.json"
        )
        pairs = _paths(self.path, domain, _trace(domain=False))
        _, blind, key = compare_pairs(pairs, seed=7)
        self.assertNotIn("Claude", blind)
        self.assertNotIn("get_recent_measurements.json", blind)
        self.assertEqual(
            {key["pairs"][0][side]["arm"] for side in ("A", "B")}, {"domain", "general"}
        )
