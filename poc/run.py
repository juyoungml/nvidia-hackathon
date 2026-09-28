"""Replay public incidents through a bounded Nano gate and read-only Ultra investigator."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from check_nvidia import load_key  # noqa: E402

from poc.rate_limit import RequestPacer, retry_delay_seconds  # noqa: E402

ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
NANO_MODEL = "nemotron-3-nano:4b"
ULTRA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
NVIDIA_PACER = RequestPacer(rpm=18)
BACKEND = os.environ.get("POC_BACKEND", "nvidia")
MODEL = os.environ.get("NVIDIA_MODEL", ULTRA_MODEL)
REPLAY = json.loads((ROOT / "data/replay-52.json").read_text())
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    }
    for name, description in [
        (
            "get_recent_measurements",
            "Read pre-decision public measurements and setpoints; return numeric summaries, not a diagnosis.",
        ),
        (
            "get_prior_incidents",
            "Read previous published reports for this asset; current diagnosis and remedy withheld.",
        ),
        (
            "get_maintenance_timeline",
            "Read previous maintenance timestamps with no assumed completion outcome.",
        ),
        ("get_signal_definitions", "Explain source sensor names, sides and units."),
    ]
]


def measurement_summary(replay: dict | None = None) -> dict:
    replay = replay or REPLAY
    rows = replay["measurement_window"]["rows"]
    source_id = replay["measurement_window"]["source_id"]
    signals = {
        "outdoor_temperature_c": "outdoor_temperature",
        "secondary_heating_circuit_supply_temperature_c": "s_hc1_supply_temperature",
        "secondary_heating_circuit_supply_setpoint_c": "s_hc1_supply_temperature_setpoint",
        "primary_network_meter_heat_power_kw": "p_net_meter_heat_power",
        "primary_network_meter_flow_l_per_hour": "p_net_meter_flow",
    }
    summary = {}
    for readable_name, raw_name in signals.items():
        values = [row.get(raw_name) for row in rows if row.get(raw_name) is not None]
        summary[readable_name] = {
            "original_field": raw_name,
            "first": round(values[0], 2) if values else None,
            "last": round(values[-1], 2) if values else None,
            "min": round(min(values), 2) if values else None,
            "max": round(max(values), 2) if values else None,
            "mean": round(statistics.mean(values), 2) if values else None,
            "unit": replay.get("features", {}).get(raw_name, {}).get("unit", ""),
        }
    gaps = [
        abs(row["s_hc1_supply_temperature"] - row["s_hc1_supply_temperature_setpoint"])
        for row in rows
        if row.get("s_hc1_supply_temperature") is not None
        and row.get("s_hc1_supply_temperature_setpoint") is not None
    ]
    return {
        "source_id": source_id,
        "interval": replay["measurement_window"]["start"]
        + " to "
        + replay["measurement_window"]["end"],
        "samples": len(rows),
        "last_sample_time": rows[-1]["timestamp"] if rows else None,
        "signals": summary,
        "secondary_heating_supply_vs_setpoint_absolute_gap_celsius": {
            "mean": round(statistics.mean(gaps), 2) if gaps else None,
            "max": round(max(gaps), 2) if gaps else None,
            "samples_within_2C": sum(gap <= 2 for gap in gaps),
            "sample_count": len(gaps),
        },
        "interpretation_limits": [
            "This sensor's secondary supply temperature tracking its setpoint does not prove heat reached rooms.",
            "No room/radiator temperature, secondary heat-circuit flow, valve position, or timestamped controller parameter-change record is available in this replay.",
            "p_net_meter_flow is primary network-side flow, not customer/secondary circuit flow.",
            "No normal operating range is provided for heat power or flow.",
        ],
    }


def run_tool(name: str, replay: dict | None = None) -> dict:
    replay = replay or REPLAY
    if name == "get_recent_measurements":
        return measurement_summary(replay)
    if name == "get_prior_incidents":
        return {
            "records": replay["prior_faults"],
            "note": "Only reports dated before this incident are available.",
        }
    if name == "get_maintenance_timeline":
        return {
            "records": replay["prior_disturbances"],
            "note": "Timestamps do not prove resolution.",
        }
    if name == "get_signal_definitions":
        return {
            "definitions": {
                "s_hc1_supply_temperature": "SECONDARY heating circuit 1 supply temperature, °C",
                "s_hc1_supply_temperature_setpoint": "SECONDARY heating circuit 1 supply setpoint, °C",
                "p_net_meter_heat_power": "PRIMARY network-side meter heat power, kW; normal range unavailable",
                "p_net_meter_flow": "PRIMARY network-side meter flow, l/h; not customer flow",
                "outdoor_temperature": "Outside air temperature, °C",
                "s_dhw_supply_temperature": "Domestic hot water supply, not space heating",
            }
        }
    raise ValueError(f"unknown tool: {name}")


def call_model(
    messages: list[dict],
    key: str | None,
    *,
    backend: str | None = None,
    model: str | None = None,
    tools: list[dict] | None = None,
) -> tuple[dict, float]:
    backend = backend or BACKEND
    model = model or MODEL
    if backend == "ollama":
        payload = {
            "model": model,
            "messages": messages,
            "think": False,
            "options": {"temperature": 0},
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
        )
        start = time.monotonic()
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        return {"message": result["message"], "finish_reason": result.get("done_reason")}, round(
            time.monotonic() - start, 2
        )
    if backend != "nvidia" or not key:
        raise RuntimeError(f"unsupported backend or missing key: {backend}")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 1200,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    if tools:
        payload.update({"tools": tools, "tool_choice": "auto"})
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    start = time.monotonic()
    for attempt in range(3):
        NVIDIA_PACER.wait()
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.load(response)
            break
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 2:
                time.sleep(retry_delay_seconds(error.headers.get("Retry-After"), attempt))
                continue
            raise RuntimeError(f"NVIDIA API HTTP {error.code}") from error
    return result["choices"][0], round(time.monotonic() - start, 2)


def undefined_signal_names(answer: str, known_names: set[str]) -> list[str]:
    """Find tag-like names absent from the public dataset schema."""
    mentioned = set(re.findall(r"\b[sp]_[a-z][a-z0-9_]*\b", answer))
    return sorted(mentioned - known_names)


def unsupported_certainty_markers(answer: str) -> list[str]:
    """Catch confident fault-location claims that this sparse replay cannot establish."""
    return [
        marker for marker in ("가능성 높음", "원인으로 판단", "원인으로 보임") if marker in answer
    ]


def rules_gate(replay: dict) -> dict:
    problem = replay["current_report"]["problem"].lower()
    escalate = any(
        term in problem
        for term in ("no heat", "not enough heat", "cold", "leak", "failure", "outage")
    )
    return {
        "escalate": escalate,
        "reason": "customer service-loss report" if escalate else "no rule trigger",
        "rule": "service_loss_keyword_v1",
    }


def validate_gate(raw: str) -> dict:
    """Reject ambiguous gate decisions and evidence kinds outside a small enum."""
    value = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    if not isinstance(value, dict) or set(value) != {
        "escalate",
        "priority",
        "reason",
        "evidence_kinds",
    }:
        raise ValueError("Nano gate must have exactly four fields")
    if not isinstance(value["escalate"], bool) or value["priority"] not in {"review", "routine"}:
        raise ValueError("invalid gate decision")
    if not isinstance(value["reason"], str) or len(value["reason"]) > 180:
        raise ValueError("invalid gate reason")
    ids = value["evidence_kinds"]
    if (
        not isinstance(ids, list)
        or not ids
        or any(
            not isinstance(item, str) or item not in {"customer_report", "measurements"}
            for item in ids
        )
    ):
        raise ValueError("unknown or missing evidence kind")
    if value["escalate"] != (value["priority"] == "review"):
        raise ValueError("priority conflicts with gate decision")
    return value


def nano_gate(
    replay: dict, key: str | None, *, backend: str = "ollama", model: str = NANO_MODEL
) -> dict:
    summary = measurement_summary(replay)
    visible = {
        "decision_time": replay["decision_time"],
        "customer_report": {
            "problem": replay["current_report"]["problem"],
            "source_id": replay["current_report"]["source_id"],
        },
        "measurements": {
            "source_id": summary["source_id"],
            "samples": summary["samples"],
            "last_sample_time": summary["last_sample_time"],
            "supply_setpoint_gap": summary[
                "secondary_heating_supply_vs_setpoint_absolute_gap_celsius"
            ],
        },
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a narrow read-only triage gate. Decide whether a human investigator should review this incident. "
                "A service-loss report warrants review even when one sensor tracks a target. Do not diagnose a root cause, "
                "invent a sensor, or use information after decision_time. Reply ONLY as JSON with exactly keys "
                "escalate (boolean), priority ('review' if escalate, else 'routine'), reason (one short sentence), "
                "evidence_kinds (list containing only 'customer_report' and/or 'measurements')."
            ),
        },
        {"role": "user", "content": json.dumps(visible, ensure_ascii=False)},
    ]
    choice, latency = call_model(messages, key, backend=backend, model=model, tools=None)
    raw = choice["message"].get("content") or ""
    try:
        decision = validate_gate(raw)
        status = "valid"
    except (ValueError, json.JSONDecodeError) as error:
        decision = {
            "escalate": True,
            "priority": "review",
            "reason": "Gate output invalid; conservative human review",
            "evidence_kinds": ["customer_report"],
        }
        status = f"fallback:{type(error).__name__}"
    evidence_map = {
        "customer_report": replay["current_report"]["source_id"],
        "measurements": summary["source_id"],
    }
    decision["source_ids"] = [evidence_map[kind] for kind in decision["evidence_kinds"]]
    rule = rules_gate(replay)
    effective_decision = decision.copy()
    if rule["escalate"] and not decision["escalate"]:
        effective_decision = {
            "escalate": True,
            "priority": "review",
            "reason": "Service-loss report requires human review; safety routing override",
            "evidence_kinds": ["customer_report"],
            "source_ids": [replay["current_report"]["source_id"]],
        }
        status += ";service_loss_override"
    return {
        "model": model,
        "schema_version": 2,
        "backend": backend,
        "input": visible,
        "decision": decision,
        "effective_decision": effective_decision,
        "validation_status": status,
        "latency_seconds": latency,
        "raw": raw,
    }


def run_case(
    replay: dict,
    *,
    backend: str = "nvidia",
    model: str = ULTRA_MODEL,
    key: str | None = None,
    triage: dict | None = None,
) -> dict:
    """Run one held-out replay; all reads are scoped to the supplied public case."""
    gate_text = ""
    if triage:
        gate_text = "Nano triage (routing only; not a diagnosis): " + json.dumps(
            triage["decision"], ensure_ascii=False
        )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a read-only district-heating investigator. Provide a next safe data check, not final root cause. "
                "Call get_recent_measurements and get_prior_incidents before answering. Other available tools: "
                "get_maintenance_timeline and get_signal_definitions. Distinguish sensor supply temperature from heat at rooms. "
                "s_ is SECONDARY, p_ is PRIMARY, DHW is domestic hot water. Never treat primary meter flow as customer-side flow. "
                "The 2 C tracking gap compares secondary supply with its setpoint only. No normal power/flow range is given. "
                "Do not invent tag names. For missing readings, use plain-language descriptions. No component failure or control change "
                "without evidence. Avoid naming speculative component failure modes, including fouling or bypass, even in uncertainty. "
                "Do not call a series a rising or falling trend unless you state supported first and last values. "
                "Cite exact source IDs. Earlier reports do not prove the current cause. "
                "Answer in Korean: observed evidence, limits, two or three human checks, uncertainty."
            ),
        },
        {
            "role": "user",
            "content": (
                f"At {replay['decision_time']}, asset {replay['asset']['substation_id']} received published report "
                f"'{replay['current_report']['problem']}' (source {replay['current_report']['source_id']}). "
                "Use only information available by then. What should a human engineer check next? "
                + gate_text
            ),
        },
    ]
    events = []
    for step in range(6):
        choice, latency = call_model(messages, key, backend=backend, model=model, tools=TOOLS)
        message = choice["message"]
        calls = message.get("tool_calls") or []
        events.append(
            {
                "step": step + 1,
                "latency_seconds": latency,
                "finish_reason": choice.get("finish_reason"),
                "model_content": message.get("content"),
                "tool_calls": [call.get("function", {}).get("name") for call in calls],
            }
        )
        if not calls:
            final = message.get("content") or ""
            break
        messages.append(message)
        for call_index, call in enumerate(calls, 1):
            name = call["function"]["name"]
            result = (
                run_tool(name, replay)
                if name in {tool["function"]["name"] for tool in TOOLS}
                else {"error": "unknown tool"}
            )
            call_id = call.get("id", f"local-{step + 1}-{call_index}")
            events.append({"tool": name, "call_id": call_id, "result": result})
            if backend == "ollama":
                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            else:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
    else:
        raise RuntimeError("model exceeded six tool rounds")
    known_names = set(replay["features"])
    invalid_tags = undefined_signal_names(final, known_names)
    unsupported_claims = unsupported_certainty_markers(final)
    if invalid_tags or unsupported_claims:
        messages.extend(
            [
                {"role": "assistant", "content": final},
                {
                    "role": "user",
                    "content": (
                        "Your answer needs a factual repair. Unavailable sensor tags: "
                        + ", ".join(invalid_tags)
                        + ". Unsupported certainty phrases: "
                        + ", ".join(unsupported_claims)
                        + ". Rewrite the same evidence and next checks, using plain-language descriptions for unavailable readings. "
                        "Do not localize a likely component failure from this evidence. Do not add new facts."
                    ),
                },
            ]
        )
        corrected, latency = call_model(messages, key, backend=backend, model=model, tools=None)
        candidate = corrected["message"].get("content") or ""
        candidate_invalid = undefined_signal_names(candidate, known_names)
        candidate_claims = unsupported_certainty_markers(candidate)
        events.append(
            {
                "output_repair": {
                    "latency_seconds": latency,
                    "original_invalid_tags": invalid_tags,
                    "remaining_invalid_tags": candidate_invalid,
                    "original_unsupported_claims": unsupported_claims,
                    "remaining_unsupported_claims": candidate_claims,
                }
            }
        )
        if candidate and not candidate_invalid and not candidate_claims:
            final = candidate
        else:
            final = "근거 검토 필요: 모델 답변에 공개 자료에 없는 센서 태그가 포함되어 엔지니어 확인 전까지 권고를 보류합니다."
    return {
        "backend": backend,
        "model": model,
        "case_id": replay["case_id"],
        "source": replay["source"],
        "decision_time": replay["decision_time"],
        "triage": triage,
        "events": events,
        "final": final,
        "undefined_signal_names": undefined_signal_names(final, known_names),
        "note": "Held-out current diagnosis and remedy were not supplied to either model.",
    }


def run(
    replay_path: str | Path,
    *,
    model: str = ULTRA_MODEL,
    backend: str = "nvidia",
    key: str | None = None,
    mode: str = "pipeline",
    nano_backend: str = "ollama",
    nano_model: str = NANO_MODEL,
) -> dict:
    replay = json.loads(Path(replay_path).read_text())
    rule = rules_gate(replay)
    if mode == "ultra":
        result = run_case(replay, backend=backend, model=model, key=key)
    elif mode == "pipeline":
        gate = nano_gate(
            replay,
            key if nano_backend == "nvidia" else None,
            backend=nano_backend,
            model=nano_model,
        )
        result = (
            run_case(replay, backend=backend, model=model, key=key, triage=gate)
            if gate["effective_decision"]["escalate"]
            else {
                "backend": backend,
                "model": model,
                "case_id": replay["case_id"],
                "source": replay["source"],
                "decision_time": replay["decision_time"],
                "triage": gate,
                "events": [],
                "final": None,
                "undefined_signal_names": [],
                "note": "Nano did not escalate; no Ultra call made.",
            }
        )
    else:
        raise ValueError(f"unknown mode: {mode}")
    result["rules_baseline"] = rule
    return result


def save_trace(trace: dict, output_dir: str | Path) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%S%fZ")
    slug = re.sub(r"[^A-Za-z0-9-]+", "-", trace["case_id"])
    path = directory / f"trace-{slug}-{stamp}-{uuid.uuid4().hex[:8]}.json"
    with path.open("x") as file:
        json.dump(trace, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, default=ROOT / "data/replay-52.json")
    parser.add_argument("--mode", choices=("pipeline", "ultra"), default="pipeline")
    parser.add_argument("--backend", choices=("nvidia", "ollama"), default=BACKEND)
    parser.add_argument("--model", default=None, help="Ultra/investigator model ID")
    parser.add_argument("--nano-backend", choices=("nvidia", "ollama"), default="ollama")
    parser.add_argument("--nano-model", default=NANO_MODEL)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".artifacts/poc-runs")
    args = parser.parse_args()
    key = load_key(ROOT / ".env") if args.backend == "nvidia" else None
    model = args.model or ("nemotron-3-nano:4b" if args.backend == "ollama" else MODEL)
    trace = run(
        args.replay,
        model=model,
        backend=args.backend,
        key=key,
        mode=args.mode,
        nano_backend=args.nano_backend,
        nano_model=args.nano_model,
    )
    path = save_trace(trace, args.output_dir)
    print(
        json.dumps(
            {
                "trace": str(path),
                "case_id": trace["case_id"],
                "gate": trace["triage"]["decision"] if trace["triage"] else None,
                "rules_baseline": trace["rules_baseline"],
                "tool_calls": [event["tool"] for event in trace["events"] if "tool" in event],
                "undefined_signal_names": trace["undefined_signal_names"],
                "final": trace["final"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
