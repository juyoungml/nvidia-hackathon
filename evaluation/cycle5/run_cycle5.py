"""Cycle 5: run the frozen cycle-5 case list once per arm (Ultra bounded_finalize_v2, Sonnet 5).

Cases are built from the public PreDist v2 manufacturer-1 CSVs in an ignored local
source directory using the same windowing and cutoff logic as
scripts/build_holdout_cases.py. Outputs are new files under evaluation/cycle5/.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT, ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from build_holdout_cases import REQUIRED_FIELDS  # noqa: E402
from build_replay import SOURCE_URL, file_sha256, numeric, read_csv, timestamp  # noqa: E402

import poc.live_investigation as live  # noqa: E402
import poc.run as poc_run  # noqa: E402
from poc.rate_limit import RequestPacer  # noqa: E402

HERE = ROOT / "evaluation" / "cycle5"
SELECTION_RULE = (
    "Every manufacturer-1 PreDist v2 fault report (all problem categories), in report-ID "
    "order, whose substation operational CSV is available locally by the run cutoff, with "
    ">=100 prior-24-hour samples and nonempty required hc1 fields. Frozen before inference."
)


class LockedPacer(RequestPacer):
    """Thread-safe pacer shared by all Ultra worker threads (34 rpm < 40 rpm limit)."""

    def __init__(self, rpm: int) -> None:
        super().__init__(rpm=rpm)
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            super().wait()


def build_case(source_dir: Path, report_id: str) -> dict:
    faults = read_csv(source_dir / "faults.csv")
    disturbances = read_csv(source_dir / "disturbances.csv")
    features = read_csv(source_dir / "features.csv")
    (target,) = [row for row in faults if row["Event ID"] == report_id]
    asset_id = target["substation ID"]
    decision_time = timestamp(target["Report date"])
    start_time = decision_time - dt.timedelta(hours=24)
    sensor_path = source_dir / f"substation_{asset_id}.csv"
    measurements: list[dict] = []
    with sensor_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        if not set(REQUIRED_FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("missing hc1 columns")
        for row in reader:
            when = timestamp(row["timestamp"])
            if start_time <= when <= decision_time:
                measurements.append(
                    {
                        "timestamp": row["timestamp"],
                        **{k: numeric(v) for k, v in row.items() if k != "timestamp"},
                    }
                )
    if len(measurements) < 100 or any(
        row[field] is None for row in measurements for field in REQUIRED_FIELDS
    ):
        raise ValueError(f"ineligible: {len(measurements)} samples or empty hc1 fields")
    case_id = f"PreDist-M1-fault-{report_id}"
    names = ("faults.csv", "disturbances.csv", "features.csv")
    source_paths = {**{n: source_dir / n for n in names}, sensor_path.name: sensor_path}
    return {
        "source": {
            "dataset": "PreDist v2",
            "url": SOURCE_URL,
            "doi": "10.5281/zenodo.19496480",
            "license": "CC BY 4.0",
            "publisher": "Fraunhofer IEE / enercity Netz GmbH",
            "asset_type": "district heating substation",
        },
        "case_id": case_id,
        "asset": {"manufacturer": 1, "substation_id": asset_id},
        "decision_time": decision_time.isoformat(sep=" "),
        "current_report": {
            "source_id": f"{case_id}-problem-only",
            "problem": target["Problem EN"],
            "note": "Only the reported problem is visible at decision time. Later diagnosis and remedy are withheld.",
        },
        "measurement_window": {
            "start": start_time.isoformat(sep=" "),
            "end": decision_time.isoformat(sep=" "),
            "source_id": f"PreDist-M1-substation-{asset_id}-operational-data",
            "rows": measurements,
        },
        "prior_faults": [
            {
                "source_id": f"PreDist-M1-fault-{row['Event ID']}",
                "report_date": row["Report date"],
                "problem": row["Problem EN"],
                "event_description": row["Event description EN"],
            }
            for row in faults
            if row["substation ID"] == asset_id and timestamp(row["Report date"]) < decision_time
        ],
        "prior_disturbances": [
            {
                "source_id": f"PreDist-M1-disturbance-{index}",
                "event_start": row["Event start"],
                "type": row["type"],
            }
            for index, row in enumerate(disturbances, 1)
            if row["substation ID"] == asset_id and timestamp(row["Event start"]) < decision_time
        ],
        "record_availability_note": (
            "Earlier report dates precede the decision time, but the dataset does not establish "
            "when their retrospective narratives became available to an operator."
        ),
        "features": {
            row["column"]: {"description": row["description"], "unit": row["unit"]}
            for row in features
        },
        "provenance": {
            "source_files_sha256": {n: file_sha256(p) for n, p in source_paths.items()},
            "selection": {
                "rule": SELECTION_RULE,
                "report_id": report_id,
                "asset_id": asset_id,
                "window_hours": 24,
                "cutoff": "measurement timestamp <= report date; prior records strictly earlier",
            },
        },
    }


def prepare(source_dir: Path) -> None:
    """Build case inputs for every report; record ineligible/unavailable ones."""
    (HERE / "cases").mkdir(parents=True, exist_ok=True)
    faults = read_csv(source_dir / "faults.csv")
    manifest = []
    for row in sorted(faults, key=lambda r: int(r["Event ID"])):
        rid, asset = row["Event ID"], row["substation ID"]
        entry = {"report_id": rid, "asset_id": asset, "problem": row["Problem EN"]}
        path = HERE / "cases" / f"case-{rid}.json"
        if path.exists():
            entry.update(status="eligible", path=str(path.relative_to(ROOT)))
        elif not (source_dir / f"substation_{asset}.csv").exists():
            entry["status"] = "source_unavailable"
        else:
            try:
                replay = build_case(source_dir, rid)
                path.write_text(json.dumps(replay, ensure_ascii=False, indent=1) + "\n")
                entry.update(status="eligible", path=str(path.relative_to(ROOT)))
            except (ValueError, KeyError) as error:
                entry.update(status="ineligible", reason=str(error))
        if entry["status"] == "eligible":
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(entry)
    (HERE / "case-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps([(m["report_id"], m["status"]) for m in manifest]))


def _save_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run(arm: str, report_ids: list[str], workers: int, tag: str = "") -> None:
    from scripts.check_nvidia import load_key

    key = load_key(ROOT / ".env") if arm == "ultra" else None
    if arm == "ultra":
        pacer = LockedPacer(rpm=int(os.environ.get("CYCLE5_RPM", "34")))
        poc_run.NVIDIA_PACER = pacer
        live.NVIDIA_PACER = pacer

    def one(rid: str) -> None:
        out = HERE / "traces" / f"{arm}{tag}-{rid}.json"
        if out.exists():
            return
        replay = json.loads((HERE / "cases" / f"case-{rid}.json").read_text())
        bundle = live.build_live_bundle(replay, temporal_enabled=True)
        started = dt.datetime.now().isoformat(timespec="seconds")
        try:
            if arm == "ultra":
                trace = live.run_live_case(
                    replay,
                    bundle=bundle,
                    key=key,
                    temporal_enabled=True,
                    handoff_policy="bounded_finalize_v2",
                )
            else:
                from evaluation.live_claude import run_live_claude

                trace = run_live_claude(bundle)
        except Exception as error:  # preserved as a run failure, never retried
            trace = {"case_id": replay["case_id"], "run_error": repr(error)}
        trace["cycle5_started_at"] = started
        _save_new(out, trace)
        print(arm, rid, (trace.get("validation") or {}).get("status"), flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, report_ids))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--source-dir", type=Path, default=ROOT / ".artifacts/public-source")
    r = sub.add_parser("run")
    r.add_argument("--arm", choices=("ultra", "sonnet"), required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--tag", default="", help="e.g. -rerun for provider-error reruns")
    r.add_argument("report_ids", nargs="+")
    args = parser.parse_args()
    if args.cmd == "prepare":
        prepare(args.source_dir)
    else:
        run(args.arm, args.report_ids, args.workers, args.tag)


if __name__ == "__main__":
    main()
