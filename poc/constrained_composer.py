"""Development-only native-schema plan composer for stored public System 2 traces."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from check_nvidia import load_key  # noqa: E402

from poc.evidence_contract import (  # noqa: E402
    CHECKS,
    LIMITS,
    TASK_V2,
    finalize_selection,
    source_manifest,
    validate_selection,
    withheld_display,
)
from poc.run import ENDPOINT, ULTRA_MODEL  # noqa: E402

OUTPUT_DIR = ROOT / "integrations/composer-development-results"
TRACE_PATHS = {
    "case52": ROOT / "evaluation/cycle3/traces/domain-52.json",
    "case63": ROOT / "evaluation/cycle3/traces/domain-63.json",
}
POLICY = "plan_first_native_schema_v1"


def plan_schema(evidence: dict) -> dict:
    """Constrain only model-selected limits, checks, references, and suggestion text."""
    fact_ids = [fact["id"] for fact in evidence["facts"]]
    if not fact_ids or len(fact_ids) != len(set(fact_ids)):
        raise ValueError("evidence requires unique fact IDs")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["limit_ids", "next_checks"],
        "properties": {
            "limit_ids": {
                "type": "array",
                "items": {"type": "string", "enum": list(LIMITS)},
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
                        "id": {"type": "string", "enum": list(CHECKS)},
                        "because_fact_ids": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string", "enum": fact_ids},
                        },
                        "rationale": {"type": "string", "minLength": 1, "maxLength": 240},
                    },
                },
            },
        },
    }


def assemble_selection(raw_plan: str, evidence: dict) -> tuple[dict, dict]:
    """Derive displayed observations solely from selected support IDs, then run v2 validator."""
    try:
        plan = json.loads(raw_plan)
    except json.JSONDecodeError as error:
        raise ValueError("plan is not JSON") from error
    if not isinstance(plan, dict) or set(plan) != {"limit_ids", "next_checks"}:
        raise ValueError("plan schema mismatch")
    limits = plan["limit_ids"]
    if (
        not isinstance(limits, list)
        or any(not isinstance(item, str) or item not in LIMITS for item in limits)
        or len(limits) != len(set(limits))
    ):
        raise ValueError("invalid or duplicate limit IDs")
    checks = plan["next_checks"]
    if not isinstance(checks, list) or len(checks) not in {2, 3}:
        raise ValueError("plan requires 2 or 3 checks")
    allowed_facts = {fact["id"] for fact in evidence["facts"]}
    selected_ids: list[str] = []
    seen_facts: set[str] = set()
    seen_checks: set[str] = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "because_fact_ids", "rationale"}:
            raise ValueError("next check schema mismatch")
        check_id = check["id"]
        if not isinstance(check_id, str) or check_id not in CHECKS or check_id in seen_checks:
            raise ValueError("invalid or duplicate check ID")
        seen_checks.add(check_id)
        refs = check["because_fact_ids"]
        if (
            not isinstance(refs, list)
            or not 1 <= len(refs) <= 4
            or any(not isinstance(item, str) or item not in allowed_facts for item in refs)
            or len(refs) != len(set(refs))
        ):
            raise ValueError("invalid or duplicate supporting fact ID")
        rationale = check["rationale"]
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 240:
            raise ValueError("invalid next check rationale")
        for fact_id in refs:
            if fact_id not in seen_facts:
                seen_facts.add(fact_id)
                selected_ids.append(fact_id)
    if len(selected_ids) > 12:
        raise ValueError("derived observations exceed 12-fact bound")
    assembled = {
        "observed_fact_ids": selected_ids,
        "limit_ids": limits,
        "next_checks": checks,
    }
    validate_selection(json.dumps(assembled), evidence, contract_version=2)
    return plan, assembled


def synthetic_context() -> tuple[dict, set[str], dict]:
    evidence = {
        "schema_version": 1,
        "case_id": "synthetic-structure-only",
        "decision_time": "synthetic",
        "sources": [{"id": "synthetic-source", "kind": "synthetic"}],
        "facts": [
            {"id": f"F-synthetic-{index}", "source_id": "synthetic-source", "text": "synthetic"}
            for index in range(1, 4)
        ],
    }
    return evidence, {"fact_catalog"}, {"case_id": "synthetic-structure-only"}


def stored_context(name: str) -> tuple[dict, set[str], dict]:
    path = TRACE_PATHS[name]
    trace_bytes = path.read_bytes()
    trace = json.loads(trace_bytes)
    if trace.get("contract_version") != 2 or trace.get("method") != "system2-tools-repair-v1":
        raise ValueError("stored trace is not the expected cycle3 domain trace")
    reads = {call["name"] for call in trace["tool_calls"]}
    expected = {
        "get_recent_measurements",
        "get_prior_incidents",
        "get_maintenance_timeline",
        "get_signal_definitions",
    }
    if reads != expected:
        raise ValueError("stored trace did not read all four case sources")
    evidence = trace["evidence"]
    if evidence["case_id"] != trace["case_id"]:
        raise ValueError("stored evidence case mismatch")
    return (
        evidence,
        reads,
        {
            "case_id": trace["case_id"],
            "stored_trace": str(path.relative_to(ROOT)),
            "stored_trace_sha256": hashlib.sha256(trace_bytes).hexdigest(),
            "corpus_sha256": trace["corpus_sha256"],
        },
    )


def request_payload(evidence: dict, reads: set[str]) -> dict:
    schema = plan_schema(evidence)
    user_content = json.dumps(
        {
            "development_composition_policy": (
                "Select 2 or 3 distinct next checks. For each, select 1 to 4 distinct supporting "
                "fact IDs from the already retrieved catalog and write a rationale of at most "
                "240 characters. Select limit IDs from the catalog. Do not output "
                "observed_fact_ids; the program will derive observations as the ordered union "
                "of your selected supporting IDs. Keep that union within 12 IDs. Do not make "
                "a root-cause conclusion or recommend changing controls. Return the plan JSON."
            ),
            "original_task": TASK_V2,
            "evidence": evidence,
            "limits_catalog": LIMITS,
            "checks_catalog": CHECKS,
            "source_read_state": source_manifest(reads),
            "plan_schema": schema,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return {
        "model": ULTRA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a read-only plant investigator. Select only supplied fact and catalog "
                    "IDs. Rationales are suggestions, not observations or proven causes. Reply "
                    "only with plan JSON matching the native schema."
                ),
            },
            {"role": "user", "content": user_content},
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


def safe_http_error(error: urllib.error.HTTPError, key: str) -> str:
    body = error.read(2048).decode("utf-8", errors="replace")
    body = body.replace(key, "[REDACTED]")
    body = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", body, flags=re.IGNORECASE)
    return body


def run_once(name: str, key: str) -> dict:
    if name.startswith("synthetic"):
        evidence, reads, provenance = synthetic_context()
    else:
        evidence, reads, provenance = stored_context(name)
    payload = request_payload(evidence, reads)
    result = {
        "composer_policy": POLICY,
        "development_only": True,
        "timestamp_utc": dt.datetime.now(dt.UTC).isoformat(),
        "api_endpoint": ENDPOINT,
        "api_path_version": "v1",
        "hosted_nim_server_version": None,
        "provenance": provenance,
        "request": payload,
        "raw_plan": None,
        "native_schema": payload["response_format"]["json_schema"]["schema"],
        "assembled_selection": None,
        "validation": None,
        "completeness": {"status": "not_assessed", "issues": []},
        "display": withheld_display("run not completed"),
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.load(response)
            result["http_status"] = response.status
            result["server_header"] = response.headers.get("Server")
        choice = body["choices"][0]
        result["returned_model"] = body.get("model")
        result["system_fingerprint"] = body.get("system_fingerprint")
        result["usage"] = body.get("usage")
        result["finish_reason"] = choice.get("finish_reason")
        raw = choice["message"].get("content") or ""
        result["raw_plan"] = raw
        plan, selection = assemble_selection(raw, evidence)
        result["parsed_plan"] = plan
        result["assembled_selection"] = selection
        result["validation"] = {"status": "valid", "selection": selection}
        result["display"], result["completeness"] = finalize_selection(
            selection, evidence, read_names=reads, contract_version=2
        )
    except urllib.error.HTTPError as error:
        result["http_status"] = error.code
        result["safe_http_error"] = safe_http_error(error, key)
        result["validation"] = {"status": "invalid", "reason": "native schema request failed"}
        result["display"] = withheld_display("native schema request failed")
    except (urllib.error.URLError, TimeoutError) as error:
        result["transport_error"] = type(error).__name__
        result["validation"] = {"status": "invalid", "reason": "transport failure"}
        result["display"] = withheld_display("transport failure")
    except (ValueError, KeyError, TypeError) as error:
        result["validation"] = {
            "status": "invalid",
            "error_type": type(error).__name__,
            "reason": str(error),
        }
        result["display"] = withheld_display(str(error))
    result["request_seconds"] = round(time.monotonic() - started, 3)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("synthetic", "synthetic_compat", "case52", "case63"))
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{args.case}.json"
    if path.exists() or len(list(OUTPUT_DIR.glob("*.json"))) >= 3:
        parser.error("development request budget exhausted or this case already has a result")
    key = load_key(ROOT / ".env")
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is empty")
    result = run_once(args.case, key)
    with path.open("x") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(
        json.dumps(
            {
                "path": str(path),
                "http_status": result.get("http_status"),
                "validation": result["validation"],
                "display_status": result["display"]["status"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
