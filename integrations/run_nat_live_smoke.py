"""Record NAT/direct equivalence for every public live reader, without inference."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integrations.live_nat_adapter import NatLiveReader  # noqa: E402
from poc.live_investigation import _read_tool  # noqa: E402


def main() -> None:
    replay_path = ROOT / "data/replay-52.json"
    replay = json.loads(replay_path.read_text())
    first, third = [replay["measurement_window"]["rows"][index]["timestamp"] for index in (0, 2)]
    calls = [
        ("get_recent_measurements", {}),
        ("get_prior_incidents", {}),
        ("get_maintenance_timeline", {}),
        ("get_signal_definitions", {}),
        ("get_temporal_episodes", {}),
        ("query_measurement_window", {"start": first, "end": third}),
    ]
    reader = NatLiveReader()
    results = []
    for name, arguments in calls:
        actual = reader.read(replay, name, arguments, True)
        expected = _read_tool(replay, name, arguments, True)
        if actual != expected:
            raise RuntimeError(f"NAT/direct mismatch: {name}")
        digest = hashlib.sha256(
            json.dumps(actual, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        results.append(
            {
                "reader": name,
                "arguments": arguments,
                "equal_to_direct": True,
                "fact_count": len(actual[1]),
                "result_and_facts_sha256": digest,
            }
        )
    trace = {
        "toolkit": "nvidia-nat",
        "toolkit_version": reader.version,
        "execution": "six registered live readers through NAT workflow; no model inference",
        "case_id": replay["case_id"],
        "public_input_sha256": hashlib.sha256(replay_path.read_bytes()).hexdigest(),
        "checks": results,
    }
    output = ROOT / "integrations/nat-live-smoke.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(trace, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
