"""Summarize cycle-5 traces into results.json (no re-validation; uses each harness's own validator)."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR_EXPOSED = {"3", "5", "13", "29", "32", "37", "47", "52", "60", "62", "63"}


def classify(arm: str, trace: dict) -> dict:
    validation = trace.get("validation") or {}
    status = validation.get("status")
    reason = trace.get("run_error") or validation.get("reason")
    if arm == "ultra":
        tool_calls = len(trace.get("tool_calls") or [])
        exhausted = bool(trace.get("investigation_budget_exhausted"))
        wall = trace.get("wall_seconds")
        provider_error = bool(reason and "NVIDIA API HTTP" in str(reason))
        output = trace.get("parsed_plan") is not None
    else:
        tool_calls = len(trace.get("tool_calls") or [])
        subtype = str(trace.get("subtype") or "").lower()
        exhausted = "budget" in subtype or bool(trace.get("timed_out"))
        wall = trace.get("latency_seconds")
        provider_error = bool(trace.get("is_error")) and not trace.get("structured_output")
        output = trace.get("structured_output") is not None
        if not reason and status != "valid":
            reason = validation.get("reason") or subtype or "invalid"
    return {
        "completed_with_output": output,
        "reference_format_pass": status == "valid",
        "validation_status": status,
        "failure_reason": None if status == "valid" else reason,
        "provider_error": provider_error,
        "tool_calls": tool_calls,
        "wall_seconds": wall,
        "budget_exhausted": exhausted,
        "finish_reason": trace.get("finish_reason"),
        "model": trace.get("model") or trace.get("resolved_models"),
        "cost_usd": trace.get("total_cost_usd"),
    }


def main() -> None:
    manifest = json.loads((HERE / "case-manifest.json").read_text())
    eligible = [m for m in manifest if m["status"] == "eligible"]
    cases = []
    for m in eligible:
        rid = m["report_id"]
        row = {
            "case_id": f"PreDist-M1-fault-{rid}",
            "report_id": rid,
            "asset_id": m["asset_id"],
            "problem": m["problem"],
            "exposure": "prior_exposed" if rid in PRIOR_EXPOSED else "fresh",
            "arms": {},
        }
        for arm in ("ultra", "sonnet", "ultra-rerun", "ultra-rerun2", "ultra-rerun3"):
            path = HERE / "traces" / f"{arm}-{rid}.json"
            if arm.startswith("ultra-rerun") and not path.exists():
                continue
            if not path.exists():
                row["arms"][arm] = {"status": "not_completed_by_cutoff"}
                continue
            trace = json.loads(path.read_text())
            row["arms"][arm] = {
                "trace": str(path.relative_to(ROOT)),
                "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **classify(arm.split("-")[0], trace),
            }
        effective = row["arms"]["ultra"]
        attempts = 1
        for tag in ("ultra-rerun", "ultra-rerun2", "ultra-rerun3"):
            if effective.get("provider_error") and tag in row["arms"]:
                effective = row["arms"][tag]
                attempts += 1
        row["arms"]["ultra_with_provider_rerun"] = {**effective, "attempts": attempts}
        cases.append(row)

    def agg(arm: str, subset: list[dict]) -> dict:
        runs = [c["arms"][arm] for c in subset if "validation_status" in c["arms"][arm]]
        passes = [r for r in runs if r["reference_format_pass"]]
        non_provider = [r for r in runs if not r["provider_error"]]
        walls = [r["wall_seconds"] for r in runs if r["wall_seconds"] is not None]
        return {
            "attempted": len(subset),
            "completed_runs": len(runs),
            "valid_output": sum(r["completed_with_output"] for r in runs),
            "pass": len(passes),
            "pass_rate_of_completed": round(len(passes) / len(runs), 3) if runs else None,
            "provider_errors": sum(r["provider_error"] for r in runs),
            "pass_rate_excluding_provider_errors": (
                round(sum(r["reference_format_pass"] for r in non_provider) / len(non_provider), 3)
                if non_provider
                else None
            ),
            "budget_exhausted": sum(r["budget_exhausted"] for r in runs),
            "median_wall_seconds": round(statistics.median(walls), 1) if walls else None,
            "median_tool_calls": statistics.median([r["tool_calls"] for r in runs])
            if runs
            else None,
        }

    fresh = [c for c in cases if c["exposure"] == "fresh"]
    result = {
        "cycle": "cycle5",
        "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
        "scope": "single run per arm/case; reference/format contract check, not diagnostic accuracy",
        "summary": {
            arm: {"all": agg(arm, cases), "fresh_only": agg(arm, fresh)}
            for arm in ("ultra", "ultra_with_provider_rerun", "sonnet")
        },
        "excluded": [m for m in manifest if m["status"] != "eligible"],
        "cases": cases,
    }
    (HERE / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
