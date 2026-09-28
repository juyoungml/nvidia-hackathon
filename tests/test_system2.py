"""Grounding contract tests: source existence and semantic value are separate checks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from poc.evidence_contract import (
    audit_completeness,
    build_case_bundle,
    build_evidence,
    render_selection,
    validate_selection,
)
from poc.run import run_tool
from poc.system2 import parse_args, run_system2

ROOT = Path(__file__).resolve().parents[1]


def replay52() -> dict:
    return json.loads((ROOT / "data/replay-52.json").read_text())


class EvidenceContractTests(unittest.TestCase):
    def test_cli_defaults_to_v2_and_keeps_explicit_v1(self) -> None:
        self.assertEqual(parse_args(["--replay", "case.json"]).contract_version, 2)
        self.assertEqual(
            parse_args(["--replay", "case.json", "--contract-version", "1"]).contract_version,
            1,
        )

    def test_selected_fact_renders_exact_tool_value_and_source(self) -> None:
        replay = replay52()
        evidence = build_evidence(
            replay, {"get_recent_measurements": run_tool("get_recent_measurements", replay)}
        )
        fact = next(
            item
            for item in evidence["facts"]
            if item["source_field"] == "signals.s_hc1_supply_temperature.mean"
        )
        raw = json.dumps(
            {
                "observed_fact_ids": [fact["id"]],
                "limit_ids": [],
                "next_checks": [
                    {
                        "id": "C-room-impact",
                        "because_fact_ids": [fact["id"]],
                        "rationale": "Confirm whether measured supply corresponds to room heat.",
                    }
                ],
            }
        )
        rendered = render_selection(validate_selection(raw, evidence), evidence)
        self.assertEqual(rendered["observations"], [fact])
        self.assertEqual(rendered["suggested_next_checks"][0]["because_facts"], [fact])

    def test_existing_source_does_not_validate_invented_value(self) -> None:
        evidence = build_evidence(replay52())
        source = evidence["sources"][0]["id"]
        bad = json.dumps(
            {"observed_fact_ids": [source + ":999"], "limit_ids": [], "next_checks": []}
        )
        with self.assertRaisesRegex(ValueError, "unavailable observed_fact_ids"):
            validate_selection(bad, evidence)

    def test_unknown_fact_reference_in_check_fails(self) -> None:
        evidence = build_evidence(replay52())
        raw = json.dumps(
            {
                "observed_fact_ids": [],
                "limit_ids": [],
                "next_checks": [
                    {
                        "id": "C-more-data",
                        "because_fact_ids": ["F-missing"],
                        "rationale": "Need observations.",
                    }
                ],
            }
        )
        with self.assertRaisesRegex(ValueError, "supporting fact"):
            validate_selection(raw, evidence)

    def test_extra_model_authored_observation_fails(self) -> None:
        evidence = build_evidence(replay52())
        raw = json.dumps(
            {
                "observed_fact_ids": [],
                "limit_ids": [],
                "next_checks": [],
                "observation": "Sensor was 999 C",
            }
        )
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            validate_selection(raw, evidence)

    def test_missing_measurements_cannot_select_numeric_fact(self) -> None:
        replay = replay52()
        replay["measurement_window"]["rows"] = []
        evidence = build_evidence(
            replay, {"get_recent_measurements": run_tool("get_recent_measurements", replay)}
        )
        self.assertTrue(
            any(f["source_field"] == "samples" and f["value"] == 0 for f in evidence["facts"])
        )
        self.assertFalse(any(f["source_field"].startswith("signals.") for f in evidence["facts"]))

    def test_bundle_is_stable_and_omits_current_diagnosis(self) -> None:
        replay = replay52()
        first = build_case_bundle(replay)
        second = build_case_bundle(replay)
        self.assertEqual(first["corpus_sha256"], second["corpus_sha256"])
        self.assertNotIn("event_description", first["files"]["case.json"])
        self.assertIn("fact_catalog.json", first["files"])
        self.assertTrue(
            any(f["source_field"] == "event_description" for f in first["evidence"]["facts"])
        )

    def test_v2_bundle_exposes_full_constraints_and_source_manifest(self) -> None:
        bundle = build_case_bundle(replay52(), contract_version=2)
        schema = bundle["schema"]
        self.assertEqual(schema["properties"]["observed_fact_ids"]["maxItems"], 12)
        self.assertEqual(schema["properties"]["next_checks"]["minItems"], 2)
        self.assertIn("source_manifest.json", bundle["files"])
        self.assertIn("measurement", bundle["task"])

    def test_v2_accepts_single_outer_fence_and_marks_incomplete_unread_sources(self) -> None:
        evidence = build_evidence(replay52())
        report_id = evidence["facts"][0]["id"]
        selection = {
            "observed_fact_ids": [report_id],
            "limit_ids": [],
            "next_checks": [
                {
                    "id": "C-room-impact",
                    "because_fact_ids": [report_id],
                    "rationale": "Check affected spaces.",
                },
                {
                    "id": "C-more-data",
                    "because_fact_ids": [report_id],
                    "rationale": "Measurements are missing.",
                },
            ],
        }
        raw = "```json\n" + json.dumps(selection) + "\n```"
        checked = validate_selection(raw, evidence, contract_version=2)
        self.assertEqual(checked, selection)
        self.assertEqual(
            render_selection(checked, evidence, contract_version=2)["status"], "reference_checked"
        )
        completeness = audit_completeness(checked, read_names=set())
        self.assertEqual(completeness["status"], "incomplete")
        self.assertIn("no_case_evidence_source_read", completeness["issues"])
        self.assertEqual(
            audit_completeness(checked, read_names={"fact_catalog"})["status"], "checked"
        )

    def test_v2_rejects_missing_check_and_support_outside_selected_facts(self) -> None:
        evidence = build_evidence(replay52())
        report_id = evidence["facts"][0]["id"]
        raw = json.dumps(
            {
                "observed_fact_ids": [report_id],
                "limit_ids": [],
                "next_checks": [
                    {
                        "id": "C-room-impact",
                        "because_fact_ids": [report_id],
                        "rationale": "Check rooms.",
                    }
                ],
            }
        )
        with self.assertRaisesRegex(ValueError, "next_checks"):
            validate_selection(raw, evidence, contract_version=2)

    @patch("poc.system2.call_model")
    def test_v2_runner_keeps_reference_and_completeness_separate(self, model) -> None:
        report_id = build_evidence(replay52())["facts"][0]["id"]
        model.return_value = (
            {
                "message": {
                    "content": json.dumps(
                        {
                            "observed_fact_ids": [report_id],
                            "limit_ids": [],
                            "next_checks": [
                                {
                                    "id": "C-room-impact",
                                    "because_fact_ids": [report_id],
                                    "rationale": "Check rooms.",
                                },
                                {
                                    "id": "C-more-data",
                                    "because_fact_ids": [report_id],
                                    "rationale": "Measurements are missing.",
                                },
                            ],
                        }
                    )
                }
            },
            0.1,
        )
        trace = run_system2(replay52(), mode="tools", key="fake", contract_version=2)
        self.assertEqual(trace["validation"]["status"], "valid")
        self.assertEqual(trace["display"]["status"], "withheld")
        self.assertEqual(trace["completeness"]["status"], "incomplete")

    @patch("poc.system2.call_model")
    def test_invalid_model_output_is_withheld_and_raw_preserved(self, model) -> None:
        model.return_value = (
            {
                "message": {
                    "content": json.dumps(
                        {"observed_fact_ids": ["F-invented"], "limit_ids": [], "next_checks": []}
                    )
                }
            },
            0.1,
        )
        trace = run_system2(replay52(), mode="packet", key="fake")
        self.assertEqual(trace["display"]["status"], "withheld")
        self.assertIn("F-invented", trace["raw_output"])
        self.assertEqual(trace["validation"]["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
