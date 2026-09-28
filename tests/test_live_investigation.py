"""Live investigation protocol and shared corpus checks without model calls."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from poc.evidence_contract import SOURCE_TOOLS
from poc.live_investigation import (
    _read_tool,
    build_live_bundle,
    run_live_case,
    temporal_review_flags,
)

ROOT = Path(__file__).resolve().parents[1]


def _choice(*names: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call-{index}",
                            "function": {"name": name, "arguments": "{}"},
                        }
                        for index, name in enumerate(names)
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }


class LiveInvestigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.replay = json.loads((ROOT / "data/replay-52.json").read_text())

    def test_bundle_is_stable_and_public(self) -> None:
        first = build_live_bundle(self.replay)
        second = build_live_bundle(self.replay)
        self.assertEqual(first["corpus_sha256"], second["corpus_sha256"])
        self.assertEqual(first["files"], second["files"])
        self.assertIn("do not write observed_fact_ids", first["task"])
        self.assertEqual(json.loads(first["files"]["task.json"])["task"], first["task"])
        self.assertTrue(
            set(SOURCE_TOOLS)
            <= {
                name.removeprefix("tools/").removesuffix(".json")
                for name in first["files"]
                if name.startswith("tools/")
            }
        )
        self.assertIn("temporal/window-fields.json", first["files"])
        self.assertIn("temporal/episodes.json", first["files"])
        case = json.loads(first["files"]["case.json"])
        self.assertTrue(case["report_facts"])
        self.assertEqual(case["report_facts"][0]["source_id"], case["current_report"]["source_id"])
        manifest = json.loads(first["files"]["source_manifest.json"])
        self.assertEqual(
            {item["reader"] for item in manifest["available_sources"]},
            set(SOURCE_TOOLS) | {"get_temporal_episodes", "query_measurement_window"},
        )
        self.assertTrue(
            all(item["read_state"] == "unread" for item in manifest["available_sources"])
        )
        catalog_ids = {fact["id"] for fact in first["evidence"]["facts"]}
        for name in first["files"]:
            if name.startswith(("tools/", "temporal/")):
                self.assertTrue(
                    {fact["id"] for fact in json.loads(first["files"][name])["facts"]}
                    <= catalog_ids
                )
        self.assertNotIn("diagnosis", json.loads(first["files"]["case.json"])["current_report"])
        self.assertEqual(
            first["schema"]["properties"]["next_checks"]["items"]["properties"]["because_fact_ids"][
                "items"
            ]["enum"],
            [fact["id"] for fact in first["evidence"]["facts"]],
        )

    def test_live_path_reads_then_uses_native_plan(self) -> None:
        bundle = build_live_bundle(self.replay)
        calls = []

        def fake_request(payload: dict, key: str) -> tuple[dict, float]:
            self.assertEqual(key, "test-key")
            calls.append(payload)
            if "response_format" in payload:
                evidence = json.loads(payload["messages"][1]["content"])["evidence"]
                fact_id = evidence["facts"][0]["id"]
                plan = {
                    "limit_ids": [],
                    "next_checks": [
                        {
                            "id": "C-room-impact",
                            "because_fact_ids": [fact_id],
                            "rationale": "Check scope.",
                        },
                        {
                            "id": "C-more-data",
                            "because_fact_ids": [fact_id],
                            "rationale": "Get data.",
                        },
                    ],
                }
                return {"choices": [{"message": {"content": json.dumps(plan)}}], "usage": {}}, 0.1
            if len(calls) == 1:
                return _choice(*SOURCE_TOOLS), 0.1
            if len(calls) == 2:
                return _choice("get_temporal_episodes"), 0.1
            return _choice("finish_investigation"), 0.1

        with patch("poc.live_investigation._nvidia_request", side_effect=fake_request):
            trace = run_live_case(self.replay, bundle=bundle, key="test-key")
        self.assertEqual(len(trace["planner_requests"]), 3)
        self.assertEqual(
            [len(item["request"]["messages"]) for item in trace["planner_requests"]],
            [2, 7, 9],
        )
        self.assertEqual(len(calls), 4)
        self.assertEqual(trace["finish_reason"], "explicit_finish_tool")
        self.assertEqual(trace["validation"]["status"], "valid")
        self.assertEqual(trace["display"]["status"], "reference_checked")
        self.assertEqual(trace["corpus_sha256"], bundle["corpus_sha256"])
        self.assertEqual(len(trace["usage"]), 4)
        self.assertEqual(trace["native_schema"], bundle["schema"])

    def test_window_tool_facts_use_ids_from_shared_bundle(self) -> None:
        bundle = build_live_bundle(self.replay)
        rows = json.loads(bundle["files"]["temporal/window-fields.json"])["result"]["rows"]
        _, facts = _read_tool(
            self.replay,
            "query_measurement_window",
            {"start": rows[0]["timestamp"], "end": rows[1]["timestamp"]},
            True,
        )
        catalog_ids = {fact["id"] for fact in bundle["evidence"]["facts"]}
        self.assertTrue({fact["id"] for fact in facts} <= catalog_ids)

    def test_planner_cap_stops_without_final_request(self) -> None:
        with patch(
            "poc.live_investigation._nvidia_request", return_value=(_choice(*SOURCE_TOOLS), 0.1)
        ) as call:
            trace = run_live_case(self.replay, key="test-key", max_planning_requests=1)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(trace["finish_reason"], "planning_request_limit")
        self.assertIsNone(trace["final_request"])
        self.assertEqual(trace["validation"]["status"], "invalid")

    def test_bounded_handoff_uses_seventh_request_after_six_valid_read_turns(self) -> None:
        replay = self.replay
        bundle = build_live_bundle(replay)
        rows = json.loads(bundle["files"]["temporal/window-fields.json"])["result"]["rows"]
        names = [*SOURCE_TOOLS, "get_temporal_episodes", "query_measurement_window"]
        requests = []

        def fake_request(payload: dict, key: str) -> tuple[dict, float]:
            requests.append(payload)
            if "response_format" in payload:
                evidence = json.loads(payload["messages"][1]["content"])["evidence"]
                fact_id = evidence["facts"][0]["id"]
                plan = {
                    "limit_ids": [],
                    "next_checks": [
                        {
                            "id": "C-room-impact",
                            "because_fact_ids": [fact_id],
                            "rationale": "Check rooms.",
                        },
                        {
                            "id": "C-more-data",
                            "because_fact_ids": [fact_id],
                            "rationale": "Get data.",
                        },
                    ],
                }
                return {"choices": [{"message": {"content": json.dumps(plan)}}], "usage": {}}, 0.1
            name = names[len(requests) - 1]
            args = (
                {"start": rows[0]["timestamp"], "end": rows[1]["timestamp"]}
                if name == "query_measurement_window"
                else {}
            )
            body = _choice(name)
            body["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = json.dumps(
                args
            )
            return body, 0.1

        with patch("poc.live_investigation._nvidia_request", side_effect=fake_request):
            trace = run_live_case(
                replay, bundle=bundle, key="test-key", handoff_policy="bounded_finalize_v2"
            )
        self.assertEqual(len(requests), 7)
        self.assertEqual(len(trace["planner_requests"]), 6)
        self.assertEqual(trace["method"], "live-system2-plan-first-handoff-v2")
        self.assertEqual(trace["finish_reason"], "planning_cap_handoff")
        self.assertTrue(trace["investigation_budget_exhausted"])
        self.assertEqual(trace["display"]["status"], "reference_checked")

    def test_bounded_handoff_with_report_only_evidence_withholds(self) -> None:
        with patch(
            "poc.live_investigation._nvidia_request",
            return_value=(_choice("get_signal_definitions"), 0.1),
        ) as call:
            trace = run_live_case(self.replay, key="test-key", handoff_policy="bounded_finalize_v2")
        self.assertEqual(call.call_count, 6)
        self.assertEqual(trace["finish_reason"], "planning_request_limit")
        self.assertIsNone(trace["final_request"])
        self.assertFalse(trace["investigation_budget_exhausted"])
        self.assertEqual(trace["display"]["status"], "withheld")

    def test_stored_case3_uncited_time_gets_review_flag(self) -> None:
        trace = json.loads((ROOT / "evaluation/cycle4/traces/domain-3.json").read_text())
        flags = temporal_review_flags(trace["parsed_plan"], trace["evidence"])
        flagged = [flag for flag in flags if flag["code"] == "rationale_time_not_in_cited_facts"]
        self.assertTrue(
            any(flag["check_id"] == "C-controls" and "11:00" in flag["times"] for flag in flagged)
        )

    def test_time_review_compares_whole_times(self) -> None:
        evidence = {
            "facts": [
                {"id": "F-one", "text": "Reading at 11:00", "value": "11:00", "interval": "11:00"}
            ]
        }
        plan = {
            "next_checks": [
                {
                    "id": "C-controls",
                    "because_fact_ids": ["F-one"],
                    "rationale": "Review the reading at 1:00.",
                }
            ]
        }
        flags = temporal_review_flags(plan, evidence)
        self.assertEqual(flags[0]["times"], ["1:00"])

    def test_invalid_tool_arguments_stop_without_final_inference(self) -> None:
        body = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "bad",
                                "function": {
                                    "name": "query_measurement_window",
                                    "arguments": json.dumps(
                                        {"start": "2000-01-01", "end": "2099-01-01"}
                                    ),
                                },
                            }
                        ]
                    }
                }
            ],
            "usage": {},
        }
        for policy in ("explicit_finish_v1", "bounded_finalize_v2"):
            with self.subTest(policy=policy):
                with patch(
                    "poc.live_investigation._nvidia_request", return_value=(body, 0.1)
                ) as call:
                    trace = run_live_case(self.replay, key="test-key", handoff_policy=policy)
                self.assertEqual(call.call_count, 1)
                self.assertEqual(trace["validation"]["status"], "invalid")
                self.assertIsNone(trace["final_request"])

    def test_provider_error_never_hands_off(self) -> None:
        with patch(
            "poc.live_investigation._nvidia_request", side_effect=RuntimeError("provider failed")
        ) as call:
            trace = run_live_case(self.replay, key="test-key", handoff_policy="bounded_finalize_v2")
        self.assertEqual(call.call_count, 1)
        self.assertIsNone(trace["final_request"])
        self.assertEqual(trace["display"]["status"], "withheld")


if __name__ == "__main__":
    unittest.main()
