"""Build the deterministic, public-only System 2 release archive.

Run from any directory: python submission/build_bundle.py
The source manifest is written inside the ZIP and beside it as RELEASE_MANIFEST.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "submission/NVIDIA_해커톤_팀명미정_Plant_Reliability_Agent_System2.zip"
MANIFEST_NAME = "submission/RELEASE_MANIFEST.json"
MAX_ZIP_BYTES = 100 * 1024 * 1024
# Every release input is named here. Keep outcomes, private run directories and old media out.
PUBLIC_FILES = (
    "README.md",
    "ARCHITECTURE.md",
    "CAPACITY_MODEL.md",
    "DATA_SOURCES.md",
    "DEMO_FLOW.md",
    "POC_RESULT.md",
    "PLAN.md",
    "STRATEGY.md",
    "WORKING_BRIEF.md",
    "pyproject.toml",
    "uv.lock",
    "data/README.md",
    "data/derived-missing-measurements-52.json",
    "data/derived-no-report-20161210.json",
    "data/replay-32.json",
    "data/replay-52.json",
    "data/replay-62.json",
    "data/holdout-3.json",
    "data/holdout-5.json",
    "data/holdout-13.json",
    "data/holdout-29.json",
    "data/holdout-37.json",
    "data/holdout-47.json",
    "data/holdout-60.json",
    "data/holdout-63.json",
    "poc/constrained_composer.py",
    "poc/evidence_contract.py",
    "poc/live_investigation.py",
    "poc/rate_limit.py",
    "poc/run.py",
    "poc/system2.py",
    "poc/temporal_evidence.py",
    "poc/temporal_tools.py",
    "poc/runtime-probe-log.json",
    "poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json",
    "poc/trace-52-ollama-nemotron-3-nano-4b.json",
    "poc/trace-52-pipeline.json",
    "scripts/build_replay.py",
    "scripts/check_nvidia.py",
    "scripts/serve_demo.py",
    "evaluation/README.md",
    "evaluation/SYSTEM2_PROTOCOL.md",
    "evaluation/audit_trajectories.py",
    "evaluation/build_derived.py",
    "evaluation/claude_code.py",
    "evaluation/compare_system2.py",
    "evaluation/domain_mcp.py",
    "evaluation/evaluate.py",
    "evaluation/live_claude.py",
    "evaluation/run_cases.py",
    "evaluation/run_live_cycle.py",
    "evaluation/run_system2_cycle.py",
    "evaluation/system2-case-manifest.json",
    # Public retrospective labels for legacy tests only; never served or supplied to live agents.
    "evaluation/held-out-32.json",
    "evaluation/held-out-52.json",
    "evaluation/held-out-62.json",
    "evaluation/results/README.md",
    "evaluation/results/comparison.json",
    "evaluation/results/traces/derived-missing-measurements.json",
    "evaluation/results/traces/derived-no-report.json",
    "evaluation/results/traces/fault-32.json",
    "evaluation/results/traces/fault-52.json",
    "evaluation/results/traces/fault-62.json",
    "evaluation/system2-results/RESULTS.md",
    "evaluation/system2-results/v2-review/summary.json",
    "evaluation/system2-results/v2-review/blind-review.md",
    "evaluation/system2-results/v2-review/blind-key.json",
    "evaluation/system2-results/posthoc/sonnet-domain-tools-52.json",
    "evaluation/system2-results/v1-pilot/domain-52.json",
    "evaluation/system2-results/v1-pilot/domain-60.json",
    "evaluation/system2-results/v1-pilot/domain-62.json",
    "evaluation/system2-results/v1-pilot/domain-63.json",
    "evaluation/system2-results/v1-pilot/general-52.json",
    "evaluation/system2-results/v1-pilot/general-60.json",
    "evaluation/system2-results/v1-pilot/general-63.json",
    "evaluation/cycle3/PROTOCOL.md",
    "evaluation/cycle3/RESULTS.md",
    "evaluation/cycle3/manifest.json",
    "evaluation/cycle3/aggregate.json",
    "evaluation/cycle3/run-summary.json",
    "evaluation/cycle3/review/summary.json",
    "evaluation/cycle3/review/blind-review.md",
    "evaluation/cycle3/audit/trajectory-audit-final.json",
    "evaluation/cycle3/audit/trajectory-audit-final.md",
    "evaluation/cycle3/audit/trajectory-audit-initial.md",
    "evaluation/audit-results/temporal-case3.json",
    "evaluation/cycle4/PROTOCOL.md",
    "evaluation/cycle4/RESULTS.md",
    "evaluation/cycle4/manifest.json",
    "evaluation/cycle4/cases.json",
    "evaluation/cycle4/results.json",
    "evaluation/cycle4/run-summary.json",
    "evaluation/cycle4/temporal-review.json",
    "evaluation/cycle4/development/handoff-v2-case52.json",
    "evaluation/readiness/RUBRIC.md",
    "evaluation/readiness/WORKPLAN.md",
    "evaluation/readiness/SCORECARD.md",
    "evaluation/readiness/JUDGE_A.md",
    "evaluation/readiness/JUDGE_B.md",
    "evaluation/readiness/QA.md",
    "evaluation/readiness/WEB_QA.md",
    "evaluation/readiness/ablation/PROTOCOL.md",
    "evaluation/readiness/ablation/RESULTS.md",
    "evaluation/readiness/ablation/results.json",
    "evaluation/readiness/ablation/build.py",
    "evaluation/readiness/content-review/RUBRIC.md",
    "evaluation/readiness/content-review/PACKETS.json",
    "evaluation/readiness/content-review/BLIND_REVIEW.json",
    "evaluation/readiness/content-review/BLIND_REVIEW.md",
    "evaluation/readiness/content-review/REVEAL_KEY.json",
    "evaluation/readiness/content-review/CONTENT_RESULTS.md",
    "evaluation/readiness/content-review/CONTENT_RESULTS.json",
    "evaluation/readiness/content-review/ERRATUM.md",
    "evaluation/readiness/content-review/reveal.py",
    "evaluation/readiness/content-review/v2/RUBRIC.md",
    "evaluation/readiness/content-review/v2/PACKETS.json",
    "evaluation/readiness/content-review/v2/REVEAL_KEY.json",
    "evaluation/readiness/content-review/v2/BLIND_REVIEW.json",
    "evaluation/readiness/content-review/v2/BLIND_REVIEW.md",
    "evaluation/readiness/content-review/v2/CONTENT_RESULTS.json",
    "evaluation/readiness/content-review/v2/CONTENT_RESULTS.md",
    "evaluation/readiness/content-review/v2/reveal.py",
    "integrations/README.md",
    "integrations/NAT_LIVE.md",
    "integrations/live_nat_adapter.py",
    "integrations/nat_live.py",
    "integrations/nat_live.yml",
    "integrations/nat-live-smoke.json",
    "integrations/nat-live-case52.json",
    "integrations/run_nat_live_smoke.py",
    "integrations/nat_replay.py",
    "integrations/nat_replay.yml",
    "integrations/openshell-README.md",
    "integrations/openshell-policy.yaml",
    "integrations/openshell-trace.json",
    "integrations/requirements.in",
    "integrations/requirements.lock",
    "integrations/run_nat_replay.py",
    "integrations/structured_output_probe.py",
    "integrations/structured-output-probe.json",
    "integrations/trace.json",
    "integrations/composer-development-results/case52.json",
    "integrations/composer-development-results/synthetic.json",
    "integrations/composer-development-results/synthetic_compat.json",
    "web/index.html",
    "web/evidence.html",
    "web/investigation.html",
    "web/app.js",
    "web/landing.js",
    "web/investigation.js",
    "web/style.css",
    "web/landing.css",
    "web/investigation.css",
    "web/hotspots.json",
    "web/plant-detailed.svg",
    "web/substation.svg",
    "web/assets/SOURCES.md",
    "web/assets/doe-steam-figure-1.png",
    "web/assets/doe-steam-page-3.png",
    "web/assets/predist-record.png",
    "web/assets/predist-trend.png",
    "web/system2.html",
    "web/system2.css",
    "web/system2.js",
    "web/assets/system2-29.json",
    "web/assets/system2-52.json",
    "web/assets/system2-case29-trend.png",
    "submission/CASE_STORY.md",
    "submission/DEMO_SCRIPT.md",
    "submission/FORM_DRAFT.md",
    "submission/REPORT.md",
    "submission/REVIEW_RESPONSE.md",
    "submission/SUBMISSION_GUIDE.md",
    "submission/build_bundle.py",
    "submission/slides/Plant_Reliability_Agent_submission.pptx",
    "submission/slides/build_deck.py",
    "submission/slides/VALIDATION.md",
    "scripts/export_submission_demo.py",
    "scripts/generate_public_figure.py",
    "tests/test_claude_code.py",
    "tests/test_compare_system2.py",
    "tests/test_constrained_composer.py",
    "tests/test_demo_server.py",
    "tests/test_evaluation.py",
    "tests/test_live_claude.py",
    "tests/test_live_cycle.py",
    "tests/test_live_investigation.py",
    "tests/test_nat_live.py",
    "tests/test_output_validation.py",
    "tests/test_rate_limit.py",
    "tests/test_replay.py",
    "tests/test_runtime.py",
    "tests/test_submission_bundle.py",
    "tests/test_system2.py",
    "tests/test_system2_cycle.py",
    "tests/test_temporal_evidence.py",
    "tests/test_temporal_tools.py",
    "tests/test_trajectory_audit.py",
    "tests/test_visual_demo.py",
)
# Historical trace files have a stable, reviewed name pattern; these are still exact release paths.
TRACE_FILES = tuple(
    f"evaluation/{cycle}/traces/{model}-{case}.json"
    for cycle, cases in (
        ("cycle3", ("3", "5", "13", "37", "52", "60", "63")),
        ("cycle4", ("3", "29", "47", "52")),
    )
    for model in ("domain", "general")
    for case in cases
)
V2_FILES = tuple(
    f"evaluation/system2-results/v2/{model}-{case}.json"
    for model in ("domain", "general")
    for case in ("3", "13", "52", "60", "63")
)
EXCLUDED_PARTS = {".git", ".venv", ".artifacts", "__pycache__", "private", "secrets", "output"}
EXCLUDED_NAMES = {".env", ".env.example", "credentials.json", "secrets.json", "token.json"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:sk-|nvapi-|ghp_|gho_|github_pat_)[A-Za-z0-9_-]{24,}"),
    re.compile(rb"(?i)\bNVIDIA_API_KEY\s*[:=]\s*['\"]?[A-Za-z0-9_/-]{28,}"),
    re.compile(
        rb"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_/-]{28,}"
    ),
    re.compile(rb"(?:/Users/|/home/|[A-Za-z]:\\Users\\)[A-Za-z0-9_.-]+"),
)
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".svg",
    ".toml",
    ".lock",
    ".in",
}


def check_path(path: Path) -> None:
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Path must be inside repository: {path}")
    relative = path.relative_to(ROOT)
    if any(
        part == ".." or part.startswith(".") or part.lower() in EXCLUDED_PARTS
        for part in relative.parts
    ):
        raise ValueError(f"Private or hidden path: {relative}")
    if path.name.lower() in EXCLUDED_NAMES:
        raise ValueError(f"Credential-like filename: {relative}")
    if any(
        (ROOT / Path(*relative.parts[:index])).is_symlink()
        for index in range(1, len(relative.parts) + 1)
    ):
        raise ValueError(f"Symlink path: {relative}")


def check_file(path: Path) -> None:
    check_path(path)
    if path.suffix.lower() in TEXT_SUFFIXES:
        raw = path.read_bytes()
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS):
            raise ValueError(f"Potential secret or private path in {path.relative_to(ROOT)}")
    elif path.suffix.lower() == ".pptx":
        with zipfile.ZipFile(path) as deck:
            for name in deck.namelist():
                if name.endswith((".xml", ".rels")) and any(
                    pattern.search(deck.read(name)) for pattern in SECRET_PATTERNS
                ):
                    raise ValueError(
                        f"Potential secret or private path in {path.relative_to(ROOT)}:{name}"
                    )


def public_files(output_path: Path | None = None) -> list[Path]:
    names = PUBLIC_FILES + TRACE_FILES + V2_FILES
    if len(names) != len(set(names)):
        raise ValueError("Duplicate release path")
    files = [ROOT / name for name in names]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"Required release file missing: {path}")
        check_file(path)
    if output_path in files:
        raise ValueError("Output would overwrite an input")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def manifest_bytes(files: list[Path]) -> bytes:
    entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
        for path in files
    ]
    return (
        json.dumps({"format": 1, "files": entries}, ensure_ascii=False, indent=2) + "\n"
    ).encode()


def build(output_path: Path = DEFAULT_OUTPUT) -> tuple[int, int]:
    output_path = ROOT / output_path if not output_path.is_absolute() else output_path
    if not output_path.is_relative_to(ROOT) or output_path.suffix.lower() != ".zip":
        raise ValueError("--output must be a ZIP inside repository")
    check_path(output_path)
    files = public_files(output_path)
    manifest = manifest_bytes(files)
    if sum(path.stat().st_size for path in files) + len(manifest) > MAX_ZIP_BYTES:
        raise ValueError("Release inputs exceed 100 MB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output_path.parent, suffix=".zip", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        with zipfile.ZipFile(
            temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, content in [
                *((path.relative_to(ROOT).as_posix(), path.read_bytes()) for path in files),
                (MANIFEST_NAME, manifest),
            ]:
                info = zipfile.ZipInfo(name, date_time=(2026, 9, 28, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        size = temporary_path.stat().st_size
        if size > MAX_ZIP_BYTES:
            raise ValueError("Release ZIP exceeds 100 MB")
        os.replace(temporary_path, output_path)
        (ROOT / MANIFEST_NAME).write_bytes(manifest)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return len(files) + 1, size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    count, size = build(args.output)
    print(f"{args.output.resolve()} ({count} files, {size:,} bytes)")


if __name__ == "__main__":
    main()
