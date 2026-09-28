"""Run a read-only Nemotron investigation of the public PreDist replay."""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_nvidia import load_key  # noqa: E402


BACKEND = os.environ.get("POC_BACKEND", "nvidia")
DEFAULT_MODEL = "nemotron-3-nano:4b" if BACKEND == "ollama" else "nvidia/nemotron-3.5-lightning-30b-a3b"
MODEL = os.environ.get("NVIDIA_MODEL", DEFAULT_MODEL)
ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
REPLAY = json.loads((ROOT / "data/replay-52.json").read_text())
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_measurements",
            "description": "Read the last 24 hours of actual public measurements and setpoints for this substation. Returns cited numeric summaries, not a diagnosis.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_prior_incidents",
            "description": "Read earlier published incident reports for this same substation. The current report's diagnosis and remedy are withheld.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_maintenance_timeline",
            "description": "Read earlier maintenance and incident timestamps for this same substation. Tasks and activities have no narrative or confirmed completion outcome.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_signal_definitions",
            "description": "Explain public sensor names and units; useful before interpreting measured versus target temperatures.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]


def measurement_summary() -> dict:
    rows = REPLAY["measurement_window"]["rows"]
    source_id = REPLAY["measurement_window"]["source_id"]
    signals = {
        "outdoor_temperature_c": "outdoor_temperature",
        "secondary_heating_circuit_supply_temperature_c": "s_hc1_supply_temperature",
        "secondary_heating_circuit_supply_setpoint_c": "s_hc1_supply_temperature_setpoint",
        "primary_network_meter_heat_power_kw": "p_net_meter_heat_power",
        "primary_network_meter_flow_l_per_hour": "p_net_meter_flow",
    }
    summary = {}
    for readable_name, raw_name in signals.items():
        values = [row[raw_name] for row in rows if row[raw_name] is not None]
        summary[readable_name] = {
            "original_field": raw_name,
            "first": round(values[0], 2) if values else None,
            "last": round(values[-1], 2) if values else None,
            "min": round(min(values), 2) if values else None,
            "max": round(max(values), 2) if values else None,
            "mean": round(statistics.mean(values), 2) if values else None,
            "unit": REPLAY["features"].get(raw_name, {}).get("unit", ""),
        }
    gaps = [
        abs(row["s_hc1_supply_temperature"] - row["s_hc1_supply_temperature_setpoint"])
        for row in rows
        if row["s_hc1_supply_temperature"] is not None
        and row["s_hc1_supply_temperature_setpoint"] is not None
    ]
    return {
        "source_id": source_id,
        "interval": REPLAY["measurement_window"]["start"] + " to " + REPLAY["measurement_window"]["end"],
        "samples": len(rows),
        "last_sample_time": rows[-1]["timestamp"],
        "signals": summary,
        "secondary_heating_supply_vs_setpoint_absolute_gap_celsius": {
            "mean": round(statistics.mean(gaps), 2),
            "max": round(max(gaps), 2),
            "samples_within_2C": sum(gap <= 2 for gap in gaps),
            "sample_count": len(gaps),
        },
        "interpretation_limits": [
            "The measured secondary heating-circuit supply temperature tracks its setpoint at this sensor location; this alone does not prove heat reached the customer's rooms.",
            "No room/radiator temperature, secondary heat-circuit flow, valve position, or timestamped controller parameter-change record is available in this replay.",
            "p_net_meter_flow is primary network-side flow, not measured customer/secondary heating-circuit flow.",
            "No normal operating range is provided for heat power or flow; do not label either normal or abnormal from these values alone.",
        ],
    }


def run_tool(name: str) -> dict:
    if name == "get_recent_measurements":
        return measurement_summary()
    if name == "get_prior_incidents":
        return {"records": REPLAY["prior_faults"], "note": "Only reports dated before the current report are available."}
    if name == "get_maintenance_timeline":
        return {"records": REPLAY["prior_disturbances"], "note": "Activity timestamps do not provide action details or proof of resolution."}
    if name == "get_signal_definitions":
        return {"definitions": {
            "s_hc1_supply_temperature": "SECONDARY-side heating circuit 1 supply (flow) temperature, °C",
            "s_hc1_supply_temperature_setpoint": "SECONDARY-side heating circuit 1 supply temperature setpoint, °C",
            "p_net_meter_heat_power": "PRIMARY network-side meter heat power, kW; no normal range provided",
            "p_net_meter_flow": "PRIMARY network-side meter flow, l/h; not secondary/customer flow",
            "outdoor_temperature": "Outside air temperature, °C",
            "s_dhw_supply_temperature": "Domestic hot water circuit supply; different from the space-heating circuit",
        }}
    raise ValueError(f"unknown tool: {name}")


