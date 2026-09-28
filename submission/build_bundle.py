"""Create a reproducible, public-only ZIP of the hackathon submission.

Usage: python submission/build_bundle.py --pdf submission/report.pdf \
    --output submission/submission.zip
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_ZIP_BYTES = 100 * 1024 * 1024
PUBLIC_FILES = (
    "ARCHITECTURE.md",
    "DATA_SOURCES.md",
    "DEMO_FLOW.md",
    "POC_RESULT.md",
    "README.md",
    "STRATEGY.md",
    "data/README.md",
    "data/derived-missing-measurements-52.json",
    "data/derived-no-report-20161210.json",
    "data/replay-32.json",
    "data/replay-52.json",
    "data/replay-62.json",
    "evaluation/README.md",
    "evaluation/build_derived.py",
    "evaluation/evaluate.py",
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
    "evaluation/run_cases.py",
    "figures/presentation/01.png",
    "figures/presentation/02.png",
    "figures/presentation/03.png",
    "figures/presentation/04.png",
    "figures/presentation/README.md",
    "integrations/README.md",
    "integrations/nat_replay.py",
    "integrations/nat_replay.yml",
    "integrations/openshell-README.md",
    "integrations/openshell-policy.yaml",
    "integrations/openshell-trace.json",
    "integrations/requirements.lock",
    "integrations/run_nat_replay.py",
    "integrations/trace.json",
    "poc/rate_limit.py",
    "poc/run.py",
    "poc/runtime-probe-log.json",
    "poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json",
    "poc/trace-52-ollama-nemotron-3-nano-4b.json",
    "poc/trace-52-pipeline.json",
    "pyproject.toml",
    "scripts/build_replay.py",
    "scripts/check_nvidia.py",
    "scripts/inspect_remote_zip.py",
    "scripts/serve_demo.py",
    "submission/DEMO_SCRIPT.md",
    "submission/FORM_DRAFT.md",
    "submission/build_bundle.py",
    "submission/build_pdf.py",
    "submission/fonts/NanumGothic-Regular.ttf",
    "submission/fonts/OFL.txt",
    "submission/report_content.json",
    "tests/test_demo_server.py",
    "tests/test_evaluation.py",
    "tests/test_output_validation.py",
    "tests/test_rate_limit.py",
    "tests/test_replay.py",
    "tests/test_runtime.py",
    "tests/test_submission_bundle.py",
    "tests/test_visual_demo.py",
    "uv.lock",
    "web/app.js",
    "web/assets/SOURCES.md",
    "web/assets/doe-steam-figure-1.png",
    "web/assets/doe-steam-page-3.png",
    "web/assets/predist-record.png",
    "web/assets/predist-trend.png",
    "web/evidence.html",
    "web/hotspots.json",
    "web/index.html",
    "web/investigation.css",
    "web/investigation.html",
    "web/investigation.js",
    "web/landing.css",
    "web/landing.js",
    "web/plant-detailed.svg",
    "web/style.css",
    "web/substation.svg",
)
OPTIONAL_PUBLIC_FILES = (
    "submission/build_demo_video.py",
    "submission/demo_walkthrough.mp4",
)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".artifacts",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "private",
    "secrets",
    "history",
    "tmp",
    "output",
}
EXCLUDED_NAMES = {
    ".env",
    ".env.example",
    "credentials.json",
    "secrets.json",
    "token.json",
    "id_rsa",
    "id_ed25519",
    "submission.zip",
}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:sk-|nvapi-|ghp_|gho_|github_pat_)[A-Za-z0-9_-]{24,}"),
    re.compile(
        rb"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_/-]{28,}"
    ),
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
    ".svg",
    ".toml",
    ".lock",
}


def public_files(pdf_path: Path, output_path: Path) -> list[Path]:
    files = [ROOT / relative for relative in PUBLIC_FILES]
    files.append(pdf_path)
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(f"Required submission file is missing: {path}")
    files.extend(
        ROOT / relative for relative in OPTIONAL_PUBLIC_FILES if (ROOT / relative).is_file()
    )
    if output_path in files:
        raise ValueError("Output path would overwrite an input file")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def check_path(path: Path, *, allow_output_name: bool = False) -> None:
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Path must be inside the repository: {path}")
    relative = path.relative_to(ROOT)
    if any(
        part == ".." or part.startswith(".") or part.lower() in EXCLUDED_PARTS
        for part in relative.parts
    ):
        raise ValueError(f"Private or hidden path would enter bundle: {relative}")
    if path.name.lower() in EXCLUDED_NAMES and not (
        allow_output_name and path.name == "submission.zip"
    ):
        raise ValueError(f"Credential-like filename would enter bundle: {relative}")
    if any(
        (ROOT / Path(*relative.parts[:index])).is_symlink()
        for index in range(1, len(relative.parts) + 1)
    ):
        raise ValueError(f"Symlink path is not allowed: {relative}")


def check_file(path: Path) -> None:
    check_path(path)
    relative = path.relative_to(ROOT)
    if path.suffix.lower() in TEXT_SUFFIXES:
        raw = path.read_bytes()
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS):
            raise ValueError(f"Potential credential in {relative}; inspect before packaging")


def build(pdf_path: Path, output_path: Path) -> tuple[int, int]:
    pdf_path = ROOT / pdf_path if not pdf_path.is_absolute() else pdf_path
    output_path = ROOT / output_path if not output_path.is_absolute() else output_path
    if pdf_path.parent != ROOT / "submission" or pdf_path.suffix.lower() != ".pdf":
        raise ValueError("--pdf must point to a PDF in submission/")
    if not output_path.is_relative_to(ROOT) or output_path.suffix.lower() != ".zip":
        raise ValueError("--output must point to a ZIP inside the repository")
    check_path(pdf_path)
    check_path(output_path, allow_output_name=True)
    files = public_files(pdf_path, output_path)
    for path in files:
        check_file(path)
    if sum(path.stat().st_size for path in files) > MAX_ZIP_BYTES:
        raise ValueError("Input files exceed the 100 MB submission limit")
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
            for path in files:
                info = zipfile.ZipInfo(
                    path.relative_to(ROOT).as_posix(), date_time=(2026, 1, 1, 0, 0, 0)
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(
                    info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
                )
        size = temporary_path.stat().st_size
        if size > MAX_ZIP_BYTES:
            raise ValueError("ZIP exceeds the 100 MB submission limit")
        os.replace(temporary_path, output_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return len(files), size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=ROOT / "submission/report.pdf")
    parser.add_argument("--output", type=Path, default=ROOT / "submission/submission.zip")
    args = parser.parse_args()
    count, size = build(args.pdf, args.output)
    print(f"{args.output.resolve()} ({count} files, {size:,} bytes)")


if __name__ == "__main__":
    main()
