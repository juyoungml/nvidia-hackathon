"""Offline, reference-limited paired review of System 2 trace files.

No model or held-out outcome files are read. The blinded review deliberately
omits runtime and source identity; the separate key preserves the assignment.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

SOURCE_READERS = (
    "get_recent_measurements",
    "get_prior_incidents",
    "get_maintenance_timeline",
    "get_signal_definitions",
)
REDACT = re.compile(
    r"\b(?:[\w.-]+[/\\])*[\w.-]+\.(?:json|md|txt)\b|"
    r"\b(?:claude|sonnet|nemotron|nvidia|anthropic|openai|ultra)\b|"
    r"\bget_(?:recent_measurements|prior_incidents|maintenance_timeline|signal_definitions)\b",
    re.IGNORECASE,
)


def _load(path: Path) -> dict:
    if not path.is_file() or path.suffix != ".json":
        raise ValueError(f"trace must be a JSON file: {path}")
    trace = json.loads(path.read_text())
    if not isinstance(trace, dict):
        raise ValueError(f"trace must contain an object: {path}")
    return trace


def _contract(trace: dict) -> int:
    version = trace.get("contract_version", trace.get("schema_version"))
    if type(version) is not int:
        raise ValueError("trace lacks an explicit integer contract version")
    return version


def _validation(trace: dict) -> tuple[str, dict | None]:
    value = trace.get("validation") or {}
    selection = value.get("selection")
    if (value.get("status") == "valid" or value.get("valid") is True) and isinstance(
        selection, dict
    ):
        return "valid", selection
    return "invalid", None


def _raw(trace: dict) -> str | None:
    value = trace.get("raw_output", trace.get("raw_answer"))
    return value if isinstance(value, str) else None


def _tool_calls(trace: dict) -> list[dict] | None:
    calls = trace.get("tool_calls")
    return calls if isinstance(calls, list) else None


def _access(trace: dict) -> dict:
    calls = _tool_calls(trace)
    if calls is None:
        return {"tool_calls": None, "file_access_calls": None, "queried_sources": None}
    queried: set[str] = set()
    file_access = 0
    for call in calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        if name in SOURCE_READERS:
            queried.add(name)
        if name in {"Read", "Glob", "Grep"}:
            file_access += 1
            arg = call.get("input") or {}
            paths = [arg.get(key) for key in ("file_path", "path", "glob")]
            for path in paths:
                if isinstance(path, str):
                    queried.update(reader for reader in SOURCE_READERS if f"{reader}.json" in path)
    return {
        "tool_calls": len(calls),
        "file_access_calls": file_access if trace.get("mode") == "file_agent" else None,
        "queried_sources": sorted(queried),
        "queried_source_count": len(queried),
        "available_source_count": len(SOURCE_READERS),
    }


def _summary(trace: dict) -> dict:
    valid, selection = _validation(trace)
    display = trace.get("display") or {}
    display_status = display.get("status", "missing")
    accepted = valid == "valid" and display_status == (
        "reference_checked" if _contract(trace) == 2 else "verified"
    )
    reference_checked = accepted and _contract(trace) == 2
    observations = display.get("observations") or [] if accepted else []
    source_ids = {fact.get("source_id") for fact in observations if isinstance(fact, dict)}
    source_ids.discard(None)
    checks = (selection or {}).get("next_checks") or [] if accepted else []
    return {
        "case_id": trace.get("case_id"),
        "harness_policy": trace.get("harness_policy", "off"),
        "corpus_sha256": trace.get("corpus_sha256"),
        "contract_version": _contract(trace),
        "raw_output_present": _raw(trace) is not None,
        "raw_output_validation": valid,
        "validation_reason": (trace.get("validation") or {}).get("reason"),
        "outer_fence_normalized": (trace.get("validation") or {}).get("outer_fence_normalized"),
        "display_status": display_status,
        "accepted_display": accepted,
        "reference_checked": reference_checked,
        "withheld": display_status == "withheld",
        "completeness": trace.get("completeness"),
        **_access(trace),
        "selected_observation_count": len(observations) if accepted else None,
        "canonical_observation_source_count": len(source_ids) if accepted else None,
        "chosen_checks_supported_fact_ids": [
            {"id": check.get("id"), "because_fact_ids": check.get("because_fact_ids")}
            for check in checks
            if isinstance(check, dict)
        ]
        if accepted
        else None,
        "wall_seconds": trace.get("wall_seconds")
        if trace.get("wall_seconds") is not None
        else trace.get("total_latency_seconds_with_repair", trace.get("latency_seconds")),
        "model_request_seconds": trace.get("request_seconds"),
        "usage": trace.get("usage"),
        "total_cost_usd": trace.get("total_cost_usd"),
    }


def _redact(value: object) -> str:
    return REDACT.sub("[redacted]", str(value))


def _blind_answer(trace: dict) -> str:
    display = trace.get("display") or {}
    if display.get("status") not in {"reference_checked", "verified"}:
        return "Response withheld by the common display contract."
    lines = ["Observations:"]
    for fact in display.get("observations") or []:
        if isinstance(fact, dict):
            lines.append(f"- {fact.get('id', '?')}: {_redact(fact.get('text', ''))}")
    lines.append("\nLimits:")
    for item in display.get("limits") or []:
        if isinstance(item, dict):
            lines.append(f"- {item.get('id', '?')}: {_redact(item.get('text', ''))}")
    lines.append("\nSuggested next checks:")
    for check in display.get("suggested_next_checks") or []:
        if isinstance(check, dict):
            facts = [x.get("id") for x in check.get("because_facts") or [] if isinstance(x, dict)]
            lines.append(f"- {check.get('id', '?')}: {_redact(check.get('text', ''))}")
            lines.append(f"  - Selected supporting fact IDs: {', '.join(facts)}")
            lines.append(
                f"  - Rationale: {_redact(check.get('model_authored_suggestion_rationale', ''))}"
            )
    return "\n".join(lines)


def compare_pairs(
    pairs: list[tuple[Path, Path]], *, seed: int = 0, contract_version: int = 2
) -> tuple[dict, str, dict]:
    if not pairs:
        raise ValueError("at least one trace pair is required")
    rng = random.Random(seed)
    rows = []
    review = [
        f"# Blinded paired review — contract v{contract_version}",
        "",
        "Review selected evidence and suggested checks. Fact IDs show reference links only; "
        "they do not prove the rationale or action is correct.",
        "",
    ]
    key = {"seed": seed, "contract_version": contract_version, "pairs": []}
    for index, (domain_path, general_path) in enumerate(pairs, 1):
        domain, general = _load(domain_path), _load(general_path)
        dver, gver = _contract(domain), _contract(general)
        if dver != gver or dver != contract_version:
            raise ValueError(f"pair {index}: contract version mismatch")
        for field in ("case_id", "corpus_sha256"):
            if not domain.get(field) or domain.get(field) != general.get(field):
                raise ValueError(f"pair {index}: {field} mismatch or missing")
        if domain.get("harness_policy", "off") != general.get("harness_policy", "off"):
            raise ValueError(f"pair {index}: harness_policy mismatch")
        if not str(domain.get("method", "")).startswith("system2-"):
            raise ValueError(f"pair {index}: domain trace method missing")
        if general.get("mode") not in {"file_agent", "packet"}:
            raise ValueError(f"pair {index}: general trace mode missing")
        assignment = ["domain", "general"]
        rng.shuffle(assignment)
        traces = {"domain": domain, "general": general}
        paths = {"domain": domain_path, "general": general_path}
        rows.append(
            {"case_id": domain["case_id"], "domain": _summary(domain), "general": _summary(general)}
        )
        review.extend([f"## Pair {index} — {domain['case_id']}", ""])
        for letter, arm in zip(("A", "B"), assignment, strict=True):
            review.extend([f"### Response {letter}", "", _blind_answer(traces[arm]), ""])
        review.extend(
            [
                "Reviewer type: __________ (author review is not independent expert review)",
                "Selection relevance: __________",
                "Rationale support: __________",
                "Check feasibility and priority: __________",
                "Unnecessary checks: __________",
                "Unsupported diagnoses or uncertainty concerns: __________",
                "",
            ]
        )
        key["pairs"].append(
            {
                "case_id": domain["case_id"],
                "A": {"arm": assignment[0], "trace": str(paths[assignment[0]])},
                "B": {"arm": assignment[1], "trace": str(paths[assignment[1]])},
            }
        )
    return (
        {
            "contract_version": contract_version,
            "claim_boundary": "Reference checks and execution only; no semantic accuracy or winner ranking.",
            "pairs": rows,
        },
        "\n".join(review),
        key,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", type=Path, action="append", required=True)
    parser.add_argument("--general", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--contract-version", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    if len(args.domain) != len(args.general):
        parser.error("provide one --general trace for each --domain trace")
    try:
        summary, blind, key = compare_pairs(
            list(zip(args.domain, args.general, strict=True)),
            seed=args.seed,
            contract_version=args.contract_version,
        )
    except (ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output_dir / "blind-review.md").write_text(blind + "\n")
    (args.output_dir / "blind-key.json").write_text(json.dumps(key, indent=2) + "\n")
    print(args.output_dir)


if __name__ == "__main__":
    main()
