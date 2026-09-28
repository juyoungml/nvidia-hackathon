"""Reproduce offline audits from frozen cycle-3/4 outputs; no model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evaluation.evaluate import baseline

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent / "content-review"
CASES = (52, 3, 29, 47)
ARMS = ("domain", "general")


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def union_references(checks: list[dict]) -> list[str]:
    return list(dict.fromkeys(fact for check in checks for fact in check["because_fact_ids"]))


def is_temporal(fact: dict) -> bool:
    return fact["source_field"].startswith("temporal.")


def cycle4_audit() -> tuple[list[dict], list[dict], dict]:
    rows = []
    packets = []
    key = {"scope": "Original valid cycle-4 traces only; case-52 dev fix is excluded", "labels": {}}
    for case in CASES:
        for arm in ARMS:
            path = ROOT / f"evaluation/cycle4/traces/{arm}-{case}.json"
            trace = read(path)
            valid = (
                trace["validation"]["status"] == "valid"
                and trace["display"]["status"] == "reference_checked"
            )
            row = {
                "case": case,
                "arm": arm,
                "valid": valid,
                "trace": str(path.relative_to(ROOT)),
                "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            if valid:
                selection = trace["assembled_selection"]
                checks = selection["next_checks"]
                refs = union_references(checks)
                obs = selection["observed_fact_ids"]
                facts = {fact["id"]: fact for fact in trace["display"]["observations"]}
                temporal_ids = {fid for fid, fact in facts.items() if is_temporal(fact)}
                temporal_by_check = [
                    {
                        "check_id": check["id"],
                        "cited_temporal_fact_ids": sorted(
                            set(check["because_fact_ids"]) & temporal_ids
                        ),
                    }
                    for check in checks
                ]
                row.update(
                    reference_count=len(refs),
                    observation_count=len(obs),
                    observation_equals_reference_union=obs == refs,
                    missing_references=sorted(set(refs) - set(obs)),
                    injected_old_style_one_id_deletion={
                        "deleted_id": refs[0],
                        "missing_reference_count": len(set(refs) - set(obs[1:])),
                        "label": "synthetic structural mutation, not model output",
                    },
                    temporal_reference_count=len(temporal_ids),
                    check_count_depending_on_temporal_facts=sum(
                        bool(c["cited_temporal_fact_ids"]) for c in temporal_by_check
                    ),
                    temporal_by_check=temporal_by_check,
                    temporal_removal_label="synthetic evidence removal; original rationale unchanged; no quality counterfactual",
                )
                if case in (3, 29):
                    # Stable pseudonyms; do not put arm names into packet filenames or content.
                    label = (
                        "P"
                        + hashlib.sha256(f"cycle4-blind-v1:{case}:{arm}".encode()).hexdigest()[:8]
                    )
                    key["labels"][label] = {
                        "case": case,
                        "arm": arm,
                        "trace": row["trace"],
                        "trace_sha256": row["trace_sha256"],
                    }
                    packets.append(
                        {
                            "label": label,
                            "case": case,
                            "source": "original valid cycle-4 model output",
                            "checks": [
                                {
                                    "id": check["id"],
                                    "rationale": check["rationale"],
                                    "cited_facts": [
                                        facts[fid] for fid in check["because_fact_ids"]
                                    ],
                                }
                                for check in checks
                            ],
                        }
                    )
            else:
                row.update(
                    failure_reason=trace.get("finish_reason") or trace["validation"].get("reason")
                )
            rows.append(row)
    packets.sort(key=lambda p: (p["case"], p["label"]))
    return rows, packets, key


def cycle3_audit() -> list[dict]:
    rows = []
    for path in sorted((ROOT / "evaluation/cycle3/traces").glob("domain-*.json")):
        trace = read(path)
        raw = trace.get("raw_output_after_repair") or trace.get("raw_output")
        row = {
            "trace": str(path.relative_to(ROOT)),
            "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "original_validation": trace["validation"]["status"],
        }
        try:
            output = json.loads(raw)
            observations = output["observed_fact_ids"]
            refs = union_references(output["next_checks"])
            row.update(
                parseable=True,
                observation_count=len(observations),
                reference_count=len(refs),
                missing_references=sorted(set(refs) - set(observations)),
                exact_union=observations == refs,
            )
        except (TypeError, ValueError, KeyError) as exc:
            row.update(parseable=False, parse_error=type(exc).__name__)
        rows.append(row)
    return rows


def main() -> None:
    cycle4, packets, key = cycle4_audit()
    cycle3 = cycle3_audit()
    summaries = []
    for case in (3, 29):
        replay = read(ROOT / f"data/holdout-{case}.json")
        generated = baseline(replay)
        summaries.append(
            {
                "case": case,
                "source": f"data/holdout-{case}.json",
                "method": generated["method"],
                "final": generated["final"],
                "note": "Deterministic basic summary from existing template; no model inference; case 3 was development-exposed, 29 is no longer fresh after cycle 4.",
            }
        )
    write(
        OUT / "results.json",
        {
            "scope": "offline frozen-output audit; injected removals are synthetic, no diagnosis/field benefit measured",
            "cycle4_all_cases": cycle4,
            "cycle3_prior_duplicated_list_domain_outputs": cycle3,
            "basic_summaries": summaries,
            "cycle4_primary_success": {
                arm: {
                    "valid": sum(row["valid"] for row in cycle4 if row["arm"] == arm),
                    "denominator": 4,
                }
                for arm in ARMS
            },
        },
    )
    write(
        REVIEW / "PACKETS.json",
        {
            "rubric": "RUBRIC.md",
            "scope": "Original valid paired cycle-4 cases 3 and 29 only; no outcomes or arm labels",
            "packets": packets,
        },
    )
    write(REVIEW / "REVEAL_KEY.json", key)


if __name__ == "__main__":
    main()
