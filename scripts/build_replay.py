"""Build one attributed, time-safe replay from the public PreDist dataset."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path


SOURCE_URL = "https://zenodo.org/records/19496480"
REPORT_ID = "52"
ASSET_ID = "21"
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    faults = read_csv(args.source_dir / "faults.csv")
    disturbances = read_csv(args.source_dir / "disturbances.csv")
    features = read_csv(args.source_dir / "features.csv")
    target = next(row for row in faults if row["Event ID"] == REPORT_ID)
    assert target["substation ID"] == ASSET_ID
    decision_time = timestamp(target["Report date"])
    start_time = decision_time - dt.timedelta(hours=WINDOW_HOURS)
    prior_faults = [
        {
            "source_id": f"PreDist-M1-fault-{row['Event ID']}",
            "report_date": row["Report date"],
            "problem": row["Problem EN"],
            "event_description": row["Event description EN"],
        }
        for row in faults
        if row["substation ID"] == ASSET_ID and timestamp(row["Report date"]) < decision_time
    ]
    prior_disturbances = [
        {
            "source_id": f"PreDist-M1-disturbance-{index}",
            "event_start": row["Event start"],
            "type": row["type"],
        }
        for index, row in enumerate(disturbances, 1)
        if row["substation ID"] == ASSET_ID and timestamp(row["Event start"]) < decision_time
    ]
    measurements = []
    with (args.source_dir / "substation_21.csv").open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            when = timestamp(row["timestamp"])
            if start_time <= when <= decision_time:
                measurements.append({
                    "timestamp": row["timestamp"],
                    **{name: numeric(value) for name, value in row.items() if name != "timestamp"},
                })

    replay = {
        "source": {
            "dataset": "PreDist v2",
            "url": SOURCE_URL,
            "doi": "10.5281/zenodo.19496480",
            "license": "CC BY 4.0",
            "publisher": "Fraunhofer IEE / enercity Netz GmbH",
            "asset_type": "district heating substation",
        },
        "case_id": "PreDist-M1-fault-52",
        "asset": {"manufacturer": 1, "substation_id": ASSET_ID},
        "decision_time": decision_time.isoformat(sep=" "),
        "current_report": {
            "source_id": "PreDist-M1-fault-52-problem-only",
            "problem": target["Problem EN"],
            "note": "Only the reported problem is visible at decision time. Later diagnosis and remedy are withheld.",
        },
        "measurement_window": {
            "start": start_time.isoformat(sep=" "),
            "end": decision_time.isoformat(sep=" "),
            "source_id": "PreDist-M1-substation-21-operational-data",
            "rows": measurements,
        },
        "prior_faults": prior_faults,
        "prior_disturbances": prior_disturbances,
        "features": {
            row["column"]: {"description": row["description"], "unit": row["unit"]}
            for row in features
        },
    }
    held_out = {
        "case_id": replay["case_id"],
        "source": SOURCE_URL,
        "not_available_to_agent": True,
        "report_date": target["Report date"],
        "event_description": target["Event description EN"],
        "fault_label": target["Fault label"],
        "note": "Published report fields are retrospective; they are not a real-time ground truth at the decision time.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "replay-52.json").write_text(json.dumps(replay, ensure_ascii=False, indent=2) + "\n")
    evaluation_dir = args.output_dir.parent / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    (evaluation_dir / "held-out-52.json").write_text(json.dumps(held_out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "case_id": replay["case_id"],
        "measurements": len(measurements),
        "prior_faults": len(prior_faults),
        "prior_disturbances": len(prior_disturbances),
        "last_measurement": measurements[-1]["timestamp"] if measurements else None,
    }))


if __name__ == "__main__":
    main()
