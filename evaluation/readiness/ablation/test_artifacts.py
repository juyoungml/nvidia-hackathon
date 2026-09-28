"""Provenance and frozen-denominator checks for offline review artifacts."""

from __future__ import annotations

import hashlib
import importlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
READINESS = ROOT / "evaluation/readiness"


def read(path: Path) -> dict:
    return json.loads(path.read_text())


class OfflineArtifactsTest(unittest.TestCase):
    def test_all_case_denominator_and_trace_hashes(self) -> None:
        result = read(READINESS / "ablation/results.json")
        rows = result["cycle4_all_cases"]
        self.assertEqual(len(rows), 8)
        self.assertEqual(
            {(r["case"], r["arm"]) for r in rows},
            {(c, a) for c in (52, 3, 29, 47) for a in ("domain", "general")},
        )
        self.assertEqual(
            result["cycle4_primary_success"],
            {"domain": {"valid": 2, "denominator": 4}, "general": {"valid": 4, "denominator": 4}},
        )
        for row in rows:
            path = ROOT / row["trace"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["trace_sha256"])
        self.assertEqual(
            {r["case"] for r in rows if r["arm"] == "domain" and not r["valid"]}, {52, 47}
        )

    def test_review_packets_preserve_exact_model_checks_and_citations(self) -> None:
        packets = read(READINESS / "content-review/PACKETS.json")["packets"]
        key = read(READINESS / "content-review/REVEAL_KEY.json")["labels"]
        self.assertEqual(len(packets), 4)
        for packet in packets:
            source = key[packet["label"]]
            trace = read(ROOT / source["trace"])
            self.assertEqual(packet["case"], source["case"])
            self.assertEqual(len(packet["checks"]), 3)
            facts = {fact["id"]: fact for fact in trace["display"]["observations"]}
            for exported, original in zip(
                packet["checks"], trace["parsed_plan"]["next_checks"], strict=True
            ):
                self.assertEqual(exported["id"], original["id"])
                self.assertEqual(exported["rationale"], original["rationale"])
                self.assertEqual(
                    exported["cited_facts"], [facts[fid] for fid in original["because_fact_ids"]]
                )

    def test_review_hash_is_sealed_before_reveal(self) -> None:
        reveal = importlib.import_module("evaluation.readiness.content-review.reveal")
        summary = reveal.build_summary()
        self.assertEqual(summary["paired_content_totals"]["domain"]["score"], 39)
        self.assertEqual(summary["paired_content_totals"]["general"]["score"], 39)
        with patch.object(reveal, "BLIND_REVIEW_SHA256_BEFORE_REVEAL", "0" * 64):
            with self.assertRaisesRegex(ValueError, "Blind review changed"):
                reveal.build_summary()

    def test_v2_packets_preserve_complete_displayed_checks(self) -> None:
        v2 = READINESS / "content-review/v2"
        packets = read(v2 / "PACKETS.json")["packets"]
        key = read(v2 / "REVEAL_KEY.json")["labels"]
        self.assertEqual(len(packets), 4)
        for packet in packets:
            source = key[packet["label"]]
            trace_path = ROOT / source["trace"]
            self.assertEqual(
                hashlib.sha256(trace_path.read_bytes()).hexdigest(), source["trace_sha256"]
            )
            display = read(trace_path)["display"]
            self.assertEqual(packet["displayed_limits"], display["limits"])
            for exported, original in zip(
                packet["checks"], display["suggested_next_checks"], strict=True
            ):
                self.assertEqual(exported["id"], original["id"])
                self.assertEqual(exported["canonical_check_text"], original["text"])
                self.assertEqual(
                    exported["model_rationale"], original["model_authored_suggestion_rationale"]
                )
                self.assertEqual(exported["cited_facts"], original["because_facts"])

    def test_v2_review_was_sealed_before_reveal(self) -> None:
        reveal = importlib.import_module("evaluation.readiness.content-review.v2.reveal")
        summary = reveal.build_summary()
        self.assertEqual(summary["paired_content_totals"]["domain"]["score"], 41)
        self.assertEqual(summary["paired_content_totals"]["general"]["score"], 42)
        with patch.object(reveal, "BLIND_REVIEW_SHA256_BEFORE_REVEAL", "0" * 64):
            with self.assertRaisesRegex(ValueError, "blind review changed"):
                reveal.build_summary()


if __name__ == "__main__":
    unittest.main()
