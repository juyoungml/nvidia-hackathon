"""Source-bound timing evidence from public PreDist replay measurements.

The 2 °C threshold describes the prior POC's tracking convention. It is not
an operational limit and the output makes no fault or control-cause inference.
"""

from __future__ import annotations

import datetime as dt
import math
from decimal import Decimal

SUPPLY_FIELD = "s_hc1_supply_temperature"
SETPOINT_FIELD = "s_hc1_supply_temperature_setpoint"


def _time(value: object) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _sample(row: dict, index: int) -> dict | None:
    supply = _number(row.get(SUPPLY_FIELD))
    setpoint = _number(row.get(SETPOINT_FIELD))
    if supply is None or setpoint is None:
        return None
    return {
        "row_index": index,
        "timestamp": row["timestamp"],
        "supply_c": supply,
        "setpoint_c": setpoint,
        "absolute_gap_c": float(abs(Decimal(str(supply)) - Decimal(str(setpoint)))),
    }


def _episode(samples: list[dict]) -> dict:
    return {
        "sample_count": len(samples),
        "first": samples[0],
        "last": samples[-1],
        "peak": max(samples, key=lambda sample: sample["absolute_gap_c"]),
    }


def build_temporal_evidence(
    replay: dict,
    *,
    threshold_c: float = 2.0,
    sample_interval_seconds: int = 600,
    max_episodes: int = 12,
    window_start: str | None = None,
    window_end: str | None = None,
) -> dict:
    """Return bounded, descriptive timing facts from one public replay input.

    An episode contains consecutive source rows with valid paired readings,
    strictly increasing timestamps exactly one expected interval apart, and
    absolute supply/setpoint gap > ``threshold_c``. Invalid, missing, duplicate,
    or irregular rows break continuity; readings are never interpolated.
    Optional inclusive bounds can narrow the replay window, never extend it.
    """
    if _number(threshold_c) is None or threshold_c < 0:
        raise ValueError("threshold_c must be finite and nonnegative")
    if type(sample_interval_seconds) is not int or sample_interval_seconds <= 0:
        raise ValueError("sample_interval_seconds must be positive")
    if type(max_episodes) is not int or max_episodes < 0:
        raise ValueError("max_episodes must be nonnegative")

    source_window = replay["measurement_window"]
    start = _time(source_window["start"])
    end = _time(source_window["end"])
    decision = _time(replay["decision_time"])
    selected_start = _time(window_start) if window_start is not None else start
    selected_end = _time(window_end) if window_end is not None else end
    try:
        valid_window = (
            start is not None
            and end is not None
            and decision is not None
            and selected_start is not None
            and selected_end is not None
            and start <= selected_start <= selected_end <= end
        )
        cutoff = min(end, decision) if valid_window else None
        valid_window = valid_window and selected_start <= cutoff
    except TypeError:
        valid_window = False
    if not valid_window:
        raise ValueError("invalid or out-of-range replay/window timestamps")

    rows = source_window.get("rows", [])
    counts = {
        "source_rows": len(rows),
        "selected_rows": 0,
        "valid_paired_samples": 0,
        "above_threshold_samples": 0,
        "missing_or_nonfinite_pair": 0,
        "invalid_timestamp": 0,
        "outside_selected_window_or_after_cutoff": 0,
        "irregular_intervals": 0,
    }
    valid_samples: list[dict] = []
    episodes: list[dict] = []
    current: list[dict] = []
    previous_time: dt.datetime | None = None
    previous_index: int | None = None
    step = dt.timedelta(seconds=sample_interval_seconds)

    def finish() -> None:
        if current:
            episodes.append(_episode(current))
            current.clear()

    for index, row in enumerate(rows):
        timestamp = _time(row.get("timestamp")) if isinstance(row, dict) else None
        if timestamp is None:
            counts["invalid_timestamp"] += 1
            finish()
            previous_time = None
            previous_index = None
            continue
        try:
            in_window = selected_start <= timestamp <= selected_end and timestamp <= cutoff
        except TypeError:
            in_window = False
        if not in_window:
            counts["outside_selected_window_or_after_cutoff"] += 1
            finish()
            previous_time = None
            previous_index = None
            continue
        counts["selected_rows"] += 1
        sample = _sample(row, index)
        if sample is None:
            counts["missing_or_nonfinite_pair"] += 1
            finish()
            previous_time = None
            previous_index = None
            continue
        counts["valid_paired_samples"] += 1
        valid_samples.append(sample)
        contiguous = previous_time is None or (
            previous_index == index - 1 and timestamp - previous_time == step
        )
        if previous_time is not None and not contiguous:
            counts["irregular_intervals"] += 1
            finish()
        if sample["absolute_gap_c"] > threshold_c:
            counts["above_threshold_samples"] += 1
            current.append(sample)
        else:
            finish()
        previous_time = timestamp
        previous_index = index
    finish()

    peak = max(valid_samples, key=lambda sample: sample["absolute_gap_c"], default=None)
    # Retain the largest observed episodes when the selectable result is bounded.
    # Their original order is restored so no omitted span implies continuity.
    ranked = sorted(
        episodes,
        key=lambda episode: (-episode["peak"]["absolute_gap_c"], episode["first"]["row_index"]),
    )[:max_episodes]
    shown = sorted(ranked, key=lambda episode: episode["first"]["row_index"])
    asset_id = replay.get("asset", {}).get("substation_id")
    hashes = replay.get("provenance", {}).get("source_files_sha256", {})
    csv_name = f"substation_{asset_id}.csv" if asset_id is not None else None
    return {
        "schema_version": 1,
        "case_id": replay["case_id"],
        "source_id": source_window["source_id"],
        "source": replay.get("source"),
        "provenance": {
            "operational_csv": csv_name,
            "operational_csv_sha256": hashes.get(csv_name),
            "source_selection": replay.get("provenance", {}).get("selection"),
        },
        "fields": {"supply_c": SUPPLY_FIELD, "setpoint_c": SETPOINT_FIELD},
        "window": {
            "source_start": source_window["start"],
            "source_end": source_window["end"],
            "selected_start": window_start or source_window["start"],
            "selected_end": window_end or source_window["end"],
            "decision_cutoff": replay["decision_time"],
            "effective_cutoff": cutoff.isoformat(sep=" "),
            "expected_sample_interval_seconds": sample_interval_seconds,
        },
        "gap_rule": {
            "operator": ">",
            "threshold_c": threshold_c,
            "status": "descriptive prior-POC convention; not a verified operational limit",
        },
        "counts": counts,
        "paired_series": {
            "first": valid_samples[0] if valid_samples else None,
            "last": valid_samples[-1] if valid_samples else None,
            "peak_gap": peak,
        },
        "episode_count": len(episodes),
        "episodes_returned": len(shown),
        "episodes_truncated": len(episodes) > len(shown),
        "episodes": shown,
        "interpretation_limit": (
            "Timing and gap at this secondary supply sensor do not establish room heat, "
            "fault, controller action, or cause. No interpolation is performed."
        ),
    }
