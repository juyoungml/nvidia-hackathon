"""Freeze complete displayed-check packets from original cycle-4 traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main() -> None:
    packets = []
    key = {"scope": "original valid paired cycle-4 traces; complete displayed checks", "labels": {}}
    for case in (3, 29):
        for arm in ("domain", "general"):
            path = ROOT / f"evaluation/cycle4/traces/{arm}-{case}.json"
            trace = read(path)
            if (
                trace["validation"]["status"] != "valid"
                or trace["display"]["status"] != "reference_checked"
            ):
                raise ValueError("paired trace is not valid")
            label = (
                "Q"
                + hashlib.sha256(f"cycle4-complete-blind-v2:{case}:{arm}".encode()).hexdigest()[:8]
            )
            displayed = trace["display"]
            model_checks = {c["id"]: c for c in trace["parsed_plan"]["next_checks"]}
            checks = []
            for check in displayed["suggested_next_checks"]:
                model = model_checks[check["id"]]
                if model["rationale"] != check["model_authored_suggestion_rationale"]:
                    raise ValueError("display rationale differs from original model plan")
                if model["because_fact_ids"] != [f["id"] for f in check["because_facts"]]:
                    raise ValueError("display citations differ from original model plan")
                checks.append(
                    {
                        "id": check["id"],
                        "canonical_check_text": check["text"],
                        "model_rationale": check["model_authored_suggestion_rationale"],
                        "cited_facts": check["because_facts"],
                    }
                )
            packets.append(
                {
                    "label": label,
                    "case": case,
                    "source": "original valid cycle-4 displayed plan",
                    "displayed_limits": displayed["limits"],
                    "checks": checks,
                }
            )
            key["labels"][label] = {
                "case": case,
                "arm": arm,
                "trace": str(path.relative_to(ROOT)),
                "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
    packets.sort(key=lambda p: (p["case"], p["label"]))
    write(
        HERE / "PACKETS.json",
        {
            "rubric": "RUBRIC.md",
            "scope": "original valid paired cases 3 and 29; complete displayed checks; no outcomes or arm labels",
            "packets": packets,
        },
    )
    write(HERE / "REVEAL_KEY.json", key)


if __name__ == "__main__":
    main()
