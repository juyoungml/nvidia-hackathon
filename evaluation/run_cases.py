"""Run the fixed public comparison serially, preserving individual traces.

Requires local Ollama Nano and NVIDIA_API_KEY in .env for the investigator.
The no-report derived probe intentionally stops after the gate decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from poc.run import load_key, nano_gate, rules_gate, run, save_trace  # noqa: E402

CASES = (
    "data/replay-52.json",
    "data/replay-62.json",
    "data/replay-32.json",
    "data/derived-no-report-20161210.json",
    "data/derived-missing-measurements-52.json",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".artifacts/poc-runs")
    parser.add_argument(
        "--case",
        action="append",
        choices=CASES,
        help="Select one or more cases; default runs all five in listed order.",
    )
    args = parser.parse_args()
    key = None
    for relative_path in args.case or CASES:
        replay_path = ROOT / relative_path
        replay = json.loads(replay_path.read_text())
        if replay["case_id"] == "PreDist-M1-derived-no-report-20161210":
            gate = nano_gate(replay, None, backend="ollama", model="nemotron-3-nano:4b")
            trace = {
                "backend": "ollama",
                "model": "nemotron-3-nano:4b",
                "case_id": replay["case_id"],
                "source": replay["source"],
                "decision_time": replay["decision_time"],
                "triage": gate,
                "rules_baseline": rules_gate(replay),
                "events": [],
                "final": None,
                "undefined_signal_names": [],
                "note": "Derived no-report gate-only probe. No Ultra call.",
            }
        else:
            if key is None:
                key = load_key(ROOT / ".env")
            trace = run(replay_path, backend="nvidia", key=key, mode="pipeline")
        path = save_trace(trace, args.output_dir)
        print(
            json.dumps(
                {
                    "case_id": trace["case_id"],
                    "trace": str(path),
                    "gate": trace["triage"]["effective_decision"]["escalate"],
                    "ultra_tool_calls": sum("tool" in event for event in trace["events"]),
                }
            )
        )


if __name__ == "__main__":
    main()
