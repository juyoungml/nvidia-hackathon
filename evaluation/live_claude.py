"""Restricted Sonnet reader for the frozen live plan-first comparison."""

from __future__ import annotations

import json
import re
from pathlib import Path

from evaluation.claude_code import (
    CLAUDE,
    MODEL,
    _source_read_names,
    _successful_tool_calls,
    run_claude_case,
)
from poc.constrained_composer import assemble_selection
from poc.evidence_contract import finalize_selection, withheld_display
from poc.live_investigation import temporal_review_flags

FACT_ID = re.compile(r"F-[A-Za-z0-9-]+")
EVIDENCE_FILES = {"case.json", "fact_catalog.json", "episodes.json", "window-fields.json"}


def _visible_fact_ids(
    tool_calls: list[dict], tool_results: list[dict], known: set[str]
) -> set[str]:
    """Approximate fact visibility from successful source content, not file paths alone."""
    results = {
        result["tool_use_id"]: result
        for result in tool_results
        if result.get("tool_use_id") and not result.get("is_error")
    }
    visible: set[str] = set()
    for call in tool_calls:
        if call.get("name") not in {"Read", "Grep"}:
            continue
        result = results.get(call.get("id"))
        if result is None:
            continue
        value = call.get("input") or {}
        path = value.get("file_path") or value.get("path")
        if not isinstance(path, str):
            continue
        filename = Path(path).name
        if filename not in EVIDENCE_FILES and not (
            filename.startswith("get_") and filename.endswith(".json")
        ):
            continue
        visible.update(FACT_ID.findall(result.get("content") or ""))
    return visible & known


def run_live_claude(
    bundle: dict,
    *,
    executable: Path = CLAUDE,
    timeout_seconds: int = 300,
    max_budget_usd: float = 0.50,
) -> dict:
    """Ask Sonnet for one native-schema plan; never substitute answer text for it."""
    files = {name: body.encode("utf-8") for name, body in bundle["files"].items()}
    prompt = (
        bundle["task"] + "\n\nPublic case files are case.json, task.json, "
        "source_manifest.json, plan_schema.json, fact_catalog.json, tools/*.json, and "
        "temporal/*.json in the current directory. Choose and read relevant sources. "
        "Each source file includes its public fact IDs and text; fact_catalog.json is an "
        "optional index of the same facts. Use raw signals and source-bound temporal episodes "
        "when relevant. Select two or three next checks, each supported "
        "by one to four fact IDs. Select applicable limit IDs. Keep the ordered union of "
        "supporting fact IDs within twelve; observations will be derived from that union. "
        "Do not assert a final root cause or recommend control changes. Return only the "
        "native plan schema object."
    )
    trace = run_claude_case(
        files=files,
        prompt=prompt,
        mode="file_agent",
        timeout_seconds=timeout_seconds,
        max_budget_usd=max_budget_usd,
        executable=executable,
        json_schema=bundle["schema"],
    )
    trace.update(
        {
            "method": "restricted_file_agent_plan_first_temporal_v1",
            "case_id": bundle["evidence"]["case_id"],
            "corpus_sha256": bundle["corpus_sha256"],
            "native_schema": bundle["schema"],
            "raw_plan": None,
            "assembled_selection": None,
            "validation": {"status": "provider_or_process_failure"},
            "display": withheld_display("provider or process failure"),
            "completeness": {"status": "not_assessed", "issues": []},
            "review_flags": [],
        }
    )
    successful_calls = _successful_tool_calls(
        trace.get("tool_calls") or [], trace.get("tool_results") or []
    )
    reads = _source_read_names(successful_calls)
    trace["source_read_names"] = reads
    trace["exact_model_match"] = trace.get("resolved_models") == [MODEL]
    trace["temporal_read_names"] = sorted(
        {
            Path(path).name
            for call in successful_calls
            if call.get("name") in {"Read", "Grep"}
            for path in [
                (call.get("input") or {}).get("file_path") or (call.get("input") or {}).get("path")
            ]
            if isinstance(path, str) and Path(path).name in {"episodes.json", "window-fields.json"}
        }
    )
    structured = trace.get("structured_output")
    known_ids = {fact["id"] for fact in bundle["evidence"]["facts"]}
    visible_ids = _visible_fact_ids(
        trace.get("tool_calls") or [], trace.get("tool_results") or [], known_ids
    )
    trace["visible_fact_ids"] = sorted(visible_ids)
    trace["visibility_rule"] = (
        "ID text in successful Read/Grep source result; partial-content approximation"
    )
    failure_reason = (
        "timeout"
        if trace.get("timed_out")
        else "budget_exhausted"
        if "budget" in str(trace.get("subtype") or "").lower()
        else "model_mismatch"
        if not trace["exact_model_match"]
        else "missing_native_structured_output"
        if not isinstance(structured, dict)
        else "provider_or_process_failure"
    )
    if (
        trace.get("timed_out")
        or trace.get("exit_code") != 0
        or trace.get("is_error")
        or not trace["exact_model_match"]
        or not isinstance(structured, dict)
    ):
        trace["validation"] = {"status": "provider_or_process_failure", "reason": failure_reason}
        trace["display"] = withheld_display(failure_reason)
        return trace
    raw_plan = json.dumps(structured, ensure_ascii=False, sort_keys=True)
    trace["raw_plan"] = raw_plan
    read_evidence = {
        **bundle["evidence"],
        "facts": [fact for fact in bundle["evidence"]["facts"] if fact["id"] in visible_ids],
    }
    try:
        parsed, selection = assemble_selection(raw_plan, read_evidence)
        trace["parsed_plan"] = parsed
        trace["assembled_selection"] = selection
        trace["validation"] = {"status": "valid"}
        trace["review_flags"] = temporal_review_flags(parsed, bundle["evidence"])
        trace["display"], trace["completeness"] = finalize_selection(
            selection,
            bundle["evidence"],
            read_names=set(reads),
            contract_version=2,
        )
    except (ValueError, KeyError, TypeError) as error:
        trace["validation"] = {"status": "invalid", "reason": str(error)}
        trace["display"] = withheld_display(str(error))
    return trace
