"""Deterministic, source-bound facts for public replay investigations."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def _fact(
    source_id: str,
    field: str,
    value: Any,
    *,
    interval: str | None = None,
    unit: str = "",
    label: str | None = None,
) -> dict:
    identity = json.dumps([source_id, field, interval, value], ensure_ascii=False, sort_keys=True)
    fact_id = "F-" + hashlib.sha256(identity.encode()).hexdigest()[:12]
    description = label or field
    text = f"{description}: {value}{(' ' + unit) if unit else ''}"
    if interval:
        text += f" ({interval})"
    return {
        "id": fact_id,
        "source_id": source_id,
        "source_field": field,
        "interval": interval,
        "value": value,
        "unit": unit,
        "text": text,
    }


def build_evidence(replay: dict, tool_results: dict[str, dict] | None = None) -> dict:
    """Build immutable facts only from the report and tools actually read."""
    tool_results = tool_results or {}
    facts: list[dict] = []
    sources: dict[str, dict] = {}
    report = replay["current_report"]
    report_id = report["source_id"]
    sources[report_id] = {"id": report_id, "kind": "customer_report"}
    if report.get("problem"):
        facts.append(
            _fact(
                report_id,
                "problem",
                report["problem"],
                interval=replay["decision_time"],
                label="Reported problem",
            )
        )

    measurements = tool_results.get("get_recent_measurements")
    if measurements:
        source_id = measurements["source_id"]
        interval = measurements["interval"]
        sources[source_id] = {"id": source_id, "kind": "measurements"}
        facts.append(
            _fact(
                source_id,
                "samples",
                measurements["samples"],
                interval=interval,
                label="Measurement sample count",
            )
        )
        if measurements.get("last_sample_time"):
            facts.append(
                _fact(
                    source_id,
                    "last_sample_time",
                    measurements["last_sample_time"],
                    interval=interval,
                    label="Last measurement time",
                )
            )
        for name, signal in measurements.get("signals", {}).items():
            field = signal["original_field"]
            for statistic in ("first", "last", "min", "max", "mean"):
                value = signal.get(statistic)
                if value is not None:
                    facts.append(
                        _fact(
                            source_id,
                            f"signals.{field}.{statistic}",
                            value,
                            interval=interval,
                            unit=signal.get("unit", ""),
                            label=f"{name} {statistic}",
                        )
                    )
        gap = measurements.get("secondary_heating_supply_vs_setpoint_absolute_gap_celsius", {})
        for statistic in ("mean", "max", "samples_within_2C", "sample_count"):
            value = gap.get(statistic)
            if value is not None:
                unit = "°C" if statistic in {"mean", "max"} else ""
                facts.append(
                    _fact(
                        source_id,
                        f"supply_setpoint_absolute_gap.{statistic}",
                        value,
                        interval=interval,
                        unit=unit,
                        label=f"Secondary supply/setpoint absolute gap {statistic}",
                    )
                )

    for tool_name, kind, fields in (
        ("get_prior_incidents", "prior_incident", ("report_date", "problem", "event_description")),
        ("get_maintenance_timeline", "maintenance_timeline", ("event_start", "type")),
    ):
        for record in tool_results.get(tool_name, {}).get("records", []):
            source_id = record["source_id"]
            sources[source_id] = {"id": source_id, "kind": kind}
            for field in fields:
                if record.get(field) is not None:
                    facts.append(_fact(source_id, field, record[field], label=field))

    facts.sort(key=lambda item: (item["source_id"], item["source_field"], item["id"]))
    return {
        "schema_version": 1,
        "case_id": replay["case_id"],
        "decision_time": replay["decision_time"],
        "sources": sorted(sources.values(), key=lambda x: x["id"]),
        "facts": facts,
    }


LIMITS = {
    "L-no-room-evidence": "Supply temperature tracking its setpoint does not establish heat delivery to rooms.",
    "L-no-normal-range": "No normal operating range is supplied for heat power or flow.",
    "L-primary-flow": "Primary meter flow is not secondary/customer circuit flow.",
    "L-prior-not-current": "A prior report does not establish the cause of this event.",
    "L-retrospective": "Prior report narratives may not have been available at the decision time.",
}

CHECKS = {
    "C-room-impact": "Verify affected room or radiator temperatures and the scope of the reported heating loss.",
    "C-secondary-flow": "Measure secondary heating circuit flow and compare it with the relevant design or operating range.",
    "C-controls": "Review timestamped controller settings, alarms, and parameter changes with an engineer.",
    "C-sensor": "Confirm sensor identity, calibration, and timestamp alignment before interpreting a trend.",
    "C-maintenance": "Check maintenance records and actual completion evidence for relevant prior work.",
    "C-more-data": "Obtain missing measurements before drawing a causal conclusion.",
}

COMMON_TASK = (
    "Given this asset's reported problem at decision_time, identify what the available "
    "evidence establishes, what remains unknown, and two or three justified next checks "
    "for an engineer. Do not give a final root cause or recommend changing controls. "
    "Use only the supplied public evidence; cite/select the provided fact IDs. "
    "Return the common JSON schema."
)

RESPONSE_SCHEMA = {
    "observed_fact_ids": ["F-..."],
    "limit_ids": ["L-..."],
    "next_checks": [
        {
            "id": "C-...",
            "because_fact_ids": ["F-..."],
            "rationale": "Short model-authored suggestion rationale",
        }
    ],
}

TASK_V2 = (
    COMMON_TASK
    + " Inspect available relevant sources before claiming a measurement or record is absent. "
    "Select 1 to 12 observed facts, exactly 2 or 3 checks, and cite at least one selected "
    "observation fact for each check. Use only IDs from the provided catalogs and do not "
    "repeat a check ID. Keep each model-authored rationale nonblank and at most 240 "
    "characters. Return one JSON object, optionally wrapped in a single ```json fence."
)

SCHEMA_V2 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["observed_fact_ids", "limit_ids", "next_checks"],
    "properties": {
        "observed_fact_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 12,
            "uniqueItems": True,
            "items": {"type": "string", "pattern": "^F-"},
        },
        "limit_ids": {
            "type": "array",
            "uniqueItems": True,
            "items": {"type": "string", "pattern": "^L-"},
        },
        "next_checks": {
            "type": "array",
            "minItems": 2,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "because_fact_ids", "rationale"],
                "properties": {
                    "id": {"type": "string", "pattern": "^C-"},
                    "because_fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string", "pattern": "^F-"},
                    },
                    "rationale": {"type": "string", "minLength": 1, "maxLength": 240},
                },
            },
        },
    },
    "x-contract-rule": "Each because_fact_id must also appear in observed_fact_ids.",
}

SOURCE_TOOLS = (
    "get_recent_measurements",
    "get_prior_incidents",
    "get_maintenance_timeline",
    "get_signal_definitions",
)


def source_manifest(read_names: set[str] | None = None) -> dict:
    read_names = read_names or set()
    return {
        "available_sources": [
            {"reader": name, "read_state": "read" if name in read_names else "unread"}
            for name in SOURCE_TOOLS
        ]
    }


def build_case_bundle(replay: dict, *, contract_version: int = 1) -> dict:
    """Create byte-stable public files for a general-purpose coding-agent comparator."""
    from poc.run import run_tool

    if contract_version not in {1, 2}:
        raise ValueError("unknown contract version")
    tool_results = {name: run_tool(name, replay) for name in SOURCE_TOOLS}
    evidence = build_evidence(replay, tool_results)
    visible_case = {
        "case_id": replay["case_id"],
        "asset": replay["asset"],
        "decision_time": replay["decision_time"],
        "current_report": replay["current_report"],
        "measurement_window": {
            key: replay["measurement_window"][key] for key in ("start", "end", "source_id")
        },
        "source": replay["source"],
    }
    objects = {
        "case.json": visible_case,
        "fact_catalog.json": evidence,
        "response_schema.json": {
            "contract_version": 1,
            "task": COMMON_TASK,
            "response_schema": RESPONSE_SCHEMA,
            "limits_catalog": LIMITS,
            "checks_catalog": CHECKS,
        },
    }
    objects.update({f"tools/{name}.json": value for name, value in tool_results.items()})
    if contract_version == 2:
        objects["response_schema.json"] = {
            "contract_version": 2,
            "task": TASK_V2,
            "response_schema": SCHEMA_V2,
            "limits_catalog": LIMITS,
            "checks_catalog": CHECKS,
        }
        objects["source_manifest.json"] = source_manifest()
    files = {
        name: json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        for name, value in sorted(objects.items())
    }
    corpus = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "contract_version": contract_version,
        "task": TASK_V2 if contract_version == 2 else COMMON_TASK,
        "schema": SCHEMA_V2 if contract_version == 2 else RESPONSE_SCHEMA,
        "files": files,
        "file_sha256": {
            name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()
        },
        "corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "evidence": evidence,
    }


def build_task_packet(
    replay: dict, tool_results: dict[str, dict], *, contract_version: int = 1
) -> dict:
    """The identical task packet to serialize for each packet-mode model."""
    evidence = build_evidence(replay, tool_results)
    packet = {
        "schema_version": 1,
        "question": COMMON_TASK,
        "asset": replay["asset"],
        "evidence": evidence,
        "limits_catalog": LIMITS,
        "checks_catalog": CHECKS,
        "task": COMMON_TASK,
        "response_schema": RESPONSE_SCHEMA,
        "instruction": (
            "Choose only available IDs. Observations are selected source facts, not prose. "
            "Provide at most three checks and a short rationale for each. A rationale is "
            "a suggested reason to check, not an observed fact or causal conclusion. "
            "If evidence is missing, select the missing-data check. Reply with JSON only."
        ),
    }
    if contract_version == 2:
        packet["schema_version"] = 2
        packet["question"] = TASK_V2
        packet["task"] = TASK_V2
        packet["response_schema"] = SCHEMA_V2
        packet["source_manifest"] = source_manifest(set(tool_results))
        packet["instruction"] = TASK_V2
    elif contract_version != 1:
        raise ValueError("unknown contract version")
    return packet


def packet_bytes(packet: dict) -> bytes:
    return json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def normalize_response(raw: str, *, contract_version: int = 1) -> tuple[str, bool]:
    """Only v2 accepts one complete outer JSON code fence, with a recorded normalization."""
    if contract_version == 1:
        return raw, False
    if contract_version != 2:
        raise ValueError("unknown contract version")
    stripped = raw.strip()
    match = re.fullmatch(r"```(?:json)?\s*\n([\s\S]*?)\n```", stripped, re.IGNORECASE)
    return (match.group(1), True) if match else (raw, False)


def validate_selection(raw: str, evidence: dict, *, contract_version: int = 1) -> dict:
    """Validate model selections; never reinterpret authored prose as observed data."""
    normalized, _ = normalize_response(raw, contract_version=contract_version)
    try:
        selection = json.loads(normalized)
    except json.JSONDecodeError as error:
        raise ValueError("output is not JSON") from error
    if not isinstance(selection, dict) or set(selection) != {
        "observed_fact_ids",
        "limit_ids",
        "next_checks",
    }:
        raise ValueError("output schema mismatch")
    choices = {
        "observed_fact_ids": {item["id"] for item in evidence["facts"]},
        "limit_ids": set(LIMITS),
    }
    for field, allowed in choices.items():
        values = selection[field]
        if (
            not isinstance(values, list)
            or any(not isinstance(x, str) for x in values)
            or len(values) != len(set(values))
            or any(x not in allowed for x in values)
        ):
            raise ValueError(f"invalid or unavailable {field}")
    checks = selection["next_checks"]
    if (
        not isinstance(checks, list)
        or len(checks) > 3
        or (contract_version == 2 and len(checks) < 2)
    ):
        raise ValueError("invalid next_checks")
    seen: set[str] = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "because_fact_ids", "rationale"}:
            raise ValueError("next check schema mismatch")
        check_id = check["id"]
        if not isinstance(check_id, str) or check_id not in CHECKS or check_id in seen:
            raise ValueError("invalid next check ID")
        seen.add(check_id)
        refs = check["because_fact_ids"]
        if (
            not isinstance(refs, list)
            or not refs
            or any(not isinstance(x, str) for x in refs)
            or len(refs) != len(set(refs))
            or any(x not in selection["observed_fact_ids"] for x in refs)
        ):
            raise ValueError("invalid supporting fact ID")
        rationale = check["rationale"]
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 240:
            raise ValueError("invalid next check rationale")
        if contract_version == 1 and re.search(r"\b[sp]_[a-z][a-z0-9_]*\b", rationale):
            raise ValueError("raw signal tag in model-authored rationale")
    if len(selection["observed_fact_ids"]) > 12 or (
        contract_version == 2 and not selection["observed_fact_ids"]
    ):
        raise ValueError("selection exceeds display bound")
    return selection


def validation_attempt(raw: str, evidence: dict, *, contract_version: int = 2) -> dict:
    """Record one unmodified candidate and the common contract's exact verdict."""
    _, normalized = normalize_response(raw, contract_version=contract_version)
    attempt = {"raw_output": raw, "outer_fence_normalized": normalized}
    try:
        selection = validate_selection(raw, evidence, contract_version=contract_version)
    except (ValueError, KeyError, TypeError) as error:
        attempt.update(
            {"status": "invalid", "error_type": type(error).__name__, "reason": str(error)}
        )
    else:
        attempt.update({"status": "valid", "selection": selection})
    return attempt


