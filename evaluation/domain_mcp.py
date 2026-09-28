"""Minimal stdio MCP server for four fixed public replay readers.

The server reads only the named JSON files in its explicit bundle directory.
It exposes no filesystem or command tool to the model.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = (
    "get_recent_measurements",
    "get_prior_incidents",
    "get_maintenance_timeline",
    "get_signal_definitions",
)
DESCRIPTIONS = {
    "get_recent_measurements": "Read pre-decision public measurements and setpoints; return numeric summaries, not a diagnosis.",
    "get_prior_incidents": "Read previous published reports for this asset; current diagnosis and remedy withheld.",
    "get_maintenance_timeline": "Read previous maintenance timestamps with no assumed completion outcome.",
    "get_signal_definitions": "Explain source sensor names, sides and units.",
}


def load_bundle(directory: Path) -> tuple[dict, dict, dict[str, dict]]:
    case = json.loads((directory / "case.json").read_text())
    catalog = json.loads((directory / "fact_catalog.json").read_text())
    results = {
        name: json.loads((directory / "tools" / f"{name}.json").read_text()) for name in TOOLS
    }
    return case, catalog, results


def tool_payload(
    name: str, case: dict, catalog: dict, results: dict[str, dict], read_names: set[str]
) -> dict:
    if name not in TOOLS:
        raise ValueError("unknown public tool")
    result = results[name]
    report_id = case["current_report"]["source_id"]
    ids = (
        {result["source_id"]}
        if name == "get_recent_measurements"
        else {row["source_id"] for row in result.get("records", [])}
    )
    read_names.add(name)
    return {
        "tool_result": result,
        "facts": [
            fact
            for fact in catalog["facts"]
            if fact["source_id"] in ids and fact["source_id"] != report_id
        ],
        "source_manifest": {
            "available_sources": [
                {"reader": reader, "read_state": "read" if reader in read_names else "unread"}
                for reader in TOOLS
            ]
        },
    }


def handle(
    request: dict,
    case: dict,
    catalog: dict,
    results: dict[str, dict],
    read_names: set[str],
    log_path: Path,
) -> dict | None:
    method = request.get("method")
    if method == "notifications/initialized" or "id" not in request:
        return None
    ident = request["id"]
    base = {"jsonrpc": "2.0", "id": ident}
    if method == "initialize":
        version = (request.get("params") or {}).get("protocolVersion", "2025-11-25")
        base["result"] = {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "public-domain-replay", "version": "1.0.0"},
        }
    elif method == "tools/list":
        base["result"] = {
            "tools": [
                {
                    "name": name,
                    "description": DESCRIPTIONS[name],
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                }
                for name in TOOLS
            ]
        }
    elif method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        if params.get("arguments", {}) != {} or name not in TOOLS:
            base["result"] = {
                "content": [{"type": "text", "text": "Invalid public tool call"}],
                "isError": True,
            }
        else:
            payload = tool_payload(name, case, catalog, results, read_names)
            text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            base["result"] = {"content": [{"type": "text", "text": text}], "isError": False}
            with log_path.open("a", encoding="utf-8") as log:
                log.write(
                    json.dumps(
                        {"name": name, "arguments": {}, "reply": payload},
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )
    elif method in {"ping", "resources/list", "prompts/list"}:
        base["result"] = (
            {"resources": []}
            if method == "resources/list"
            else ({"prompts": []} if method == "prompts/list" else {})
        )
    else:
        base["error"] = {"code": -32601, "message": "Method not found"}
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.bundle_dir.resolve(strict=True)
    case, catalog, results = load_bundle(directory)
    log_path = directory / "mcp-calls.jsonl"
    read_names: set[str] = set()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle(request, case, catalog, results, read_names, log_path)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            print(f"public MCP request error: {type(exc).__name__}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
