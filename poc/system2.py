"""Grounded System2 replay with optional read-only tool use (v2 by default)."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from check_nvidia import load_key  # noqa: E402

from poc.evidence_contract import (  # noqa: E402
    build_case_bundle,
    build_evidence,
    build_task_packet,
    finalize_selection,
    normalize_response,
    packet_bytes,
    source_manifest,
    validate_selection,
    withheld_display,
)
from poc.run import TOOLS, ULTRA_MODEL, call_model, run_tool  # noqa: E402

SYSTEM_PROMPT = (
    "You are a read-only plant investigator. Choose observed fact IDs from supplied evidence; "
    "do not author observed claims. Choose limitations and next checks from the catalogs. "
    "A next-check rationale is a suggestion, not a measured observation or proven cause. "
    "Use only information at or before the decision time. Earlier reports do not prove the "
    "current cause. No root-cause conclusion is required. Reply with only JSON matching the "
    "response_schema."
)
ALLOWED_TOOLS = {tool["function"]["name"] for tool in TOOLS}


def _tool_evidence(replay: dict, name: str, result: dict) -> dict:
    packet = build_evidence(replay, {name: result})
    return {
        "tool_result": result,
        "facts": [
            fact
            for fact in packet["facts"]
            if fact["source_id"] != replay["current_report"]["source_id"]
        ],
    }


def run_system2(
    replay: dict,
    *,
    mode: str = "tools",
    backend: str = "nvidia",
    model: str = ULTRA_MODEL,
    key: str | None = None,
    max_rounds: int = 6,
    contract_version: int = 1,
) -> dict:
    started = time.monotonic()
    if mode not in {"tools", "packet"}:
        raise ValueError("mode must be tools or packet")
    if contract_version not in {1, 2}:
        raise ValueError("unknown contract version")
    trace = {
        "schema_version": contract_version,
        "contract_version": contract_version,
        "method": f"system2-{mode}",
        "case_id": replay["case_id"],
        "backend": backend,
        "model": model,
        "decision_time": replay["decision_time"],
        "question": None,
        "input": None,
        "packet_sha256": None,
        "corpus_sha256": None,
        "tool_calls": [],
        "model_events": [],
        "evidence": None,
        "raw_output": None,
        "validation": None,
        "completeness": None,
        "display": withheld_display("run not completed"),
        "request_seconds": 0.0,
        "wall_seconds": None,
    }
    try:
        trace["corpus_sha256"] = build_case_bundle(replay, contract_version=contract_version)[
            "corpus_sha256"
        ]
        if mode == "packet":
            tool_results = {name: run_tool(name, replay) for name in sorted(ALLOWED_TOOLS)}
            packet = build_task_packet(replay, tool_results, contract_version=contract_version)
            payload = packet_bytes(packet)
            trace["question"] = packet["question"]
            trace["input"] = packet
            trace["packet_sha256"] = hashlib.sha256(payload).hexdigest()
            trace["evidence"] = packet["evidence"]
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload.decode()},
            ]
            choice, latency = call_model(messages, key, backend=backend, model=model)
            trace["request_seconds"] += latency
            trace["model_events"].append(
                {
                    "round": 1,
                    "latency_seconds": latency,
                    "finish_reason": choice.get("finish_reason"),
                }
            )
            raw = choice["message"].get("content") or ""
        else:
            # The question and catalog are common across methods. Only actual tool reads enter evidence.
            initial_packet = build_task_packet(replay, {}, contract_version=contract_version)
            trace["question"] = initial_packet["question"]
            trace["input"] = initial_packet
            trace["packet_sha256"] = hashlib.sha256(packet_bytes(initial_packet)).hexdigest()
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": packet_bytes(initial_packet).decode()},
            ]
            tool_results = {}
            for index in range(max_rounds):
                choice, latency = call_model(
                    messages, key, backend=backend, model=model, tools=TOOLS
                )
                trace["request_seconds"] += latency
                message = choice["message"]
                calls = message.get("tool_calls") or []
                trace["model_events"].append(
                    {
                        "round": index + 1,
                        "latency_seconds": latency,
                        "finish_reason": choice.get("finish_reason"),
                        "tool_names": [c.get("function", {}).get("name") for c in calls],
                        "content": message.get("content"),
                    }
                )
                if not calls:
                    raw = message.get("content") or ""
                    break
                messages.append(message)
                for call_index, call in enumerate(calls, 1):
                    function = call.get("function") or {}
                    name = function.get("name")
                    if name not in ALLOWED_TOOLS:
                        raise ValueError(f"unknown tool: {name}")
                    args = function.get("arguments") or "{}"
                    if isinstance(args, str):
                        args = json.loads(args)
                    if args != {}:
                        raise ValueError(f"tool {name} requires empty arguments")
                    result = run_tool(name, replay)
                    tool_results[name] = result
                    call_id = call.get("id") or f"local-{index + 1}-{call_index}"
                    trace["tool_calls"].append({"name": name, "call_id": call_id, "result": result})
                    response = _tool_evidence(replay, name, result)
                    if contract_version == 2:
                        response["source_manifest"] = source_manifest(set(tool_results))
                    content = json.dumps(response, ensure_ascii=False)
                    if backend == "ollama":
                        messages.append({"role": "tool", "tool_name": name, "content": content})
                    else:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": name,
                                "content": content,
                            }
                        )
            else:
                raise ValueError(f"model exceeded {max_rounds} tool rounds")
            trace["evidence"] = build_evidence(replay, tool_results)
        trace["raw_output"] = raw
        selection = validate_selection(raw, trace["evidence"], contract_version=contract_version)
        _, normalized = normalize_response(raw, contract_version=contract_version)
        trace["validation"] = {
            "status": "valid",
            "selection": selection,
            "outer_fence_normalized": normalized,
        }
        reads = set(tool_results) if mode == "tools" else set(ALLOWED_TOOLS)
        trace["display"], trace["completeness"] = finalize_selection(
            selection,
            trace["evidence"],
            read_names=reads,
            contract_version=contract_version,
        )
    except (ValueError, KeyError, TypeError, RuntimeError) as error:
        trace["validation"] = {
            "status": "invalid",
            "error_type": type(error).__name__,
            "reason": str(error),
        }
        trace["display"] = withheld_display(str(error))
        trace["completeness"] = {"status": "not_assessed", "issues": []}
    trace["wall_seconds"] = round(time.monotonic() - started, 3)
    return trace


def save_trace(trace: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S%fZ")
    slug = re.sub(r"[^A-Za-z0-9-]+", "-", trace["case_id"])
    path = directory / f"system2-{trace['method']}-{slug}-{stamp}-{uuid.uuid4().hex[:8]}.json"
    with path.open("x") as file:
        json.dump(trace, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--mode", choices=("tools", "packet"), default="tools")
    parser.add_argument("--backend", choices=("nvidia", "ollama"), default="nvidia")
    parser.add_argument("--model", default=ULTRA_MODEL)
    parser.add_argument(
        "--contract-version",
        type=int,
        choices=(1, 2),
        default=2,
        help="Evidence contract version (default: 2; use 1 to replay the pilot)",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".artifacts/system2")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    replay = json.loads(args.replay.read_text())
    key = load_key(ROOT / ".env") if args.backend == "nvidia" else None
    trace = run_system2(
        replay,
        mode=args.mode,
        backend=args.backend,
        model=args.model,
        key=key,
        contract_version=args.contract_version,
    )
    path = save_trace(trace, args.output_dir)
    print(
        json.dumps(
            {
                "trace": str(path),
                "case_id": trace["case_id"],
                "validation": trace["validation"],
                "display": trace["display"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
