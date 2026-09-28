"""Deterministic checks for the separate development composer."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from poc.constrained_composer import (
    assemble_selection,
    plan_schema,
    stored_context,
    synthetic_context,
)
from poc.evidence_contract import finalize_selection, validate_selection


def plan(checks: list[dict], limits: list[str] | None = None) -> str:
    return json.dumps({"limit_ids": limits or [], "next_checks": checks})


def check(check_id: str, refs: list[str], rationale: str = "Check the source evidence.") -> dict:
    return {"id": check_id, "because_fact_ids": refs, "rationale": rationale}


class ComposerTests(unittest.TestCase):
    def test_ordered_union_is_only_source_of_observations(self) -> None:
        evidence, _, _ = synthetic_context()
        first, second, third = [fact["id"] for fact in evidence["facts"]]
        raw = plan(
            [
                check("C-room-impact", [second, first]),
                check("C-secondary-flow", [first, third]),
            ]
        )
        parsed, assembled = assemble_selection(raw, evidence)
        self.assertEqual(parsed["next_checks"][0]["because_fact_ids"], [second, first])
        self.assertEqual(assembled["observed_fact_ids"], [second, first, third])
        self.assertEqual(
            validate_selection(json.dumps(assembled), evidence, contract_version=2), assembled
        )

    def test_schema_constrains_fact_enum_check_count_and_rationale(self) -> None:
        evidence, _, _ = synthetic_context()
        schema = plan_schema(evidence)
        checks = schema["properties"]["next_checks"]
        refs = checks["items"]["properties"]["because_fact_ids"]
        self.assertEqual((checks["minItems"], checks["maxItems"]), (2, 3))
        self.assertEqual((refs["minItems"], refs["maxItems"]), (1, 4))
        self.assertEqual(refs["items"]["enum"], [fact["id"] for fact in evidence["facts"]])
        self.assertEqual(checks["items"]["properties"]["rationale"]["maxLength"], 240)
        self.assertNotIn("observed_fact_ids", schema["properties"])
        self.assertNotIn("uniqueItems", refs)

    def test_unknown_reference_duplicate_check_and_duplicate_ref_fail(self) -> None:
        evidence, _, _ = synthetic_context()
        fact_id = evidence["facts"][0]["id"]
        bad_plans = [
            plan([check("C-room-impact", ["F-unknown"]), check("C-secondary-flow", [fact_id])]),
            plan([check("C-room-impact", [fact_id]), check("C-room-impact", [fact_id])]),
            plan(
                [check("C-room-impact", [fact_id, fact_id]), check("C-secondary-flow", [fact_id])]
            ),
        ]
        for raw in bad_plans:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                assemble_selection(raw, evidence)

    def test_three_by_four_reaches_twelve_bound_and_five_refs_fail(self) -> None:
        evidence, _, _ = synthetic_context()
        evidence["facts"] = [
            {"id": f"F-{index}", "source_id": "synthetic-source", "text": "synthetic"}
            for index in range(13)
        ]
        ids = [fact["id"] for fact in evidence["facts"]]
        raw = plan(
            [
                check("C-room-impact", ids[:4]),
                check("C-secondary-flow", ids[4:8]),
                check("C-controls", ids[8:12]),
            ]
        )
        _, assembled = assemble_selection(raw, evidence)
        self.assertEqual(len(assembled["observed_fact_ids"]), 12)
        with self.assertRaisesRegex(ValueError, "supporting fact"):
            assemble_selection(
                plan([check("C-room-impact", ids[:5]), check("C-secondary-flow", ids[5:9])]),
                evidence,
            )
        with self.assertRaisesRegex(ValueError, "2 or 3 checks"):
            assemble_selection(
                plan(
                    [
                        check("C-room-impact", ids[:4]),
                        check("C-secondary-flow", ids[4:8]),
                        check("C-controls", ids[8:12]),
                        check("C-sensor", ids[12:]),
                    ]
                ),
                evidence,
            )

    def test_missing_reader_in_stored_trace_fails(self) -> None:
        evidence, _, _ = synthetic_context()
        trace = {
            "contract_version": 2,
            "method": "system2-tools-repair-v1",
            "case_id": evidence["case_id"],
            "evidence": evidence,
            "tool_calls": [{"name": "get_recent_measurements"}],
            "corpus_sha256": "synthetic",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps(trace))
            with patch.dict("poc.constrained_composer.TRACE_PATHS", {"case52": path}):
                with self.assertRaisesRegex(ValueError, "all four case sources"):
                    stored_context("case52")

    def test_unread_evidence_is_withheld_after_valid_composition(self) -> None:
        evidence, _, _ = synthetic_context()
        fact_id = evidence["facts"][0]["id"]
        _, assembled = assemble_selection(
            plan([check("C-room-impact", [fact_id]), check("C-more-data", [fact_id])]),
            evidence,
        )
        display, completeness = finalize_selection(
            assembled, evidence, read_names=set(), contract_version=2
        )
        self.assertEqual(display["status"], "withheld")
        self.assertIn("no_case_evidence_source_read", completeness["issues"])

    def test_plan_shape_and_blank_rationale_fail(self) -> None:
        evidence, _, _ = synthetic_context()
        fact_id = evidence["facts"][0]["id"]
        with self.assertRaisesRegex(ValueError, "plan schema mismatch"):
            assemble_selection('{"observed_fact_ids":[]}', evidence)
        with self.assertRaisesRegex(ValueError, "rationale"):
            assemble_selection(
                plan([check("C-room-impact", [fact_id], " "), check("C-more-data", [fact_id])]),
                evidence,
            )


if __name__ == "__main__":
    unittest.main()
