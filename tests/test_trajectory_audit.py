"""The trajectory audit preserves contract failures and limits heuristic claims."""

import json
import tempfile
import unittest
from pathlib import Path

from evaluation.audit_trajectories import audit_directory, audit_trace, parse_raw


def _trace(rationale: str, refs: list[str], *, withheld: bool = False) -> dict:
    facts = [
        {"id": "F-first", "source_field": "signals.flow.first", "value": 448.0},
        {"id": "F-last", "source_field": "signals.flow.last", "value": 296.67},
    ]
    selection = {
        "observed_fact_ids": ["F-first", "F-last"],
        "next_checks": [{"id": "C-flow", "because_fact_ids": refs, "rationale": rationale}],
    }
    return {
        "contract_version": 2,
        "case_id": "case",
        "tool_calls": [
            {"name": "get_recent_measurements", "input": {}},
            {"name": "get_recent_measurements", "input": {}},
        ],
        "raw_output": json.dumps(selection),
        "validation": {"status": "invalid", "reason": "selection exceeds display bound"}
        if withheld
        else {"status": "valid", "selection": selection},
        "display": {
            "status": "withheld" if withheld else "reference_checked",
            "reason": "selection exceeds display bound" if withheld else None,
            "observations": facts,
        },
        "evidence": {"facts": facts},
    }


def _codes(row: dict) -> set[str]:
    return {event["code"] for event in row["events"]}


