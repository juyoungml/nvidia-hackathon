"""Build two labeled probe cases from public PreDist observations.

These are evaluation transformations, not additional published incidents.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from copy import deepcopy
from pathlib import Path

NO_REPORT_TIME = dt.datetime(2016, 12, 10, 15, 55)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--base-replay", type=Path, default=Path("data/replay-52.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    base = json.loads(args.base_replay.read_text())
    if base["case_id"] != "PreDist-M1-fault-52":
        raise ValueError("derived probes require the public fault-52 base replay")

    no_report = deepcopy(base)
    no_report["case_id"] = "PreDist-M1-derived-no-report-20161210"
    no_report["decision_time"] = NO_REPORT_TIME.isoformat(sep=" ")
    no_report["current_report"] = {
        "source_id": "PreDist-M1-derived-no-report-20161210",
        "problem": "No incident report is supplied for this sampled window",
        "note": "Derived no-report probe; absence of a listed report is not proof of normal operation.",
    }
    window_start = NO_REPORT_TIME - dt.timedelta(hours=24)
    no_report["measurement_window"]["start"] = window_start.isoformat(sep=" ")
    no_report["measurement_window"]["end"] = no_report["decision_time"]
    rows = []
    sensor = args.source_dir / "substation_21.csv"
    with sensor.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream, delimiter=";"):
            when = dt.datetime.fromisoformat(row["timestamp"])
            if window_start <= when <= NO_REPORT_TIME:
                rows.append(
                    {
                        key: (value if key == "timestamp" else (float(value) if value else None))
                        for key, value in row.items()
                    }
                )
    if not rows:
        raise ValueError("no public observations in the derived no-report window")
    no_report["measurement_window"]["rows"] = rows
    no_report["prior_faults"] = [
        row
        for row in base["prior_faults"]
        if dt.datetime.fromisoformat(row["report_date"]) < NO_REPORT_TIME
    ]
    no_report["prior_disturbances"] = [
        row
        for row in base["prior_disturbances"]
        if dt.datetime.fromisoformat(row["event_start"]) < NO_REPORT_TIME
    ]
    no_report["derived_case"] = {
        "type": "no_report_window",
        "published_incident": False,
        "method": "Sample a public sensor window without supplying an incident report.",
        "limitation": "No report in this probe is not a verified normal label.",
    }
    no_report["provenance"]["selection"] = {
        "asset_id": "21",
        "decision_time": no_report["decision_time"],
        "window_hours": 24,
        "derived_from": "PreDist-M1-fault-52 public asset metadata",
    }

    missing = deepcopy(base)
    missing["case_id"] = "PreDist-M1-derived-missing-measurements-52"
    missing["measurement_window"]["rows"] = []
    missing["derived_case"] = {
        "type": "missing_measurements",
        "published_incident": False,
        "method": "Remove all public sensor rows from fault-52 replay; retain the complaint and earlier reports.",
        "limitation": "This is an artificial evidence outage, not a reported data-quality event.",
    }
    missing["provenance"]["selection"]["transformation"] = "remove measurement rows"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, replay in (("no-report-20161210", no_report), ("missing-measurements-52", missing)):
        path = args.output_dir / f"derived-{name}.json"
        path.write_text(json.dumps(replay, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {"path": str(path), "measurements": len(replay["measurement_window"]["rows"])}
            )
        )


if __name__ == "__main__":
    main()
