"""Offline, symmetric audit of frozen System 2 v2 trajectories.

Flags are trace-level prompts for review, not semantic accuracy labels. This
module reads only explicit trace paths and never invokes a model.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SOURCE_TOOLS = frozenset(
    {
        "get_recent_measurements",
        "get_prior_incidents",
        "get_maintenance_timeline",
        "get_signal_definitions",
    }
)
TREND = re.compile(
    r"\b(?:declin(?:e|ed|ing)|fell|fall(?:en|ing)?|drop(?:ped|ping)?|ris(?:e|en|ing)|rose|increas(?:ed|ing)|decreas(?:ed|ing))\b",
    re.I,
)
NUMBER = re.compile(r"(?<![\w.-])\d+(?:\.\d+)?(?![\w.-])")
FENCE = re.compile(r"^```(?:json)?\s*\n([\s\S]*?)\n```\s*$", re.I)


def parse_raw(trace: dict) -> dict | None:
    """Recover a selection even when the common display contract withheld it."""
    raw = trace.get("raw_output", trace.get("raw_answer"))
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    match = FENCE.fullmatch(raw)
    if match:
        raw = match.group(1)
    try:
        selection = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return selection if isinstance(selection, dict) else None


def _facts(trace: dict) -> dict[str, dict]:
    evidence = trace.get("evidence") or {}
    facts = evidence.get("facts") or (trace.get("display") or {}).get("observations") or []
    # A withheld D trace retains the original catalog; G's displayed entries
    # cover every selected supporting fact in the frozen v2 traces.
    return {
        fact["id"]: fact
        for fact in facts
        if isinstance(fact, dict) and isinstance(fact.get("id"), str)
    }


def _full_catalog_ids(trace: dict) -> set[str] | None:
    """Use only a complete catalog saved in this trace; absence is unknown."""
    evidence = trace.get("evidence") or {}
    if isinstance(evidence.get("facts"), list):
        return {
            fact["id"]
            for fact in evidence["facts"]
            if isinstance(fact, dict) and isinstance(fact.get("id"), str)
        }
    results = {
        item.get("tool_use_id"): item
        for item in trace.get("tool_results") or []
        if isinstance(item, dict)
    }
    for call in trace.get("tool_calls") or []:
        if not isinstance(call, dict) or call.get("name") != "Read":
            continue
        path = (call.get("input") or {}).get("file_path")
        if not isinstance(path, str) or not path.endswith("/fact_catalog.json"):
            continue
        result = results.get(call.get("id"))
        if not result or result.get("is_error") or result.get("truncated"):
            continue
        content = result.get("content")
        if not isinstance(content, str):
            continue
        numbered = "\n".join(re.sub(r"^\d+\t", "", line) for line in content.splitlines())
        try:
            catalog = json.loads(numbered)
        except json.JSONDecodeError:
            continue
        if isinstance(catalog, dict) and isinstance(catalog.get("facts"), list):
            return {
                fact["id"]
                for fact in catalog["facts"]
                if isinstance(fact, dict) and isinstance(fact.get("id"), str)
            }
    return None


def _supporting_reference_diagnostics(
    selection: dict | None, catalog_ids: set[str] | None, raw_ref: str
) -> list[dict]:
    """Subtype a validator failure without changing its verdict."""
    if not isinstance(selection, dict):
        return []
    chosen = selection.get("observed_fact_ids")
    selected = (
        set(chosen)
        if isinstance(chosen, list) and all(isinstance(x, str) for x in chosen)
        else set()
    )
    output = []
    for index, check in enumerate(selection.get("next_checks") or []):
        if not isinstance(check, dict):
            continue
        refs = check.get("because_fact_ids")
        kinds: dict[str, list[str]] = defaultdict(list)
        if not isinstance(refs, list):
            kinds["nonlist"].append(type(refs).__name__)
        elif not refs:
            kinds["empty"].append("")
        else:
            seen: set[str] = set()
            for ref in refs:
                if not isinstance(ref, str):
                    kinds["nonstring"].append(type(ref).__name__)
                elif ref in seen:
                    kinds["duplicate"].append(ref)
                elif ref not in selected:
                    if catalog_ids is None:
                        kinds["catalog_unavailable"].append(ref)
                    elif ref in catalog_ids:
                        kinds["known_but_unselected"].append(ref)
                    else:
                        kinds["unknown_in_full_catalog"].append(ref)
                if isinstance(ref, str):
                    seen.add(ref)
        for subtype, ids in sorted(kinds.items()):
            output.append(
                {
                    "check_index": index,
                    "check_id": check.get("id"),
                    "subtype": subtype,
                    "fact_ids": ids,
                    "trace_refs": [raw_ref],
                }
            )
    return output


def _source_access(call: dict) -> bool:
    name = call.get("name")
    if name in SOURCE_TOOLS:
        return True
    if name != "Read":
        return False
    path = (call.get("input") or {}).get("file_path", "")
    return isinstance(path, str) and any(
        path.endswith(f"/{source}.json") for source in SOURCE_TOOLS
    )


def _event(code: str, severity: str, detail: str, refs: list[str]) -> dict:
    return {"code": code, "severity": severity, "detail": detail, "trace_refs": refs}


def _field_endpoint(fact: dict) -> tuple[str, str] | None:
    field = fact.get("source_field")
    if not isinstance(field, str):
        return None
    stem, dot, endpoint = field.rpartition(".")
    return (stem, endpoint) if dot and endpoint in {"first", "last"} else None


def _numeric_support(rationale: str, facts: list[dict]) -> list[str]:
    # Dates and explicit years are reviewed by a human; this check only finds
    # numbers missing from the chosen supporting values, with no truth claim.
    tokens = set(NUMBER.findall(rationale))
    values = " ".join(str(f.get("value", "")) for f in facts)
    return sorted(token for token in tokens if token not in set(NUMBER.findall(values)))


def _stage_view(trace: dict, arm: str, stage: str) -> tuple[str | None, dict, dict, str, str]:
    """Select one candidate and its verdict without changing the saved trace."""
    raw_key = "raw_output" if arm == "D" else "raw_answer"
    attempts = trace.get("validation_attempts") or []
    if stage == "initial" and attempts:
        attempt = attempts[0]
        raw = attempt.get("raw_output", trace.get("raw_output_before_repair", trace.get(raw_key)))
        display = {
            "status": "withheld" if attempt.get("status") != "valid" else "reference_checked",
            "reason": attempt.get("reason"),
        }
        return raw, attempt, display, "/validation_attempts/0", "/validation_attempts/0/raw_output"
    if stage == "final" and len(attempts) > 1:
        raw = attempts[-1].get("raw_output", trace.get("raw_output_after_repair"))
        return (
            raw,
            trace.get("validation") or {},
            trace.get("display") or {},
            "/validation",
            f"/validation_attempts/{len(attempts) - 1}/raw_output",
        )
    raw = trace.get(raw_key)
    return (
        raw,
        trace.get("validation") or {},
        trace.get("display") or {},
        "/validation",
        f"/{raw_key}",
    )


def audit_trace(trace: dict, arm: str, trace_path: str, *, stage: str = "final") -> dict:
    if trace.get("contract_version") != 2:
        raise ValueError(f"v2 contract required: {trace_path}")
    if stage not in {"initial", "final"}:
        raise ValueError(f"unknown audit stage: {stage}")
    raw, validation, display, validation_ref, raw_ref = _stage_view(trace, arm, stage)
    selection = parse_raw({"raw_output": raw})
    validated = validation.get("selection")
    if selection is None and isinstance(validated, dict):
        selection = validated
    selected = selection.get("observed_fact_ids", []) if isinstance(selection, dict) else []
    checks = selection.get("next_checks", []) if isinstance(selection, dict) else []
    catalog = _facts(trace)
    events = []
    calls = trace.get("tool_calls") or []
    if not any(isinstance(call, dict) and _source_access(call) for call in calls):
        events.append(_event("no_query", "failure", "No source read is recorded.", ["/tool_calls"]))
    seen = {}
    for index, call in enumerate(calls):
        if not isinstance(call, dict):
            continue
        signature = json.dumps([call.get("name"), call.get("input", {})], sort_keys=True)
        if signature in seen:
            events.append(
                _event(
                    "repeated_identical_tool_call",
                    "review",
                    f"Same name and input as call {seen[signature]}.",
                    [f"/tool_calls/{seen[signature]}", f"/tool_calls/{index}"],
                )
            )
        else:
            seen[signature] = index
    reason = str(validation.get("reason", ""))
    if "bound" in reason or "exceed" in reason:
        events.append(
            _event(
                "selection_overflow",
                "failure",
                reason,
                [validation_ref + "/reason", raw_ref],
            )
        )
    elif reason:
        code = (
            "reference_invalid"
            if re.search(
                r"reference|unknown (?:fact|id)|not selected|supporting fact", reason, re.I
            )
            else "schema_invalid"
        )
        events.append(_event(code, "failure", reason, [validation_ref + "/reason"]))
    supporting_diagnostics = []
    if "invalid supporting fact ID" in reason:
        supporting_diagnostics = _supporting_reference_diagnostics(
            selection, _full_catalog_ids(trace), raw_ref
        )
        if not supporting_diagnostics:
            supporting_diagnostics = [
                {
                    "check_index": None,
                    "check_id": None,
                    "subtype": "unresolved",
                    "fact_ids": [],
                    "trace_refs": [raw_ref],
                }
            ]
        for diagnostic in supporting_diagnostics:
            events.append(
                _event(
                    "supporting_ref_" + diagnostic["subtype"],
                    "diagnostic",
                    f"Check {diagnostic['check_index']} supporting reference subtype: {diagnostic['subtype']}; values: {diagnostic['fact_ids']}",
                    diagnostic["trace_refs"],
                )
            )
    if display.get("status") == "withheld":
        events.append(
            _event(
                "output_withheld",
                "failure",
                str(display.get("reason", "withheld")),
                [
                    "/display/status" if stage == "final" else validation_ref + "/status",
                    validation_ref,
                ],
            )
        )
    # The final corrected display is the only cycle-3 content assessed here.
    # For v2, keep the original raw withheld-selection review behavior.
    inspect_content = (
        not trace.get("validation_attempts")
        or (stage == "final" and display.get("status") == "reference_checked")
        or (stage == "initial" and display.get("status") == "reference_checked")
    )
    if isinstance(selection, dict) and inspect_content:
        for index, check in enumerate(checks if isinstance(checks, list) else []):
            if not isinstance(check, dict):
                continue
            refs = check.get("because_fact_ids") or []
            rationale = check.get("rationale", "")
            if not isinstance(rationale, str) or not isinstance(refs, list):
                continue
            support = [catalog[ref] for ref in refs if isinstance(ref, str) and ref in catalog]
            # A withheld selection lives inside a JSON string, so its trace
            # pointer stops at the raw field rather than inventing a path.
            base = (
                f"{validation_ref}/selection/next_checks/{index}"
                if isinstance(validated, dict)
                else raw_ref
            )
            if TREND.search(rationale):
                endpoints: dict[str, set[str]] = defaultdict(set)
                for fact in support:
                    parsed = _field_endpoint(fact)
                    if parsed:
                        endpoints[parsed[0]].add(parsed[1])
                if not any(sides == {"first", "last"} for sides in endpoints.values()):
                    events.append(
                        _event(
                            "direction_needs_endpoints",
                            "review",
                            "Direction wording lacks selected first and last values of one field in this check's supporting facts.",
                            [base + "/rationale", base + "/because_fact_ids"]
                            if isinstance(validated, dict)
                            else [raw_ref],
                        )
                    )
            missing = _numeric_support(rationale, support)
            if missing:
                events.append(
                    _event(
                        "numeric_rationale_review",
                        "review",
                        f"Numeric tokens absent from linked fact values: {', '.join(missing)}. Check units, arithmetic, and source context manually.",
                        [base + "/rationale", base + "/because_fact_ids"]
                        if isinstance(validated, dict)
                        else [raw_ref],
                    )
                )
            if re.search(r"\b(?:caused|causes|due to|because of|resulted in)\b", rationale, re.I):
                events.append(
                    _event(
                        "causality_review",
                        "review",
                        "Causal wording requires human assessment of whether it asserts an observed cause or proposes a test.",
                        [base + "/rationale"] if isinstance(validated, dict) else [raw_ref],
                    )
                )
    return {
        "arm": arm,
        "case_id": trace.get("case_id"),
        "trace": trace_path,
        "raw_selection_parsed": isinstance(selection, dict),
        "raw_selected_fact_count": len(selected) if isinstance(selected, list) else None,
        "display_status": display.get("status"),
        "supporting_reference_diagnostics": supporting_diagnostics,
        "events": events,
    }


def audit_directory(trace_dir: Path, *, stage: str = "final") -> dict:
    if stage not in {"initial", "final"}:
        raise ValueError(f"unknown audit stage: {stage}")
    rows = []
    attempt_aware = False
    for arm, prefix in (("D", "domain"), ("G", "general")):
        paths = sorted(trace_dir.glob(f"{prefix}-*.json"))
        if not paths:
            raise ValueError(f"no {arm} traces under {trace_dir}")
        for path in paths:
            trace = json.loads(path.read_text())
            attempt_aware |= bool(trace.get("validation_attempts"))
            rows.append(audit_trace(trace, arm, str(path), stage=stage))
    counts = {}
    for arm in ("D", "G"):
        arm_rows = [row for row in rows if row["arm"] == arm]
        counts[arm] = {
            "traces": len(arm_rows),
            "traces_by_code": dict(
                sorted(
                    Counter(
                        code
                        for row in arm_rows
                        for code in {event["code"] for event in row["events"]}
                    ).items()
                )
            ),
            "events_by_code": dict(
                sorted(
                    Counter(event["code"] for row in arm_rows for event in row["events"]).items()
                )
            ),
        }
    report = {
        "scope": "frozen v2 trace-level heuristic audit; no semantic accuracy or winner aggregate",
        "arms": counts,
        "traces": rows,
    }
    if attempt_aware:
        report["stage"] = stage
        report["scope"] = (
            f"stage={stage} trace-level heuristic audit; no semantic accuracy or winner aggregate"
        )
    return report


def markdown(report: dict) -> str:
    stage_note = (
        "Initial display status is inferred from the first validation attempt; no initial display was saved. "
        "Content flags are assessed only for accepted selections in stage-aware traces."
        if report.get("stage") == "initial"
        else "Content flags in stage-aware traces assess the final displayed selection."
        if report.get("stage") == "final"
        else "Raw selections from withheld v2 traces were parsed for audit only; they remain withheld under the original contract."
    )
    lines = [
        "# Frozen v2 trajectory audit"
        + (f" — {report['stage']} stage" if report.get("stage") else ""),
        "",
        "This offline audit applies the same heuristics to D and G. Flags are review prompts, not accuracy scores. Display withholding is reported separately from content. No winner aggregate is computed.",
        "",
    ]
    priority = (
        "selection_overflow",
        "output_withheld",
        "no_query",
        "schema_invalid",
        "reference_invalid",
        "supporting_ref_known_but_unselected",
        "supporting_ref_unknown_in_full_catalog",
        "supporting_ref_duplicate",
        "supporting_ref_empty",
        "supporting_ref_nonstring",
        "supporting_ref_nonlist",
        "supporting_ref_catalog_unavailable",
        "supporting_ref_unresolved",
        "direction_needs_endpoints",
        "numeric_rationale_review",
        "repeated_identical_tool_call",
        "causality_review",
    )
    for arm in ("D", "G"):
        stats = report["arms"][arm]
        lines += [f"## Arm {arm} ({stats['traces']} traces)", ""]
        for code in priority:
            n = stats["traces_by_code"].get(code, 0)
            if not n:
                continue
            examples = [
                (row["trace"], event["trace_refs"][0])
                for row in report["traces"]
                if row["arm"] == arm
                for event in row["events"]
                if event["code"] == code
            ]
            path, ref = examples[0]
            lines.append(
                f"- **{code}**: {n}/{stats['traces']} traces; {stats['events_by_code'][code]} events. Example: `{path}#{ref}`"
            )
        lines.append("")
    lines += [
        "## Interpretation",
        "",
        "Prioritize output bound control, then review linked trend and numeric rationales. A selected ID establishes a reference link, not that the prose follows from it. Causality flags require human reading. "
        + stage_note,
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-dir", type=Path, default=Path("evaluation/system2-results/v2"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/audit-results"))
    parser.add_argument("--stage", choices=("initial", "final", "both"), default="final")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stages = ("initial", "final") if args.stage == "both" else (args.stage,)
    for stage in stages:
        report = audit_directory(args.trace_dir, stage=stage)
        suffix = f"-{stage}" if args.stage == "both" else ""
        (args.output_dir / f"trajectory-audit{suffix}.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        )
        (args.output_dir / f"trajectory-audit{suffix}.md").write_text(markdown(report))


if __name__ == "__main__":
    main()
