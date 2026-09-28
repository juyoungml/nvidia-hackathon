"""Generate a fixed evidence summary and audit public replay investigation traces.

This is a small-case, rule-based audit. It does not grade diagnostic accuracy.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import time
from pathlib import Path

SOURCE_ID_PATTERN = re.compile(r"PreDist-M1-(?:fault|disturbance|substation|derived)-[\w-]+")
SIGNAL_PATTERN = re.compile(r"\b[sp]_[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*\b")
UNCERTAINTY_TERMS = (
    "unknown",
    "uncertain",
    "insufficient",
    "cannot establish",
    "cannot determine",
    "not prove",
    "불확실",
    "알 수 없",
    "판단할 수 없",
    "단정할 수 없",
    "확인할 수 없",
    "증명할 수 없",
    "특정할 수 없",
    "부족",
)


def source_ids(replay: dict) -> set[str]:
    return {
        replay["current_report"]["source_id"],
        replay["measurement_window"]["source_id"],
        *(record["source_id"] for record in replay["prior_faults"]),
        *(record["source_id"] for record in replay["prior_disturbances"]),
    }


def check_cutoff(replay: dict) -> None:
    decision = dt.datetime.fromisoformat(replay["decision_time"])
    start = dt.datetime.fromisoformat(replay["measurement_window"]["start"])
    if dt.datetime.fromisoformat(replay["measurement_window"]["end"]) != decision:
        raise ValueError("measurement window end differs from decision time")
    for row in replay["measurement_window"]["rows"]:
        when = dt.datetime.fromisoformat(row["timestamp"])
        if not start <= when <= decision:
            raise ValueError(f"measurement crosses cutoff: {when}")
    for section, field in (("prior_faults", "report_date"), ("prior_disturbances", "event_start")):
        for row in replay[section]:
            if dt.datetime.fromisoformat(row[field]) >= decision:
                raise ValueError(f"{section} crosses cutoff: {row[field]}")


def baseline(replay: dict) -> dict:
    """Produce the same deterministic search-and-summary response for every case."""
    check_cutoff(replay)
    start = time.monotonic()
    rows = replay["measurement_window"]["rows"]
    left = "s_hc1_supply_temperature"
    right = "s_hc1_supply_temperature_setpoint"
    pairs = [
        (row[left], row[right])
        for row in rows
        if row.get(left) is not None and row.get(right) is not None
    ]
    measurement_id = replay["measurement_window"]["source_id"]
    report_id = replay["current_report"]["source_id"]
    lines = [
        f"At {replay['decision_time']}, the reported problem was "
        f"{replay['current_report']['problem']} [{report_id}]."
    ]
    if pairs:
        gaps = [abs(actual - target) for actual, target in pairs]
        lines.append(
            f"The preceding measurement window contains {len(rows)} rows; "
            f"{left} versus {right} has mean absolute gap "
            f"{statistics.mean(gaps):.2f} °C across {len(gaps)} paired rows [{measurement_id}]."
        )
    else:
        lines.append(
            f"No paired heating supply and setpoint values are present [{measurement_id}]."
        )
    if replay["prior_faults"]:
        earlier = max(replay["prior_faults"], key=lambda row: row["report_date"])
        lines.append(
            f"The latest earlier report, dated {earlier['report_date']}, recorded "
            f"{earlier['problem']} [{earlier['source_id']}]. Its narrative availability "
            "at the decision time is unverified."
        )
    lines.append(
        "This evidence cannot establish heat delivery to the customer's rooms. "
        "A human engineer should obtain customer-side temperature and secondary heating-circuit "
        "flow, and check the controller parameter-change record. The present cause remains unknown."
    )
    return {
        "case_id": replay["case_id"],
        "method": "deterministic_search_and_summary",
        "final": "\n".join(lines),
        "events": [],
        "latency_seconds": round(time.monotonic() - start, 4),
        "note": "Fixed template using only the replay evidence; no language model or tool loop.",
    }


def score(replay: dict, trace: dict) -> dict:
    """Return observable checks, leaving clinical/domain usefulness for human review."""
    check_cutoff(replay)
    if trace["case_id"] != replay["case_id"]:
        raise ValueError("trace and replay case IDs differ")
    answer = trace.get("final") or ""
    valid_ids = source_ids(replay)
    cited = sorted(set(SOURCE_ID_PATTERN.findall(answer)))
    known_signals = set(replay["features"])
    mentioned_signals = set(SIGNAL_PATTERN.findall(answer))
    events = trace.get("events") or []
    calls = [event["tool"] for event in events if "tool" in event]
    model_latency = sum(event.get("latency_seconds", 0) for event in events)
    triage = trace.get("triage") or {}
    triage_latency = triage.get("latency_seconds") or 0
    return {
        "case_id": replay["case_id"],
        "case_kind": "derived_probe" if replay.get("derived_case") else "published_incident",
        "method": trace.get("method", trace.get("model", "unknown")),
        "final_answer": answer,
        "citation_ids": cited,
        "valid_citation_ids": sorted(set(cited) & valid_ids),
        "invalid_citation_ids": sorted(set(cited) - valid_ids),
        "has_any_citation": bool(cited),
        "current_report_source_cited": replay["current_report"]["source_id"] in cited,
        "measurement_source_cited": replay["measurement_window"]["source_id"] in cited,
        "undefined_signal_names": sorted(mentioned_signals - known_signals),
        "uncertainty_stated": any(term in answer.lower() for term in UNCERTAINTY_TERMS),
        "tool_calls": calls,
        "tool_call_count": len(calls),
        "model_request_count": sum("latency_seconds" in event for event in events),
        "model_request_latency_seconds": round(model_latency, 2),
        "triage_latency_seconds": round(triage_latency, 2),
        "total_model_latency_seconds": round(model_latency + triage_latency, 2),
        "triage_validation_status": triage.get("validation_status"),
        "triage_decision": triage.get("decision"),
        "triage_effective_decision": triage.get("effective_decision"),
        "rules_gate": trace.get("rules_baseline"),
        "total_latency_seconds": trace.get("latency_seconds"),
        "latency_note": "Model/API request time is not plant fault identification time.",
        "review_required": [
            "Citation existence does not establish claim support.",
            "Uncertainty wording does not establish appropriate abstention.",
            "Human review must assess next-check usefulness and unsafe control advice.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="append", type=Path, required=True)
    parser.add_argument("--trace", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    replays = {
        item["case_id"]: item for path in args.replay if (item := json.loads(path.read_text()))
    }
    baselines = [baseline(replay) for replay in replays.values()]
    traces = [json.loads(path.read_text()) for path in args.trace]
    results = [score(replays[trace["case_id"]], trace) for trace in [*baselines, *traces]]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"baselines": baselines, "checks": results}, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({"output": str(args.output), "checks": len(results)}))


if __name__ == "__main__":
    main()
