"""Execute the frozen cycle 4 comparison once per arm and case."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.live_claude import run_live_claude  # noqa: E402
from poc.live_investigation import build_live_bundle, run_live_case  # noqa: E402
from scripts.check_nvidia import load_key  # noqa: E402

MANIFEST = ROOT / "evaluation/cycle4/manifest.json"
PROTOCOL = ROOT / "evaluation/cycle4/PROTOCOL.md"
OUTPUT = ROOT / "evaluation/cycle4/traces"
DEVELOPMENT_IDS = (52, 3)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_cases(manifest_path: Path = MANIFEST) -> list[tuple[dict, dict, dict]]:
    """Verify every frozen input and public bundle before either model is contacted."""
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("cycle") != "cycle4" or not manifest.get("selection_frozen_before_inference"):
        raise ValueError("cycle 4 manifest is not frozen")
    cases = manifest["cases"]
    if [int(row["case_id"].rsplit("-", 1)[-1]) for row in cases[:2]] != list(DEVELOPMENT_IDS):
        raise ValueError("development case order changed")
    if [row["kind"] for row in cases[:2]] != ["development_exposed"] * 2:
        raise ValueError("development split changed")
    if any(row["kind"] != "fresh_test" for row in cases[2:]):
        raise ValueError("fresh test split changed")
    if len(cases) != 4 or len({row["case_id"] for row in cases}) != len(cases):
        raise ValueError("missing or duplicate cases")
    checked = []
    for row in cases:
        path = ROOT / row["path"]
        if path.parent != ROOT / "data" or sha256(path) != row["sha256"]:
            raise ValueError(f"public input hash mismatch: {row['path']}")
        replay = json.loads(path.read_text())
        if (
            replay["case_id"] != row["case_id"]
            or replay["asset"] != row["asset"]
            or replay["decision_time"] != row["decision_time"]
        ):
            raise ValueError(f"manifest identity mismatch: {row['path']}")
        bundle = build_live_bundle(replay, temporal_enabled=True)
        if bundle["corpus_sha256"] != row["public_corpus_sha256"]:
            raise ValueError(f"public corpus mismatch: {row['path']}")
        schema_hash = hashlib.sha256(
            json.dumps(bundle["schema"], ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        if schema_hash != row["plan_schema_sha256"]:
            raise ValueError(f"plan schema mismatch: {row['path']}")
        checked.append((row, replay, bundle))
    return checked


def _save_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run_cycle(*, expected_protocol_sha256: str, output_dir: Path = OUTPUT) -> list[dict]:
    if sha256(PROTOCOL) != expected_protocol_sha256:
        raise ValueError("protocol SHA-256 does not match frozen value")
    cases = checked_cases()
    if (output_dir.exists() and any(output_dir.glob("*.json"))) or (
        output_dir.parent / "run-summary.json"
    ).exists():
        raise ValueError("cycle output already contains results; use a new directory")
    key = load_key(ROOT / ".env")
    if not key:
        raise ValueError("NVIDIA API key unavailable")
    results = []
    for row, replay, bundle in cases:
        slug = row["case_id"].rsplit("-", 1)[-1]
        domain = run_live_case(replay, bundle=bundle, key=key, temporal_enabled=True)
        _save_new(output_dir / f"domain-{slug}.json", domain)
        general = run_live_claude(bundle)
        _save_new(output_dir / f"general-{slug}.json", general)
        if domain.get("corpus_sha256") != general.get("corpus_sha256"):
            raise ValueError(f"public corpus mismatch for {row['case_id']}")
        results.append(
            {
                "case_id": row["case_id"],
                "kind": row["kind"],
                "corpus_sha256": bundle["corpus_sha256"],
                "domain_validation": domain.get("validation"),
                "domain_display_status": (domain.get("display") or {}).get("status"),
                "general_validation": general.get("validation"),
                "general_display_status": (general.get("display") or {}).get("status"),
            }
        )
    _save_new(
        output_dir.parent / "run-summary.json",
        {
            "protocol_sha256": expected_protocol_sha256,
            "manifest_sha256": sha256(MANIFEST),
            "pairs": results,
        },
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-protocol-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(
        json.dumps(
            run_cycle(
                expected_protocol_sha256=args.expected_protocol_sha256,
                output_dir=args.output_dir,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
