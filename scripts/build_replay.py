"""Build attributed, time-safe replays from the public PreDist dataset."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

SOURCE_URL = "https://zenodo.org/records/19496480"
REPORT_ID = "52"
WINDOW_HOURS = 24


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value)


def numeric(value: str) -> float | None:
    if not value:
        return None
    return float(value)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--report-id", default=REPORT_ID)
    parser.add_argument("--window-hours", type=int, default=WINDOW_HOURS)
    args = parser.parse_args()

    if args.window_hours <= 0:
        parser.error("--window-hours must be positive")

    source_paths = {
        name: args.source_dir / name for name in ("faults.csv", "disturbances.csv", "features.csv")
    }
    faults = read_csv(source_paths["faults.csv"])
    disturbances = read_csv(source_paths["disturbances.csv"])
    features = read_csv(source_paths["features.csv"])
    matches = [row for row in faults if row["Event ID"] == args.report_id]
    if len(matches) != 1:
        raise ValueError(f"expected one report with ID {args.report_id}, found {len(matches)}")
    target = matches[0]
    asset_id = target["substation ID"]
    sensor_path = args.source_dir / f"substation_{asset_id}.csv"
    source_paths[sensor_path.name] = sensor_path
    decision_time = timestamp(target["Report date"])
    start_time = decision_time - dt.timedelta(hours=args.window_hours)
    prior_faults = [
        {
            "source_id": f"PreDist-M1-fault-{row['Event ID']}",
            "report_date": row["Report date"],
            "problem": row["Problem EN"],
            "event_description": row["Event description EN"],
        }
        for row in faults
        if row["substation ID"] == asset_id and timestamp(row["Report date"]) < decision_time
    ]
    prior_disturbances = [
        {
            "source_id": f"PreDist-M1-disturbance-{index}",
            "event_start": row["Event start"],
            "type": row["type"],
        }
        for index, row in enumerate(disturbances, 1)
        if row["substation ID"] == asset_id and timestamp(row["Event start"]) < decision_time
    ]
    measurements = []
    with sensor_path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            when = timestamp(row["timestamp"])
            if start_time <= when <= decision_time:
                measurements.append(
                    {
                        "timestamp": row["timestamp"],
                        **{
                            name: numeric(value)
                            for name, value in row.items()
                            if name != "timestamp"
                        },
                    }
                )
    if not measurements:
        raise ValueError(f"no measurements for substation {asset_id} before {decision_time}")

    case_id = f"PreDist-M1-fault-{args.report_id}"
    provenance = {
        "source_files_sha256": {name: file_sha256(path) for name, path in source_paths.items()},
        "selection": {
            "report_id": args.report_id,
            "asset_id": asset_id,
            "window_hours": args.window_hours,
            "cutoff": "measurement timestamp <= report date; prior records strictly earlier",
        },
    }

    replay = {
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
        "prior_faults": prior_faults,
        "prior_disturbances": prior_disturbances,
        "record_availability_note": (
            "Earlier report dates precede the decision time, but the dataset does not establish "
            "when their retrospective narratives became available to an operator."
        ),
        "features": {
            row["column"]: {"description": row["description"], "unit": row["unit"]}
            for row in features
        },
        "provenance": provenance,
    }
    held_out = {
        "case_id": replay["case_id"],
        "source": SOURCE_URL,
        "not_available_to_agent": True,
        "provenance": provenance,
        "report_date": target["Report date"],
        "event_description": target["Event description EN"],
        "fault_label": target["Fault label"],
        "note": "Published report fields are retrospective; they are not a real-time ground truth at the decision time.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / f"replay-{args.report_id}.json").write_text(
        json.dumps(replay, ensure_ascii=False, indent=2) + "\n"
    )
    evaluation_dir = args.output_dir.parent / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    (evaluation_dir / f"held-out-{args.report_id}.json").write_text(
        json.dumps(held_out, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "case_id": replay["case_id"],
                "measurements": len(measurements),
                "prior_faults": len(prior_faults),
                "prior_disturbances": len(prior_disturbances),
                "last_measurement": measurements[-1]["timestamp"] if measurements else None,
            }
        )
    )


if __name__ == "__main__":
    main()
