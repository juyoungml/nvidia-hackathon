"""Run a bounded Claude Code comparison over an explicit public case bundle.

The caller supplies every byte visible in the isolated working directory. Two
modes are supported: ``file_agent`` exposes only Claude Code's read-only file
tools, and ``packet`` exposes no tools. No repository directory is mounted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLAUDE = Path(shutil.which("claude") or "claude")
MODEL = "claude-sonnet-5"
ENV_KEYS = frozenset(
    {"HOME", "PATH", "LANG", "LC_ALL", "TERM", "USER", "LOGNAME", "SHELL", "TMPDIR"}
)
MAX_FILE_BYTES = 2_000_000
MAX_OUTPUT_BYTES = 8_000_000
MODES = frozenset({"file_agent", "packet", "domain_tools"})
PUBLIC_FILES = frozenset(
    {
        "case.json",
        "fact_catalog.json",
        "response_schema.json",
        "source_manifest.json",
        "plan_schema.json",
        "task.json",
        "temporal/episodes.json",
        "temporal/window-fields.json",
        "tools/get_recent_measurements.json",
        "tools/get_prior_incidents.json",
        "tools/get_maintenance_timeline.json",
        "tools/get_signal_definitions.json",
    }
)
PUBLIC_REPLAY_NAMES = frozenset(
    {
        "replay-52.json",
        "replay-62.json",
        "replay-32.json",
        "derived-missing-measurements-52.json",
        "holdout-60.json",
        "holdout-63.json",
        "holdout-3.json",
        "holdout-13.json",
        "holdout-37.json",
        "holdout-5.json",
    }
)


def _check_files(files: Mapping[str, bytes]) -> None:
    for name, body in files.items():
        if name not in PUBLIC_FILES:
            raise ValueError(f"unsafe bundle filename: {name!r}")
        if not isinstance(body, bytes) or len(body) > MAX_FILE_BYTES:
            raise ValueError(f"invalid bundle bytes for {name!r}")


def _events(stdout: str) -> tuple[list[dict], dict]:
    events = []
    result = None
    for line in stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        events.append(item)
        if item.get("type") == "result":
            result = item
    if result is None:
        raise ValueError("Claude stream omitted final result")
    return events, result


def _summary(events: list[dict], result: dict) -> dict:
    models = []
    tool_calls = []
    tool_results = []
    for event in events:
        if event.get("type") == "user":
            for block in (event.get("message") or {}).get("content") or []:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                content = block.get("content")
                if isinstance(content, list):
                    content = "\n".join(
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict) and item.get("type") == "text"
                    )
                if not isinstance(content, str):
                    content = ""
                tool_results.append(
                    {
                        "tool_use_id": block.get("tool_use_id"),
                        "is_error": block.get("is_error") is True,
                        "content": content[:MAX_FILE_BYTES],
                        "truncated": len(content) > MAX_FILE_BYTES,
                    }
                )
            continue
        if event.get("type") != "assistant":
            continue
        message = event.get("message") or {}
        if message.get("model") and message["model"] not in models:
            models.append(message["model"])
        for block in message.get("content") or []:
            if block.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "name": block.get("name"),
                        "input": block.get("input"),
                        "id": block.get("id"),
                    }
                )
    return {
        "resolved_models": models,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "raw_answer": result.get("result"),
        "structured_output": result.get("structured_output"),
        "is_error": result.get("is_error"),
        "subtype": result.get("subtype"),
        "usage": result.get("usage"),
        "total_cost_usd": result.get("total_cost_usd"),
        "num_turns": result.get("num_turns"),
    }


def _successful_tool_calls(tool_calls: list[dict], tool_results: list[dict]) -> list[dict]:
    successful = {
        result.get("tool_use_id")
        for result in tool_results
        if result.get("tool_use_id") and not result.get("is_error")
    }
    return [call for call in tool_calls if call.get("id") in successful]


def run_claude_case(
    *,
    files: Mapping[str, bytes],
    prompt: str,
    mode: str,
    system_prompt: str | None = None,
    timeout_seconds: int = 120,
    max_budget_usd: float = 0.50,
    executable: Path = CLAUDE,
    json_schema: dict | None = None,
) -> dict:
    """Return an auditable comparison trace for an already-approved public case.

    ``files`` must be explicitly assembled by the frozen protocol. In packet
    mode it should be empty and the packet should be in ``prompt``. This runner
    never discovers data, reads credentials, or invokes model fallbacks.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    if mode == "packet" and files:
        raise ValueError("packet mode must not expose files")
    if not 0 < max_budget_usd <= 0.50 or not 1 <= timeout_seconds <= 300:
        raise ValueError("budget or timeout exceeds comparison limits")
    _check_files(files)
    env = {k: v for k, v in os.environ.items() if k in ENV_KEYS}
    command = [
        str(executable),
        "--model",
        MODEL,
        "--safe-mode",
        "--restricted",
        "--strict-mcp-config",
        "--tools",
        "Read,Glob,Grep" if mode == "file_agent" else "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--permission-prompts",
        "none",
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-budget-usd",
        str(max_budget_usd),
    ]
    schema_text = (
        json.dumps(json_schema, ensure_ascii=False, sort_keys=True)
        if json_schema is not None
        else None
    )
    if schema_text is not None:
        command.extend(["--json-schema", schema_text])
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())}
    with tempfile.TemporaryDirectory(prefix="claude-public-case-") as directory:
        working = Path(directory)
        for name, body in files.items():
            (working / name).parent.mkdir(parents=True, exist_ok=True)
            (working / name).write_bytes(body)
        if mode == "domain_tools":
            config = {
                "mcpServers": {
                    "public-domain": {
                        "command": sys.executable,
                        "args": [
                            str(ROOT / "evaluation/domain_mcp.py"),
                            "--bundle-dir",
                            str(working),
                        ],
                    }
                }
            }
            config_path = working / "public-mcp-config.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False))
            command.extend(["--mcp-config", str(config_path)])
        if system_prompt is not None:
            command.extend(["--system-prompt", system_prompt])
        command.append(prompt)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=working,
                env=env,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            elapsed = round(time.monotonic() - started, 3)
        except subprocess.TimeoutExpired as exc:
            return {
                "mode": mode,
                "requested_model": MODEL,
                "file_sha256": hashes,
                "json_schema_sha256": hashlib.sha256(schema_text.encode()).hexdigest()
                if schema_text is not None
                else None,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "timeout_seconds": timeout_seconds,
                "timed_out": True,
                "latency_seconds": round(time.monotonic() - started, 3),
                "stdout_bytes_before_timeout": len(exc.stdout or b""),
            }
        mcp_log = working / "mcp-calls.jsonl"
        mcp_calls = (
            [json.loads(line) for line in mcp_log.read_text().splitlines()]
            if mcp_log.exists()
            else []
        )
    trace = {
        "mode": mode,
        "requested_model": MODEL,
        "claude_version": _version(executable, env),
        "available_tools": ["Read", "Glob", "Grep"]
        + (["StructuredOutput"] if schema_text is not None else [])
        if mode == "file_agent"
        else (
            [
                f"mcp__public-domain__{name}"
                for name in (
                    "get_recent_measurements",
                    "get_prior_incidents",
                    "get_maintenance_timeline",
                    "get_signal_definitions",
                )
            ]
            if mode == "domain_tools"
            else []
        ),
        "effort": "CLI default; no explicit --effort override",
        "file_sha256": hashes,
        "json_schema_sha256": hashlib.sha256(schema_text.encode()).hexdigest()
        if schema_text is not None
        else None,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(system_prompt.encode()).hexdigest()
        if system_prompt is not None
        else None,
        "flags": [
            "<json-schema-sha256-above>"
            if schema_text is not None and arg == schema_text
            else "<system-prompt-sha256-above>"
            if system_prompt is not None and arg == system_prompt
            else arg
            for arg in command[1:-1]
        ],
        "timeout_seconds": timeout_seconds,
        "max_budget_usd": max_budget_usd,
        "latency_seconds": elapsed,
        "exit_code": completed.returncode,
        "stdout_bytes": len(completed.stdout),
        "stderr_excerpt": completed.stderr.decode("utf-8", errors="replace")[-500:],
        "timed_out": False,
    }
    if mode == "domain_tools":
        trace["mcp_calls"] = mcp_calls
        trace["mcp_call_count"] = len(mcp_calls)
        trace["mcp_tool_use_observed"] = bool(mcp_calls)
    if len(completed.stdout) > MAX_OUTPUT_BYTES:
        trace["parse_error"] = "Claude output exceeded size limit"
        return trace
    try:
        events, result = _events(completed.stdout.decode("utf-8"))
        trace.update(_summary(events, result))
        models = trace["resolved_models"]
        trace["model_mismatch"] = bool(models) and any(
            not str(model).startswith(MODEL) for model in models
        )
        trace["unavailable_tool_calls"] = sorted(
            {
                call["name"]
                for call in trace["tool_calls"]
                if call["name"] not in trace["available_tools"]
            }
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        trace["parse_error"] = str(exc)
    return trace


def run_public_bundle(
    replay: dict,
    *,
    timeout_seconds: int = 180,
    max_budget_usd: float = 0.50,
    contract_version: int = 1,
    mode: str = "file_agent",
    harness_policy: str = "off",
    executable: Path = CLAUDE,
) -> dict:
    """Run the frozen general file-agent arm and apply the common display contract."""
    from poc.evidence_contract import (
        build_case_bundle,
        build_task_packet,
        finalize_selection,
        packet_bytes,
        source_manifest,
        validation_attempt,
        withheld_display,
    )
    from poc.system2 import HARNESS_POLICIES, REPAIR_POLICY_VERSION, build_repair_prompt

    if harness_policy not in HARNESS_POLICIES:
        raise ValueError("unknown harness policy")
    if harness_policy != "off" and contract_version != 2:
        raise ValueError("repair policy requires contract v2")

    bundle = build_case_bundle(replay, contract_version=contract_version)
    files = {name: body.encode("utf-8") for name, body in bundle["files"].items()}
    if mode == "domain_tools":
        from poc.system2 import SYSTEM_PROMPT

        prompt = packet_bytes(
            build_task_packet(replay, {}, contract_version=contract_version)
        ).decode()
        system_prompt = SYSTEM_PROMPT
    else:
        prompt = (
            bundle["task"] + "\n\nThe supplied public evidence is in case.json, "
            "fact_catalog.json, response_schema.json, source_manifest.json (if present), "
            "and tools/*.json in the current "
            "working directory. Read these files to answer. Return JSON only."
        )
        system_prompt = None
    trace = run_claude_case(
        files=files,
        prompt=prompt,
        mode=mode,
        system_prompt=system_prompt,
        timeout_seconds=timeout_seconds,
        max_budget_usd=max_budget_usd,
        executable=executable,
    )
    trace.update(
        {
            "case_id": replay["case_id"],
            "corpus_sha256": bundle["corpus_sha256"],
            "contract_version": contract_version,
            "protocol": f"evaluation/SYSTEM2_PROTOCOL.md v{contract_version}",
            "harness_policy": harness_policy,
            "harness_policy_version": REPAIR_POLICY_VERSION if harness_policy != "off" else None,
            "validation_attempts": [],
            "repair": None,
        }
    )
    if contract_version == 2:
        trace["source_read_names"] = (
            sorted({call["name"] for call in trace.get("mcp_calls", [])})
            if mode == "domain_tools"
            else _source_read_names(
                _successful_tool_calls(
                    trace.get("tool_calls") or [], trace.get("tool_results") or []
                )
            )
        )
    raw = trace.get("raw_answer")
    if (
        not isinstance(raw, str)
        or trace.get("is_error")
        or trace.get("exit_code") != 0
        or trace.get("model_mismatch")
    ):
        trace["validation"] = {"valid": False, "reason": "provider or process failure"}
        trace["display"] = withheld_display("provider or process failure")
        return trace
    attempt = validation_attempt(raw, bundle["evidence"], contract_version=contract_version)
    final_evidence = bundle["evidence"]
    trace["validation_attempts"].append(attempt)
    trace["single_fence_unwrapped"] = attempt["outer_fence_normalized"]
    if attempt["status"] == "invalid" and harness_policy == "validate_repair_once":
        from poc.evidence_contract import SOURCE_TOOLS
        from poc.run import run_tool

        read_names = set(trace.get("source_read_names") or [])
        repair_sources = (
            SOURCE_TOOLS
            if "fact_catalog" in read_names
            else [name for name in SOURCE_TOOLS if name in read_names]
        )
        packet = build_task_packet(
            replay,
            {name: run_tool(name, replay) for name in repair_sources},
            contract_version=contract_version,
        )
        packet["source_manifest"] = source_manifest(read_names)
        repair_prompt = build_repair_prompt(packet, attempt, contract_version=contract_version)
        initial_cost = trace.get("total_cost_usd")
        remaining_budget = (
            max_budget_usd - initial_cost
            if isinstance(initial_cost, (int, float)) and not isinstance(initial_cost, bool)
            else max_budget_usd
        )
        trace["repair_budget_usd"] = max(0.0, remaining_budget)
        if remaining_budget <= 0:
            trace["repair"] = {"status": "skipped_budget_exhausted"}
        else:
            repaired = run_claude_case(
                files={},
                prompt=repair_prompt,
                mode="packet",
                system_prompt=system_prompt,
                timeout_seconds=timeout_seconds,
                max_budget_usd=remaining_budget,
                executable=executable,
            )
            trace["repair"] = repaired
            repaired_raw = repaired.get("raw_answer")
            trace["raw_output_after_repair"] = repaired_raw
            if (
                isinstance(repaired_raw, str)
                and not repaired.get("is_error")
                and repaired.get("exit_code") == 0
                and not repaired.get("model_mismatch")
            ):
                attempt = validation_attempt(
                    repaired_raw, packet["evidence"], contract_version=contract_version
                )
                trace["validation_attempts"].append(attempt)
                final_evidence = packet["evidence"]
            else:
                trace["repair"]["status"] = "provider_or_process_failure"
    repair = trace.get("repair") or {}
    trace["total_latency_seconds_with_repair"] = round(
        trace.get("latency_seconds", 0) + repair.get("latency_seconds", 0), 3
    )
    initial_cost, repair_cost = trace.get("total_cost_usd"), repair.get("total_cost_usd")
    trace["total_cost_usd_with_repair"] = (
        round(initial_cost + repair_cost, 6)
        if isinstance(initial_cost, (int, float)) and isinstance(repair_cost, (int, float))
        else initial_cost
        if not repair
        else None
    )
    if attempt["status"] == "valid":
        trace["validation"] = {"valid": True, "selection": attempt["selection"]}
        trace["display"], trace["completeness"] = finalize_selection(
            attempt["selection"],
            final_evidence,
            read_names=set(trace.get("source_read_names") or []),
            contract_version=contract_version,
        )
    else:
        reason = (
            "repair provider or process failure"
            if repair.get("status") == "provider_or_process_failure"
            else attempt["reason"]
        )
        trace["validation"] = {"valid": False, "reason": reason}
        trace["display"] = withheld_display(reason)
    return trace


def _source_read_names(tool_calls: list[dict]) -> list[str]:
    names: set[str] = set()
    for call in tool_calls:
        if call.get("name") not in {"Read", "Grep"}:
            continue
        value = call.get("input") or {}
        path = value.get("file_path") or value.get("path")
        if not isinstance(path, str):
            continue
        file_name = Path(path).name
        if path.endswith("fact_catalog.json"):
            names.add("fact_catalog")
        elif file_name.startswith("get_") and file_name.endswith(".json"):
            names.add(file_name[:-5])
    return sorted(names)


def _version(executable: Path, env: dict[str, str]) -> str | None:
    try:
        p = subprocess.run(
            [str(executable), "--version"], env=env, capture_output=True, text=True, timeout=5
        )
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--contract-version", type=int, choices=(1, 2), default=2)
    parser.add_argument("--mode", choices=("file_agent", "domain_tools"), default="file_agent")
    parser.add_argument("--executable", type=Path, default=CLAUDE)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = args.replay.resolve()
    if path.parent != (root / "data").resolve() or path.name not in PUBLIC_REPLAY_NAMES:
        parser.error("replay must be an approved public case in data/")
    if args.output.exists():
        parser.error("output trace already exists; choose a new path")
    replay = json.loads(path.read_text())
    trace = run_public_bundle(
        replay,
        contract_version=args.contract_version,
        mode=args.mode,
        executable=args.executable,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(json.dumps(trace, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError:
        parser.error("output trace already exists; choose a new path")
    print(
        json.dumps(
            {
                "case_id": trace["case_id"],
                "output": str(args.output),
                "resolved_models": trace.get("resolved_models"),
                "valid": trace["validation"]["valid"],
                "latency_seconds": trace["latency_seconds"],
                "total_cost_usd": trace.get("total_cost_usd"),
            }
        )
    )


if __name__ == "__main__":
    main()
