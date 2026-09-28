"""Live read-only System 2 investigation ending in a native-schema check plan."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from poc.constrained_composer import assemble_selection, plan_schema
from poc.evidence_contract import (
    CHECKS,
    LIMITS,
    SOURCE_TOOLS,
    build_evidence,
    finalize_selection,
    source_manifest,
    withheld_display,
)
from poc.run import ENDPOINT, NVIDIA_PACER, ULTRA_MODEL, run_tool
from poc.temporal_tools import (
    permitted_window_fields,
    query_window,
    temporal_episodes,
    temporal_facts,
    validate_public_replay,
    window_facts,
)

TEMPORAL_TOOLS = ("get_temporal_episodes", "query_measurement_window")
FINISH_TOOL = "finish_investigation"
HANDOFF_POLICIES = ("explicit_finish_v1", "bounded_finalize_v2")
READ_BACKENDS = ("direct", "nat")
TIME_OF_DAY_PATTERN = re.compile(r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)")
QUANTITY_PATTERN = re.compile(
    r"(?<![\w:])~?(\d+(?:\.\d+)?)(?:\s*[-–]\s*(\d+(?:\.\d+)?))?"
    r"\s*(°\s*C|kWh|kW|l/h|%|samples?)(?!\w)",
    re.IGNORECASE,
)
LIVE_TASK = (
    "Given this asset's reported problem at decision_time, inspect the available public "
    "evidence at or before that time and propose a plan with only limit_ids and next_checks. "
    "Select 2 or 3 distinct checks. For each check, cite 1 to 4 distinct retrieved supporting "
    "fact IDs and write a nonblank rationale of at most 240 characters. The program derives "
    "displayed observations as the ordered union of supporting fact IDs (at most 12); do not "
    "write observed_fact_ids. Select only supplied limit and check IDs. Ground temporal claims "
    "in timestamped readings or explicit first/last samples; minimum and maximum summaries "
    "are not start/end readings. Do not claim a cause or operational fault from descriptive "
    "temperature gaps, and do not recommend changing controls. Return one plan JSON object."
)


def live_source_manifest(
    read_names: set[str] | None = None, *, temporal_enabled: bool = True
) -> dict:
    """Advertise every permitted reader and its actual read state."""
    read_names = read_names or set()
    manifest = source_manifest(read_names)
    if temporal_enabled:
        manifest["available_sources"].extend(
            [
                {
                    "reader": "get_temporal_episodes",
                    "file": "temporal/episodes.json",
                    "read_state": "read" if "get_temporal_episodes" in read_names else "unread",
                },
                {
                    "reader": "query_measurement_window",
                    "file": "temporal/window-fields.json",
                    "read_state": "read" if "query_measurement_window" in read_names else "unread",
                    "max_rows_per_query": 24,
                },
            ]
        )
    return manifest


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _evidence_with_facts(base: dict, facts: list[dict]) -> dict:
    evidence = {**base, "sources": list(base["sources"]), "facts": list(base["facts"])}
    known = {fact["id"] for fact in evidence["facts"]}
    for fact in facts:
        if fact["id"] not in known:
            evidence["facts"].append(fact)
            known.add(fact["id"])
        if fact["source_id"] not in {source["id"] for source in evidence["sources"]}:
            evidence["sources"].append({"id": fact["source_id"], "kind": "retrieved_public_source"})
    evidence["sources"].sort(key=lambda source: source["id"])
    evidence["facts"].sort(key=lambda fact: (fact["source_id"], fact["source_field"], fact["id"]))
    return evidence


def build_live_bundle(replay: dict, temporal_enabled: bool = True) -> dict:
    """Shared permitted corpus for both live comparators; no hidden outcomes or paths."""
    validate_public_replay(replay)
    tool_results = {name: run_tool(name, replay) for name in SOURCE_TOOLS}
    evidence = build_evidence(replay, tool_results)
    report_id = replay["current_report"]["source_id"]
    report_facts = [
        fact for fact in build_evidence(replay)["facts"] if fact["source_id"] == report_id
    ]
    visible_case = {
        "case_id": replay["case_id"],
        "asset": replay["asset"],
        "decision_time": replay["decision_time"],
        "current_report": replay["current_report"],
        "report_facts": report_facts,
        "measurement_window": {
            field: replay["measurement_window"][field] for field in ("start", "end", "source_id")
        },
        "source": replay["source"],
    }
    objects = {
        "case.json": visible_case,
        "source_manifest.json": live_source_manifest(temporal_enabled=temporal_enabled),
    }
    for name, result in tool_results.items():
        source_facts = build_evidence(replay, {name: result})["facts"]
        objects[f"tools/{name}.json"] = {
            "result": result,
            "facts": [fact for fact in source_facts if fact["source_id"] != report_id],
        }
    if temporal_enabled:
        episodes = temporal_episodes(replay)
        raw_window = permitted_window_fields(replay)
        evidence = _evidence_with_facts(
            evidence,
            temporal_facts(replay, episodes) + window_facts(raw_window),
        )
        objects["temporal/episodes.json"] = {
            "result": episodes,
            "facts": temporal_facts(replay, episodes),
        }
        objects["temporal/window-fields.json"] = {
            "result": raw_window,
            "facts": window_facts(raw_window),
        }
    schema = plan_schema(evidence)
    objects["fact_catalog.json"] = evidence
    objects["plan_schema.json"] = schema
    objects["task.json"] = {
        "task": LIVE_TASK,
        "plan_policy": (
            "Select 2 or 3 distinct checks, each supported by 1 to 4 retrieved fact IDs. "
            "The program derives displayed observations as the ordered union of these IDs "
            "(at most 12). Rationales are suggestions, not observed facts or causal findings."
        ),
        "limits_catalog": LIMITS,
        "checks_catalog": CHECKS,
    }
    files = {name: _json(value) for name, value in sorted(objects.items())}
    corpus = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "contract_version": 2,
        "task": LIVE_TASK,
        "schema": schema,
        "evidence": evidence,
        "files": files,
        "file_sha256": {
            name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()
        },
        "corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "temporal_enabled": temporal_enabled,
    }


def _tool_specs(temporal_enabled: bool) -> list[dict]:
    specs = []
    for name in SOURCE_TOOLS:
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Read the public {name} source for this case.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            }
        )
    if temporal_enabled:
        specs.extend(
            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_temporal_episodes",
                        "description": "Read pre-decision paired supply/setpoint episodes and exact endpoints.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "query_measurement_window",
                        "description": "Read at most 24 public measurement rows in an inclusive ISO timestamp window within the decision cutoff.",
                        "parameters": {
                            "type": "object",
                            "properties": {"start": {"type": "string"}, "end": {"type": "string"}},
                            "required": ["start", "end"],
                            "additionalProperties": False,
                        },
                    },
                },
            ]
        )
    specs.append(
        {
            "type": "function",
            "function": {
                "name": FINISH_TOOL,
                "description": "Finish reading sources and proceed to a separate native-schema final plan.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        }
    )
    return specs


def _read_tool(
    replay: dict, name: str, args: dict, temporal_enabled: bool
) -> tuple[dict, list[dict]]:
    if name in SOURCE_TOOLS:
        if args:
            raise ValueError(f"{name} requires empty arguments")
        result = run_tool(name, replay)
        facts = build_evidence(replay, {name: result})["facts"]
        report_id = replay["current_report"]["source_id"]
        return result, [fact for fact in facts if fact["source_id"] != report_id]
    if not temporal_enabled:
        raise ValueError("temporal tools are disabled")
    if name == "get_temporal_episodes":
        if args:
            raise ValueError("get_temporal_episodes requires empty arguments")
        result = temporal_episodes(replay)
        return result, temporal_facts(replay, result)
    if name == "query_measurement_window":
        if set(args) != {"start", "end"}:
            raise ValueError("query_measurement_window requires start and end only")
        result = query_window(replay, start=args["start"], end=args["end"])
        return result, window_facts(result)
    raise ValueError(f"unknown tool: {name}")


def _nvidia_request(payload: dict, key: str) -> tuple[dict, float]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    NVIDIA_PACER.wait()
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"NVIDIA API HTTP {error.code}") from error
    return body, round(time.monotonic() - started, 3)


def _numeric_values(value: object) -> list[float]:
    if type(value) in (int, float):
        return [float(value)]
    if isinstance(value, dict):
        return [number for child in value.values() for number in _numeric_values(child)]
    if isinstance(value, list):
        return [number for child in value for number in _numeric_values(child)]
    return []


def temporal_review_flags(plan: dict, evidence: dict) -> list[dict]:
    """Heuristic human review only; never changes the model's rationale or score."""
    facts = {fact["id"]: fact for fact in evidence["facts"]}
    flags = []
    trend_words = (
        "rising",
        "rose",
        "increasing",
        "falling",
        "fell",
        "decreasing",
        "trend",
        "상승",
        "하락",
        "증가",
        "감소",
    )
    for check in plan["next_checks"]:
        rationale = check["rationale"].lower()
        cited = [facts[fact_id] for fact_id in check["because_fact_ids"]]
        rationale_times = set(TIME_OF_DAY_PATTERN.findall(rationale))
        cited_text = json.dumps(
            [
                {
                    "text": fact.get("text"),
                    "value": fact.get("value"),
                    "interval": fact.get("interval"),
                }
                for fact in cited
            ],
            ensure_ascii=False,
        )
        cited_times = set(TIME_OF_DAY_PATTERN.findall(cited_text))
        unsupported_times = sorted(rationale_times - cited_times)
        if unsupported_times:
            flags.append(
                {
                    "code": "rationale_time_not_in_cited_facts",
                    "severity": "human_review",
                    "check_id": check["id"],
                    "fact_ids": check["because_fact_ids"],
                    "times": unsupported_times,
                }
            )
        cited_numbers = [number for fact in cited for number in _numeric_values(fact.get("value"))]
        unsupported_quantities = []
        for match in QUANTITY_PATTERN.finditer(rationale):
            for claimed_number in (match.group(1), match.group(2)):
                if claimed_number is None:
                    continue
                claim = float(claimed_number)
                decimals = len(claimed_number.partition(".")[2])
                tolerance = 0.5 * 10**-decimals + 1e-9
                if not any(abs(claim - value) <= tolerance for value in cited_numbers):
                    unsupported_quantities.append(f"{claimed_number} {match.group(3).lower()}")
        if unsupported_quantities:
            flags.append(
                {
                    "code": "rationale_quantity_not_in_cited_facts",
                    "severity": "human_review",
                    "check_id": check["id"],
                    "fact_ids": check["because_fact_ids"],
                    "quantities": unsupported_quantities,
                    "note": "Numeric match is heuristic; it does not verify sensor, unit, or claim meaning.",
                }
            )
        if (
            any(word in rationale for word in trend_words)
            and cited
            and all(fact["source_field"].endswith((".min", ".max", ".last")) for fact in cited)
        ):
            flags.append(
                {
                    "code": "summary_stat_may_be_read_as_full_window_trend",
                    "severity": "human_review",
                    "check_id": check["id"],
                    "fact_ids": check["because_fact_ids"],
                }
            )
    return flags