class TrajectoryAuditTests(unittest.TestCase):
    def test_withheld_raw_selection_is_auditable_without_content_failure(self) -> None:
        trace = _trace("Flow fell from 448 to 296.67.", ["F-first", "F-last"], withheld=True)
        row = audit_trace(trace, "D", "domain-case.json")
        self.assertEqual(parse_raw(trace)["observed_fact_ids"], ["F-first", "F-last"])
        self.assertEqual(row["raw_selected_fact_count"], 2)
        self.assertTrue(
            {"selection_overflow", "output_withheld", "repeated_identical_tool_call"} <= _codes(row)
        )
        self.assertNotIn("direction_needs_endpoints", _codes(row))
        self.assertNotIn("schema_invalid", _codes(row))

    def test_direction_and_numeric_flags_are_review_only(self) -> None:
        row = audit_trace(_trace("Flow declined to 296.67 after 48 hours.", ["F-last"]), "D", "x")
        self.assertTrue({"direction_needs_endpoints", "numeric_rationale_review"} <= _codes(row))
        self.assertTrue(
            all(
                event["severity"] == "review"
                for event in row["events"]
                if event["code"] in {"direction_needs_endpoints", "numeric_rationale_review"}
            )
        )
        self.assertNotIn(
            "direction_needs_endpoints",
            _codes(
                audit_trace(
                    _trace("Flow declined from 448 to 296.67.", ["F-first", "F-last"]),
                    "D",
                    "x",
                )
            ),
        )

    def test_no_query_and_reference_invalid_are_distinct(self) -> None:
        trace = _trace("Check flow.", ["F-last"])
        trace["tool_calls"] = []
        trace["validation"] = {"status": "invalid", "reason": "unknown fact ID"}
        self.assertTrue({"no_query", "reference_invalid"} <= _codes(audit_trace(trace, "D", "x")))

    def test_frozen_v2_counts_and_symmetric_denominators(self) -> None:
        root = Path(__file__).resolve().parents[1]
        report = audit_directory(root / "evaluation/system2-results/v2")
        self.assertEqual(report["arms"]["D"]["traces"], 5)
        self.assertEqual(report["arms"]["G"]["traces"], 5)
        self.assertEqual(report["arms"]["D"]["traces_by_code"]["selection_overflow"], 3)
        self.assertEqual(report["arms"]["D"]["traces_by_code"]["output_withheld"], 3)
        self.assertEqual(report["arms"]["G"]["traces_by_code"].get("output_withheld", 0), 0)

    def test_corrected_final_does_not_inherit_initial_overflow(self) -> None:
        trace = _trace("Flow declined to 296.67.", ["F-last"])
        initial = json.loads(trace["raw_output"])
        initial["observed_fact_ids"] = ["F-last"] * 13
        initial_raw = json.dumps(initial)
        final_raw = trace["raw_output"]
        trace["raw_output"] = initial_raw
        trace["raw_output_after_repair"] = final_raw
        trace["validation_attempts"] = [
            {
                "raw_output": initial_raw,
                "status": "invalid",
                "reason": "selection exceeds display bound",
            },
            {"raw_output": final_raw, "status": "valid", "selection": json.loads(final_raw)},
        ]
        initial_row = audit_trace(trace, "D", "x", stage="initial")
        final_row = audit_trace(trace, "D", "x", stage="final")
        self.assertTrue({"selection_overflow", "output_withheld"} <= _codes(initial_row))
        self.assertNotIn("selection_overflow", _codes(final_row))
        self.assertNotIn("output_withheld", _codes(final_row))
        self.assertIn("direction_needs_endpoints", _codes(final_row))
        self.assertIn(
            "/validation/selection/next_checks/0/rationale", final_row["events"][-1]["trace_refs"]
        )

    def test_corrected_general_uses_final_raw_and_display(self) -> None:
        trace = _trace("Flow declined from 448 to 296.67.", ["F-first", "F-last"])
        initial_raw = json.dumps({"observed_fact_ids": list(range(13)), "next_checks": []})
        final_raw = trace.pop("raw_output")
        trace["raw_answer"] = initial_raw
        trace["raw_output_after_repair"] = final_raw
        trace["validation_attempts"] = [
            {
                "raw_output": initial_raw,
                "status": "invalid",
                "reason": "selection exceeds display bound",
            },
            {"raw_output": final_raw, "status": "valid", "selection": json.loads(final_raw)},
        ]
        row = audit_trace(trace, "G", "x", stage="final")
        self.assertTrue(row["raw_selection_parsed"])
        self.assertEqual(row["raw_selected_fact_count"], 2)
        self.assertNotIn("selection_overflow", _codes(row))

    def test_stage_reports_keep_per_arm_denominators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for arm, prefix in (("D", "domain"), ("G", "general")):
                trace = _trace("Check flow.", ["F-last"])
                raw = trace["raw_output"]
                trace["validation_attempts"] = [
                    {
                        "raw_output": raw,
                        "status": "invalid",
                        "reason": "selection exceeds display bound",
                    },
                    {"raw_output": raw, "status": "valid", "selection": json.loads(raw)},
                ]
                if arm == "G":
                    trace["raw_answer"] = trace.pop("raw_output")
                (path / f"{prefix}-case.json").write_text(json.dumps(trace))
            initial = audit_directory(path, stage="initial")
            final = audit_directory(path, stage="final")
        self.assertEqual(initial["stage"], "initial")
        self.assertEqual(final["stage"], "final")
        for arm in ("D", "G"):
            self.assertEqual(initial["arms"][arm]["traces"], 1)
            self.assertEqual(final["arms"][arm]["traces"], 1)
            self.assertEqual(initial["arms"][arm]["traces_by_code"]["selection_overflow"], 1)
            self.assertEqual(final["arms"][arm]["traces_by_code"].get("selection_overflow", 0), 0)

    def test_supporting_reference_subtypes_are_distinct(self) -> None:
        trace = _trace("Check flow.", ["F-last"])
        selection = json.loads(trace["raw_output"])
        selection["observed_fact_ids"] = ["F-first"]
        selection["next_checks"] = [
            {
                "id": "C-a",
                "because_fact_ids": ["F-last", "F-unknown", "F-unknown", 7],
                "rationale": "Check flow.",
            },
            {"id": "C-b", "because_fact_ids": [], "rationale": "Check flow."},
        ]
        trace["raw_output"] = json.dumps(selection)
        trace["validation"] = {"status": "invalid", "reason": "invalid supporting fact ID"}
        trace["display"] = {"status": "withheld", "reason": "invalid supporting fact ID"}
        row = audit_trace(trace, "D", "x")
        subtypes = {item["subtype"] for item in row["supporting_reference_diagnostics"]}
        self.assertEqual(
            subtypes,
            {"known_but_unselected", "unknown_in_full_catalog", "duplicate", "nonstring", "empty"},
        )
        self.assertIn("reference_invalid", _codes(row))
        self.assertNotIn("schema_invalid", _codes(row))
        self.assertTrue(
            all(
                item["trace_refs"] == ["/raw_output"]
                for item in row["supporting_reference_diagnostics"]
            )
        )

    def test_general_full_catalog_read_supports_known_unselected_subtype(self) -> None:
        trace = _trace("Check flow.", ["F-last"])
        selection = json.loads(trace.pop("raw_output"))
        selection["observed_fact_ids"] = ["F-first"]
        trace["raw_answer"] = json.dumps(selection)
        trace["validation"] = {"valid": False, "reason": "invalid supporting fact ID"}
        trace["display"] = {
            "status": "withheld",
            "reason": "invalid supporting fact ID",
            "observations": [],
        }
        trace.pop("evidence")
        trace["tool_calls"] = [
            {"name": "Read", "input": {"file_path": "/tmp/fact_catalog.json"}, "id": "read-1"}
        ]
        catalog = {"facts": [{"id": "F-first"}, {"id": "F-last"}]}
        content = "\n".join(
            f"{index}\t{line}"
            for index, line in enumerate(json.dumps(catalog, indent=2).splitlines(), 1)
        )
        trace["tool_results"] = [
            {"tool_use_id": "read-1", "is_error": False, "truncated": False, "content": content}
        ]
        row = audit_trace(trace, "G", "x")
        self.assertEqual(
            row["supporting_reference_diagnostics"][0]["subtype"], "known_but_unselected"
        )
        self.assertEqual(row["supporting_reference_diagnostics"][0]["trace_refs"], ["/raw_answer"])