def call_model(messages: list[dict], key: str | None) -> tuple[dict, float]:
    if BACKEND == "ollama":
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "think": False,
            "options": {"temperature": 0},
            "stream": False,
        }
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
        )
        start = time.monotonic()
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        return {"message": result["message"], "finish_reason": result.get("done_reason")}, round(time.monotonic() - start, 2)
    if BACKEND != "nvidia" or key is None:
        raise RuntimeError(f"unsupported backend or missing key: {BACKEND}")
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": 1200,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"NVIDIA API HTTP {error.code}: {error.read(500).decode(errors='replace')}") from error
    return result["choices"][0], round(time.monotonic() - start, 2)


def main() -> None:
    key = load_key(ROOT / ".env") if BACKEND == "nvidia" else None
    messages = [
        {
            "role": "system",
            "content": (
                "You are a read-only district-heating investigation assistant. The user asks for the next safe data check, not a final root cause. "
                "Only these four exact tool names exist: get_recent_measurements, get_prior_incidents, get_maintenance_timeline, get_signal_definitions. "
                "Before answering, call get_recent_measurements and get_prior_incidents, then any other tool that helps. "
                "Distinguish measured temperatures from actual heat at the customer. Do not infer a specific component failure, heat exchanger fouling, or normal operating status without direct evidence. "
                "The prefix s_ means SECONDARY and p_ means PRIMARY. Do not swap them. DHW is domestic hot water, not space heating. "
                "Never compare supply temperature to outdoor temperature using the 2 C setpoint-tracking threshold; that threshold only compares measured supply with its setpoint. "
                "Do not list unobserved component failures as hypotheses. Limit the final answer to two numeric observations, one historical record, and 2-3 measurements or records to obtain next. "
                "Cite exact source IDs for factual claims. Past reports are evidence, not proof of the present cause. "
                "If evidence conflicts or is insufficient, say what remains unknown. Do not suggest changing controls or operating equipment. "
                "Answer in Korean in four short parts: observed evidence, what the evidence cannot establish, 2-3 next checks for a human engineer, and uncertainty."
            ),
        },
        {
            "role": "user",
            "content": (
                "At 2016-12-12 15:55, district-heating substation 21 received a published customer report of 'no heat' "
                "(source PreDist-M1-fault-52-problem-only). Investigate only information available by that time. "
                "What should a human engineer check next?"
            ),
        },
    ]
    events = []
    finish_reason = None
    for step in range(6):
        choice, latency = call_model(messages, key)
        message = choice["message"]
        finish_reason = choice.get("finish_reason")
        calls = message.get("tool_calls") or []
        events.append({
            "step": step + 1,
            "latency_seconds": latency,
            "finish_reason": finish_reason,
            "model_content": message.get("content"),
            "tool_calls": [call.get("function", {}).get("name") for call in calls],
        })
        if not calls:
            final = message.get("content") or ""
            break
        messages.append(message)
        for call_index, call in enumerate(calls, 1):
            name = call["function"]["name"]
            if name not in {tool["function"]["name"] for tool in TOOLS}:
                result = {"error": "unknown tool", "available_tools": [tool["function"]["name"] for tool in TOOLS]}
            else:
                result = run_tool(name)
            call_id = call.get("id", f"local-{step + 1}-{call_index}")
            events.append({"tool": name, "call_id": call_id, "result": result})
            if BACKEND == "ollama":
                messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result, ensure_ascii=False)})
            else:
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                })
    else:
        raise RuntimeError("model exceeded 6 tool rounds")

    output = {
        "backend": BACKEND,
        "model": MODEL,
        "case_id": REPLAY["case_id"],
        "source": REPLAY["source"],
        "decision_time": REPLAY["decision_time"],
        "finish_reason": finish_reason,
        "events": events,
        "final": final,
        "note": "Held-out current report diagnosis was not read or sent to the model.",
    }
    model_slug = MODEL.rsplit('/', 1)[-1].replace(':', '-')
    output_path = ROOT / f"poc/trace-52-{BACKEND}-{model_slug}.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "trace": str(output_path),
        "tool_calls": [event["tool"] for event in events if "tool" in event],
        "finish_reason": finish_reason,
        "final": final,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