def run_live_case(
    replay: dict,
    *,
    bundle: dict | None = None,
    key: str,
    model: str = ULTRA_MODEL,
    temporal_enabled: bool = True,
    max_planning_requests: int = 6,
    handoff_policy: str = "explicit_finish_v1",
    read_backend: str = "direct",
) -> dict:
    """Run at most six planner requests plus one final native-schema request."""
    if not key:
        raise ValueError("NVIDIA key is required")
    if not 1 <= max_planning_requests <= 6:
        raise ValueError("planning request limit must be between 1 and 6")
    if handoff_policy not in HANDOFF_POLICIES:
        raise ValueError("unknown handoff policy")
    if read_backend not in READ_BACKENDS:
        raise ValueError("unknown read backend")
    validate_public_replay(replay)
    reader = None
    if read_backend == "nat":
        from integrations.live_nat_adapter import NatLiveReader

        reader = NatLiveReader()
    bundle = bundle or build_live_bundle(replay, temporal_enabled=temporal_enabled)
    if (
        bundle["temporal_enabled"] != temporal_enabled
        or bundle["evidence"]["case_id"] != replay["case_id"]
    ):
        raise ValueError("live bundle does not match requested case and temporal policy")
    started = time.monotonic()
    trace = {
        "method": (
            "live-system2-plan-first-handoff-v2"
            if handoff_policy == "bounded_finalize_v2"
            else "live-system2-plan-first-v1"
        ),
        "case_id": replay["case_id"],
        "model": model,
        "corpus_sha256": bundle["corpus_sha256"],
        "file_sha256": bundle["file_sha256"],
        "temporal_enabled": temporal_enabled,
        "read_backend": read_backend,
        "nat_version": reader.version if reader else None,
        "planner_requests": [],
        "tool_calls": [],
        "finish_reason": None,
        "source_read_state": live_source_manifest(temporal_enabled=temporal_enabled),
        "temporal_read_state": {name: False for name in TEMPORAL_TOOLS},
        "evidence": None,
        "native_schema": None,
        "final_request": None,
        "final_response": None,
        "raw_plan": None,
        "parsed_plan": None,
        "assembled_selection": None,
        "derived_observations": None,
        "validation": None,
        "review_flags": [],
        "display": withheld_display("run not completed"),
        "completeness": {"status": "not_assessed", "issues": []},
        "usage": [],
        "request_seconds": 0.0,
        "wall_seconds": None,
    }
    if handoff_policy == "bounded_finalize_v2":
        trace["handoff_policy"] = handoff_policy
        trace["investigation_budget_exhausted"] = False
        trace["review_notes"] = []
    evidence = build_evidence(replay)
    read_names: set[str] = set()
    completed_read_turns = 0
    messages = [
        {
            "role": "system",
            "content": (
                "You are a read-only plant investigator. Use tools to inspect the public case. "
                "Read relevant sources, including temporal episodes and a bounded raw window "
                "when making time or trend claims. Do not infer cause, fault status, or control "
                "action from gaps alone. Call finish_investigation when ready. Do not write a "
                "final plan during this stage."
            ),
        },
        {
            "role": "user",
            "content": _json(
                {
                    "task": LIVE_TASK,
                    "case": json.loads(bundle["files"]["case.json"]),
                    "available_tools": [
                        tool["function"]["name"] for tool in _tool_specs(temporal_enabled)
                    ],
                }
            ),
        },
    ]
    try:
        for index in range(max_planning_requests):
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 1200,
                "chat_template_kwargs": {"enable_thinking": False},
                "stream": False,
                "tools": _tool_specs(temporal_enabled),
                "tool_choice": "auto",
            }
            request_snapshot = copy.deepcopy(payload)
            body, elapsed = _nvidia_request(payload, key)
            trace["request_seconds"] += elapsed
            trace["usage"].append(body.get("usage"))
            choice = body["choices"][0]
            message = choice["message"]
            calls = message.get("tool_calls") or []
            trace["planner_requests"].append(
                {
                    "request_index": index + 1,
                    "request": request_snapshot,
                    "response": body,
                    "latency_seconds": elapsed,
                }
            )
            if not calls:
                trace["finish_reason"] = "planner_stopped_without_tool"
                break
            messages.append(message)
            done = False
            read_this_turn = False
            for call_index, call in enumerate(calls, 1):
                function = call.get("function") or {}
                name = function.get("name")
                raw_args = function.get("arguments") or "{}"
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                if not isinstance(args, dict):
                    raise ValueError("tool arguments must be an object")
                if done:
                    raise ValueError("tool call after finish_investigation")
                if name == FINISH_TOOL:
                    if args:
                        raise ValueError("finish_investigation requires empty arguments")
                    result, new_facts = {"status": "finished"}, []
                    done = True
                    trace["finish_reason"] = "explicit_finish_tool"
                else:
                    result, new_facts = (
                        reader.read(replay, name, args, temporal_enabled)
                        if reader
                        else _read_tool(replay, name, args, temporal_enabled)
                    )
                    read_this_turn = True
                    read_names.add(name)
                    evidence = _evidence_with_facts(evidence, new_facts)
                    trace["source_read_state"] = live_source_manifest(
                        read_names, temporal_enabled=temporal_enabled
                    )
                    trace["temporal_read_state"] = {
                        temporal_name: temporal_name in read_names
                        for temporal_name in TEMPORAL_TOOLS
                    }
                call_id = call.get("id") or f"local-{index + 1}-{call_index}"
                tool_response = {
                    "result": result,
                    "facts": new_facts,
                    "source_manifest": live_source_manifest(
                        read_names, temporal_enabled=temporal_enabled
                    ),
                }
                trace["tool_calls"].append(
                    {
                        "name": name,
                        "call_id": call_id,
                        "arguments": args,
                        "response": tool_response,
                        "executor": read_backend,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": _json(tool_response),
                    }
                )
            if read_this_turn:
                completed_read_turns += 1
            if done:
                break
        else:
            trace["finish_reason"] = "planning_request_limit"
        trace["evidence"] = evidence
        report_id = replay["current_report"]["source_id"]
        has_case_evidence = any(fact["source_id"] != report_id for fact in evidence["facts"])
        bounded_handoff = (
            handoff_policy == "bounded_finalize_v2"
            and trace["finish_reason"] == "planning_request_limit"
            and max_planning_requests == 6
            and completed_read_turns == 6
            and has_case_evidence
        )
        if bounded_handoff:
            trace["finish_reason"] = "planning_cap_handoff"
            trace["investigation_budget_exhausted"] = True
            trace["review_notes"].append(
                "Native final plan requested after six valid read turns reached the planning cap; "
                "the investigator did not explicitly finish or attest sufficiency."
            )
        if trace["finish_reason"] not in {"explicit_finish_tool", "planning_cap_handoff"}:
            raise ValueError(f"planning stopped: {trace['finish_reason']}")
        schema = bundle["schema"]
        trace["native_schema"] = schema
        final_payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Select a grounded check plan from retrieved facts only. Rationales are "
                        "suggestions, not observed facts or causal findings. Return only JSON "
                        "matching the native schema."
                    ),
                },
                {
                    "role": "user",
                    "content": _json(
                        {
                            "task": LIVE_TASK,
                            "evidence": evidence,
                            "limits_catalog": LIMITS,
                            "checks_catalog": CHECKS,
                            "source_manifest": live_source_manifest(
                                read_names, temporal_enabled=temporal_enabled
                            ),
                            "temporal_read_state": {
                                name: name in read_names for name in TEMPORAL_TOOLS
                            },
                            "plan_schema": schema,
                            **({"investigation_budget_exhausted": True} if bounded_handoff else {}),
                        }
                    ),
                },
            ],
            "temperature": 0,
            "max_tokens": 1200,
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "grounded_check_plan", "strict": True, "schema": schema},
            },
        }
        trace["final_request"] = final_payload
        body, elapsed = _nvidia_request(final_payload, key)
        trace["request_seconds"] += elapsed
        trace["usage"].append(body.get("usage"))
        trace["final_response"] = body
        raw = body["choices"][0]["message"].get("content") or ""
        trace["raw_plan"] = raw
        plan, selection = assemble_selection(raw, evidence)
        trace["parsed_plan"] = plan
        trace["assembled_selection"] = selection
        trace["derived_observations"] = [
            fact for fact in evidence["facts"] if fact["id"] in selection["observed_fact_ids"]
        ]
        trace["validation"] = {"status": "valid", "selection": selection}
        trace["review_flags"] = temporal_review_flags(plan, evidence)
        trace["display"], trace["completeness"] = finalize_selection(
            selection, evidence, read_names=read_names, contract_version=2
        )
    except (
        ValueError,
        KeyError,
        TypeError,
        RuntimeError,
        urllib.error.URLError,
        TimeoutError,
    ) as error:
        trace["evidence"] = evidence
        trace["validation"] = {
            "status": "invalid",
            "error_type": type(error).__name__,
            "reason": str(error),
        }
        trace["display"] = withheld_display(str(error))
    trace["wall_seconds"] = round(time.monotonic() - started, 3)
    return trace


