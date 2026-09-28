"""Run the registered NAT workflow locally; no model or network call is made."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nat.runtime.loader import load_workflow  # noqa: E402

import integrations.nat_replay  # noqa: E402,F401  registration side effect
from poc.run import REPLAY  # noqa: E402


async def main() -> None:
    config = Path(__file__).with_name("nat_replay.yml")
    async with load_workflow(config) as workflow:
        async with workflow.run(REPLAY["case_id"]) as runner:
            result = await runner.result()
    if len(result["tool_results"]) != 3 or any(
        not entry["result"] for entry in result["tool_results"]
    ):
        raise RuntimeError("NAT did not return all three evidence results")
    result_bytes = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
    trace = {
        "toolkit": "nvidia-nat",
        "toolkit_version": importlib.metadata.version("nvidia-nat"),
        "execution": "deterministic registered-tool workflow; no LLM inference",
        "case_id": REPLAY["case_id"],
        "decision_time": REPLAY["decision_time"],
        "tool_calls": [entry["tool"] for entry in result["tool_results"]],
        "tool_result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "source_ids": sorted(
            {value for entry in result["tool_results"] for value in _source_ids(entry["result"])}
        ),
    }
    output = Path(__file__).with_name("trace.json")
    output.write_text(json.dumps(trace, indent=2) + "\n")
    print(json.dumps(trace, indent=2))


def _source_ids(value: object) -> list[str]:
    if isinstance(value, dict):
        return [
            *([value["source_id"]] if isinstance(value.get("source_id"), str) else []),
            *(source for item in value.values() for source in _source_ids(item)),
        ]
    if isinstance(value, list):
        return [source for item in value for source in _source_ids(item)]
    return []


if __name__ == "__main__":
    asyncio.run(main())
