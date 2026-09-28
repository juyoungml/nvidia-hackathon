"""Run one frozen cycle-3 domain/general pair per manifest case.

Inference requires an explicit SHA-256 of the frozen protocol. Trace files are
created exclusively, and every case input is checked against the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.claude_code import run_public_bundle  # noqa: E402
from poc.evidence_contract import build_case_bundle  # noqa: E402
from poc.system2 import run_system2  # noqa: E402
from scripts.check_nvidia import load_key  # noqa: E402

MANIFEST = ROOT / "evaluation/cycle3/manifest.json"
PROTOCOL = ROOT / "evaluation/cycle3/PROTOCOL.md"
OUTPUT = ROOT / "evaluation/cycle3/traces"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_cases(manifest_path: Path = MANIFEST) -> list[tuple[dict, dict]]:
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("cycle") != "cycle3" or not manifest.get("selection_frozen_before_inference"):
        raise ValueError("cycle-3 manifest is not frozen")
    cases = manifest["cases"]
    if [row["kind"] for row in cases] != ["development_exposed"] * 5 + ["fresh_test"] * 2:
        raise ValueError("cycle-3 development/test split changed")
    checked = []
    for row in cases:
        path = ROOT / row["path"]
        if path.parent != ROOT / "data" or sha256(path) != row["sha256"]:
            raise ValueError(f"public input hash mismatch: {row['path']}")
        replay = json.loads(path.read_text())
        if replay["case_id"] != row["case_id"] or replay["asset"] != row["asset"]:
            raise ValueError(f"manifest identity mismatch: {row['path']}")
        corpus = build_case_bundle(replay, contract_version=2)["corpus_sha256"]
        if corpus != row["public_corpus_sha256_v2"]:
            raise ValueError(f"public corpus mismatch: {row['path']}")
        checked.append((row, replay))
    return checked


def _save_new(path: Path, trace: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(trace, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run_cycle(*, expected_protocol_sha256: str, output_dir: Path = OUTPUT) -> list[dict]:
    if sha256(PROTOCOL) != expected_protocol_sha256:
        raise ValueError("protocol SHA-256 does not match frozen value")
    cases = checked_cases()
    if output_dir.exists() and any(output_dir.glob("*.json")):
        raise ValueError("cycle trace directory already contains JSON; use a new directory")
    key = load_key(ROOT / ".env")
    if not key:
        raise ValueError("NVIDIA API key unavailable")
    results = []
    for row, replay in cases:
        case_id = row["case_id"]
        slug = case_id.rsplit("-", 1)[-1]
        domain = run_system2(
            replay,
            mode="tools",
            backend="nvidia",
            key=key,
            contract_version=2,
            harness_policy="validate_repair_once",
        )
        _save_new(output_dir / f"domain-{slug}.json", domain)
        general = run_public_bundle(
            replay,
            mode="file_agent",
            contract_version=2,
            harness_policy="validate_repair_once",
        )
        _save_new(output_dir / f"general-{slug}.json", general)
        if domain.get("corpus_sha256") != general.get("corpus_sha256"):
            raise ValueError(f"public corpus mismatch for {case_id}")
        results.append(
            {
                "case_id": case_id,
                "kind": row["kind"],
                "corpus_sha256": domain["corpus_sha256"],
                "domain_initial": (domain.get("validation_attempts") or [{}])[0].get("status"),
                "domain_final": (domain.get("validation") or {}).get("status"),
                "general_initial": (general.get("validation_attempts") or [{}])[0].get("status"),
                "general_final": "valid"
                if (general.get("validation") or {}).get("valid")
                else "invalid",
            }
        )
        time.sleep(1.6)
    _save_new(
        output_dir.parent / "run-summary.json",
        {
            "protocol_sha256": expected_protocol_sha256,
            "manifest_sha256": sha256(MANIFEST),
            "harness_policy": "validate_repair_once",
            "pairs": results,
        },
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-protocol-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    rows = run_cycle(
        expected_protocol_sha256=args.expected_protocol_sha256,
        output_dir=args.output_dir,
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