def main() -> None:
    """Run one public replay without changing the frozen comparison protocol."""
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="JSON filename under data/")
    parser.add_argument("--output", required=True, type=Path, help="new trace JSON path")
    parser.add_argument("--read-backend", choices=READ_BACKENDS, default="direct")
    parser.add_argument("--handoff-policy", choices=HANDOFF_POLICIES, required=True)
    parser.add_argument("--max-planning-requests", type=int, default=6)
    parser.add_argument("--no-temporal", action="store_true")
    parser.add_argument("--model", default=ULTRA_MODEL)
    args = parser.parse_args()
    case_path = (root / "data" / args.case).resolve()
    if case_path.parent != root / "data" or case_path.suffix != ".json":
        parser.error("--case must name a JSON file directly under data/")
    if args.output.exists():
        parser.error("--output already exists; choose a new trace path")
    if args.output.resolve().is_relative_to(root / "evaluation" / "cycle4"):
        parser.error("--output cannot write into frozen cycle4 artifacts")
    replay = json.loads(case_path.read_text())
    temporal_enabled = not args.no_temporal
    bundle = build_live_bundle(replay, temporal_enabled=temporal_enabled)
    from scripts.check_nvidia import load_key

    key = load_key(root / ".env")
    trace = run_live_case(
        replay,
        bundle=bundle,
        key=key,
        model=args.model,
        temporal_enabled=temporal_enabled,
        max_planning_requests=args.max_planning_requests,
        handoff_policy=args.handoff_policy,
        read_backend=args.read_backend,
    )
    trace["run_context"] = {
        "kind": "development_integration_smoke",
        "input_file": f"data/{case_path.name}",
        "input_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
        "scope": "Independent live run; not part of frozen cycle4 comparison",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(_json(trace))
    print(
        _json(
            {
                "output": str(args.output),
                "case_id": replay["case_id"],
                "display_status": trace["display"]["status"],
                "finish_reason": trace["finish_reason"],
                "read_backend": args.read_backend,
                "review_flag_count": len(trace["review_flags"]),
            }
        ),
        end="",
    )


if __name__ == "__main__":
    main()
