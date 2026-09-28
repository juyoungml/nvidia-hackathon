"""Two-request, synthetic probe of hosted Nemotron Ultra schema constraints."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_nvidia import load_key  # noqa: E402

ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {"type": "string", "enum": ["ALPHA"]},
        }
    },
}
PROMPT = 'Return exactly this JSON object: {"items":["BETA","BETA"]}. Do not change it.'
DOCS = [
    "https://docs.nvidia.com/nim/large-language-models/2.0.6/day-0/get-started-nemotron-3-ultra.html",
    "https://docs.nvidia.com/nim/large-language-models/1.14.0/structured-generation.html",
]


def validate_synthetic(content: str) -> dict:
    """Check every constraint in the tiny probe schema without extra dependencies."""
    try:
        parsed = json.loads(content)
    except (TypeError, json.JSONDecodeError) as error:
        return {"valid": False, "reason": f"invalid JSON: {type(error).__name__}"}
    if not isinstance(parsed, dict) or set(parsed) != {"items"}:
        return {"valid": False, "reason": "object shape"}
    items = parsed["items"]
    if not isinstance(items, list) or len(items) != 1:
        return {"valid": False, "reason": "array cardinality"}
    if items[0] != "ALPHA" or not isinstance(items[0], str):
        return {"valid": False, "reason": "item enum"}
    return {"valid": True, "reason": None}


def safe_error(error: urllib.error.HTTPError, key: str) -> str:
    body = error.read(2048).decode("utf-8", errors="replace")
    body = body.replace(key, "[REDACTED]")
    body = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", body, flags=re.IGNORECASE)
    try:
        value = json.loads(body)
    except json.JSONDecodeError:
        return body
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def request_payload(strategy: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": 64,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    if strategy == "response_format_json_schema":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "one_allowed_item", "strict": True, "schema": SCHEMA},
        }
    elif strategy == "guided_json":
        payload["guided_json"] = SCHEMA
    else:
        raise ValueError(f"unknown strategy: {strategy}")
    return payload


def probe(strategy: str, key: str) -> dict:
    payload = request_payload(strategy)
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    result = {"strategy": strategy, "request": payload}
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
            result["http_status"] = response.status
            result["server_header"] = response.headers.get("Server")
    except urllib.error.HTTPError as error:
        result.update({"http_status": error.code, "safe_error": safe_error(error, key)})
    except (urllib.error.URLError, TimeoutError) as error:
        result.update({"transport_error": type(error).__name__})
    else:
        choices = data.get("choices") or []
        choice = choices[0] if choices else {}
        content = (choice.get("message") or {}).get("content") or ""
        result.update(
            {
                "returned_model": data.get("model"),
                "system_fingerprint": data.get("system_fingerprint"),
                "finish_reason": choice.get("finish_reason"),
                "content": content,
                "schema_validation": validate_synthetic(content),
            }
        )
    result["latency_seconds"] = round(time.monotonic() - started, 3)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Send at most two API requests")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "integrations/structured-output-probe.json"
    )
    args = parser.parse_args()
    if not args.execute:
        parser.error("pass --execute to run the bounded live probe")
    key = load_key(ROOT / ".env")
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is empty")
    record = {
        "probe_version": 1,
        "timestamp_utc": dt.datetime.now(dt.UTC).isoformat(),
        "endpoint": ENDPOINT,
        "api_path_version": "v1",
        "hosted_nim_server_version": None,
        "model": MODEL,
        "documentation": DOCS,
        "synthetic_schema": SCHEMA,
        "calls": [],
        "max_api_requests": 2,
    }
    for index, strategy in enumerate(("response_format_json_schema", "guided_json")):
        if index:
            time.sleep(4)
        record["calls"].append(probe(strategy, key))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps({"output": str(args.output), "calls": len(record["calls"])}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