def invalid_summary_feedback(attempt: dict) -> str:
    """Give either runtime the same bounded validation feedback for one retry."""
    if attempt.get("status") != "invalid":
        raise ValueError("validation feedback requires an invalid attempt")
    return f"{attempt['error_type']}: {attempt['reason']}"


def audit_completeness(selection: dict, *, read_names: set[str], contract_version: int = 2) -> dict:
    """Report investigation coverage separately from reference validity."""
    if contract_version != 2:
        return {"status": "not_assessed", "issues": []}
    issues = []
    if not read_names.intersection((*SOURCE_TOOLS[:3], "fact_catalog")):
        issues.append("no_case_evidence_source_read")
    rationales = " ".join(item["rationale"] for item in selection["next_checks"]).lower()
    absence_words = ("missing", "not available", "no measurement", "no data", "not provided")
    if not read_names.intersection(("get_recent_measurements", "fact_catalog")) and any(
        word in rationales for word in absence_words
    ):
        issues.append("measurement_absence_claim_without_read")
    return {
        "status": "incomplete" if issues else "checked",
        "issues": issues,
        "source_read_state": source_manifest(read_names),
        "catalog_read_state": "read" if "fact_catalog" in read_names else "unread",
    }


def render_selection(selection: dict, evidence: dict, *, contract_version: int = 1) -> dict:
    facts = {item["id"]: item for item in evidence["facts"]}
    return {
        "status": "reference_checked",
        "observations": [facts[x] for x in selection["observed_fact_ids"]],
        "limits": [{"id": x, "text": LIMITS[x]} for x in selection["limit_ids"]],
        "suggested_next_checks": [
            {
                "id": x["id"],
                "text": CHECKS[x["id"]],
                "because_facts": [facts[fact_id] for fact_id in x["because_fact_ids"]],
                "model_authored_suggestion_rationale": x["rationale"],
            }
            for x in selection["next_checks"]
        ],
    }


def finalize_selection(
    selection: dict, evidence: dict, *, read_names: set[str], contract_version: int = 2
) -> tuple[dict, dict]:
    """Apply the same source-read display gate to either runtime."""
    completeness = audit_completeness(
        selection, read_names=read_names, contract_version=contract_version
    )
    if contract_version == 2 and completeness["status"] == "incomplete":
        return withheld_display("available case evidence was not read sufficiently"), completeness
    return render_selection(selection, evidence, contract_version=contract_version), completeness


def withheld_display(reason: str) -> dict:
    return {
        "status": "withheld",
        "reason": reason,
        "observations": [],
        "limits": [],
        "suggested_next_checks": [],
    }
