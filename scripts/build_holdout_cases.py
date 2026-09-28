"""Rebuild the fixed, untouched PreDist cross-substation comparison cases.

Extract the public manufacturer-1 CSVs named in data/README.md from the
official PreDist v2 archive before running this script. The original batch
was fixed before its model runs: reports 60 (substation 4) and 63
(substation 7). The next batch used reports 3 (substation 12) and 13
(substation 24). The third batch uses reports 37 (substation 19) and 5
(substation 11), selected from public metadata before cycle-3 inference.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

from build_replay import SOURCE_URL, file_sha256, numeric, read_csv, timestamp

CASES = {
    "original": (("60", "4"), ("63", "7")),
    "next": (("3", "12"), ("13", "24")),
    "third": (("37", "19"), ("5", "11")),
}
REQUIRED_FIELDS = (
    "s_hc1_supply_temperature",
    "s_hc1_supply_temperature_setpoint",
    "p_hc1_return_temperature",
)
SELECTION_RULE = {
    "original": (
        "First two chronological manufacturer-1 reports with problem 'no heat' or "
        "'not enough heat', outside substation 21 and on distinct substations, "
        "having >=100 prior-24-hour samples and nonempty required hc1 fields; "
        "selection fixed before model runs."
    ),
    "next": (
        "First two chronological manufacturer-1 reports with problem 'no heat' or "
        "'not enough heat', outside substations 21, 4, and 7 and on distinct "
        "substations, having >=100 prior-24-hour samples and nonempty required "
        "hc1 fields; choice of reports 3 and 13 frozen before second comparison."
    ),
    "third": (
        "First two chronological manufacturer-1 reports with problem 'no heat' or "
        "'not enough heat', outside substations 21, 4, 7, 12, and 24 and on "
        "distinct substations, having >=100 prior-24-hour samples and nonempty "
        "required hc1 fields; reports 37 and 5 selected before cycle-3 inference."
    ),
}


def build(source_dir: Path, output_dir: Path, batch: str = "original") -> None:
    common = {
        name: source_dir / name for name in ("faults.csv", "disturbances.csv", "features.csv")
    }
    faults = read_csv(common["faults.csv"])
    disturbances = read_csv(common["disturbances.csv"])
    features = read_csv(common["features.csv"])
    outcome_dir = output_dir.parent / "evaluation" / "holdout-outcomes"
    output_dir.mkdir(parents=True, exist_ok=True)
    outcome_dir.mkdir(parents=True, exist_ok=True)

    for report_id, asset_id in CASES[batch]:
        matches = [row for row in faults if row["Event ID"] == report_id]
        if len(matches) != 1:
            raise ValueError(f"expected one report {report_id}, found {len(matches)}")
        target = matches[0]
        if target["substation ID"] != asset_id or target["Problem EN"].strip().lower() not in (
            "no heat",
            "not enough heat",
        ):
            raise ValueError(f"fixed selection no longer matches report {report_id}")
        decision_time = timestamp(target["Report date"])
        start_time = decision_time - dt.timedelta(hours=24)
        sensor_path = source_dir / f"substation_{asset_id}.csv"
        measurements: list[dict] = []
        with sensor_path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream, delimiter=";")
            if not set(REQUIRED_FIELDS).issubset(reader.fieldnames or []):
                raise ValueError(f"missing hc1 columns for substation {asset_id}")
            for row in reader:
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
        if len(measurements) < 100 or any(
            row[field] is None for row in measurements for field in REQUIRED_FIELDS
        ):
            raise ValueError(f"report {report_id} fails measurement eligibility")

        case_id = f"PreDist-M1-fault-{report_id}"
        source_paths = {**common, sensor_path.name: sensor_path}
        provenance = {
            "source_files_sha256": {name: file_sha256(path) for name, path in source_paths.items()},
            "selection": {
                "rule": SELECTION_RULE[batch],
                "report_id": report_id,
                "asset_id": asset_id,
                "window_hours": 24,
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
            "prior_faults": [
                {
                    "source_id": f"PreDist-M1-fault-{row['Event ID']}",
                    "report_date": row["Report date"],
                    "problem": row["Problem EN"],
                    "event_description": row["Event description EN"],
                }
                for row in faults
                if row["substation ID"] == asset_id
                and timestamp(row["Report date"]) < decision_time
            ],
            "prior_disturbances": [
                {
                    "source_id": f"PreDist-M1-disturbance-{index}",
                    "event_start": row["Event start"],
                    "type": row["type"],
                }
                for index, row in enumerate(disturbances, 1)
                if row["substation ID"] == asset_id
                and timestamp(row["Event start"]) < decision_time
            ],
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
        outcome = {
            "case_id": case_id,
            "source": SOURCE_URL,
            "not_available_to_agent": True,
            "provenance": provenance,
            "report_date": target["Report date"],
            "event_description": target["Event description EN"],
            "fault_label": target["Fault label"],
            "note": "Published report fields are retrospective; they are not a real-time ground truth at the decision time.",
        }
        (output_dir / f"holdout-{report_id}.json").write_text(
            json.dumps(replay, ensure_ascii=False, indent=2) + "\n"
        )
        (outcome_dir / f"holdout-{report_id}.json").write_text(
            json.dumps(outcome, ensure_ascii=False, indent=2) + "\n"
        )
        print(
            json.dumps(
                {
                    "case_id": case_id,
                    "input": str(output_dir / f"holdout-{report_id}.json"),
                    "measurements": len(measurements),
                    "prior_faults": len(replay["prior_faults"]),
                    "prior_disturbances": len(replay["prior_disturbances"]),
                }
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--batch", choices=CASES, default="original")
    args = parser.parse_args()
    build(args.source_dir, args.output_dir, args.batch)


if __name__ == "__main__":
    main()
