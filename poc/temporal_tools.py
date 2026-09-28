"""Bounded, read-only timing views of the public replay measurement rows."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math

from poc.temporal_evidence import SETPOINT_FIELD, SUPPLY_FIELD, build_temporal_evidence

WINDOW_FIELDS = (
    "outdoor_temperature",
    SUPPLY_FIELD,
    SETPOINT_FIELD,
    "p_net_meter_heat_power",
    "p_net_meter_flow",
)
MAX_WINDOW_ROWS = 24


def validate_public_replay(replay: dict) -> None:
    """Reject source records crossing the case's decision-time boundary."""
    cutoff = _timestamp(replay["decision_time"])
    window = replay["measurement_window"]
    start, end = _timestamp(window["start"]), _timestamp(window["end"])
    if not start <= end <= cutoff:
        raise ValueError("measurement window exceeds decision cutoff")
    for row in window["rows"]:
        stamp = _timestamp(row["timestamp"])
        if not start <= stamp <= end:
            raise ValueError("measurement row exceeds public pre-decision window")
    for record in replay.get("prior_faults", []):
        if _timestamp(record["report_date"]) >= cutoff:
            raise ValueError("prior report is not earlier than decision time")
    for record in replay.get("prior_disturbances", []):
        if _timestamp(record["event_start"]) >= cutoff:
            raise ValueError("prior disturbance is not earlier than decision time")


def _timestamp(value: object) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("timestamp must be an ISO string") from error
    if parsed.tzinfo is not None:
        raise ValueError("timezone-aware timestamps are not used in this replay")
    return parsed


def permitted_bounds(replay: dict) -> tuple[dt.datetime, dt.datetime]:
    window = replay["measurement_window"]
    start = _timestamp(window["start"])
    end = min(_timestamp(window["end"]), _timestamp(replay["decision_time"]))
    if start > end:
        raise ValueError("replay has no pre-decision measurement window")
    return start, end


def _row(row: dict) -> dict:
    return {"timestamp": row["timestamp"], **{field: row.get(field) for field in WINDOW_FIELDS}}


def permitted_window_fields(replay: dict) -> dict:
    """Expose the complete public pre-decision series used by both comparators."""
    start, end = permitted_bounds(replay)
    rows = []
    for row in replay["measurement_window"]["rows"]:
        try:
            stamp = _timestamp(row["timestamp"])
        except (KeyError, TypeError, ValueError):
            continue
        if start <= stamp <= end:
            rows.append(_row(row))
    return {
        "case_id": replay["case_id"],
        "source_id": replay["measurement_window"]["source_id"],
        "start": start.isoformat(sep=" "),
        "end": end.isoformat(sep=" "),
        "fields": list(WINDOW_FIELDS),
        "rows": rows,
    }


def query_window(replay: dict, *, start: str, end: str) -> dict:
    """Read at most 24 inclusive source rows within the decision cutoff."""
    lower, upper = permitted_bounds(replay)
    requested_start, requested_end = _timestamp(start), _timestamp(end)
    if not lower <= requested_start <= requested_end <= upper:
        raise ValueError("window is outside the public pre-decision cutoff")
    rows = [
        row
        for row in permitted_window_fields(replay)["rows"]
        if requested_start <= _timestamp(row["timestamp"]) <= requested_end
    ]
    if len(rows) > MAX_WINDOW_ROWS:
        raise ValueError(f"window contains more than {MAX_WINDOW_ROWS} rows")
    return {
        "case_id": replay["case_id"],
        "source_id": replay["measurement_window"]["source_id"],
        "start": start,
        "end": end,
        "fields": list(WINDOW_FIELDS),
        "rows": rows,
        "row_count": len(rows),
    }


def temporal_episodes(replay: dict) -> dict:
    """Compute descriptive supply/setpoint episodes from source timestamps."""
    return build_temporal_evidence(replay)


def _fact(source_id: str, field: str, value: dict, text: str) -> dict:
    encoded = json.dumps([source_id, field, value], sort_keys=True, ensure_ascii=False)
    return {
        "id": "F-" + hashlib.sha256(encoded.encode()).hexdigest()[:12],
        "source_id": source_id,
        "source_field": field,
        "interval": value.get("interval"),
        "value": value,
        "unit": "°C",
        "text": text,
    }


def _paired_text(label: str, sample: dict) -> str:
    return (
        f"{label} at {sample['timestamp']}: secondary supply {sample['supply_c']} °C, "
        f"setpoint {sample['setpoint_c']} °C, absolute gap {sample['absolute_gap_c']} °C"
    )


def temporal_facts(replay: dict, episodes: dict | None = None) -> list[dict]:
    """Immutable composite facts; each value keeps both readings and their timestamp."""
    episodes = episodes or temporal_episodes(replay)
    source_id = episodes["source_id"]
    facts = []
    for label in ("first", "last", "peak_gap"):
        sample = episodes["paired_series"].get(label)
        if sample is not None:
            value = {"interval": sample["timestamp"], "sample": sample}
            facts.append(
                _fact(source_id, f"temporal.paired_{label}", value, _paired_text(label, sample))
            )
    for index, episode in enumerate(episodes["episodes"], 1):
        first, last, peak = episode["first"], episode["last"], episode["peak"]
        interval = f"{first['timestamp']} to {last['timestamp']}"
        value = {
            "interval": interval,
            "sample_count": episode["sample_count"],
            "first": first,
            "last": last,
            "peak": peak,
            "rule": episodes["gap_rule"],
        }
        text = (
            f"Episode {index}, {interval}, {episode['sample_count']} consecutive paired samples "
            f"with absolute gap > {episodes['gap_rule']['threshold_c']} °C; "
            + _paired_text("first", first)
            + "; "
            + _paired_text("last", last)
            + "; "
            + _paired_text("peak", peak)
        )
        facts.append(_fact(source_id, f"temporal.episode.{index}", value, text))
    return facts


def window_facts(result: dict) -> list[dict]:
    """One source-bound paired fact per returned row with finite readings."""
    facts = []
    for row in result["rows"]:
        supply, setpoint = row.get(SUPPLY_FIELD), row.get(SETPOINT_FIELD)
        if any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in (supply, setpoint)
        ):
            continue
        sample = {
            "timestamp": row["timestamp"],
            "supply_c": supply,
            "setpoint_c": setpoint,
            "absolute_gap_c": round(abs(supply - setpoint), 6),
        }
        facts.append(
            _fact(
                result["source_id"],
                "temporal.window_pair",
                {"interval": row["timestamp"], "sample": sample},
                _paired_text("Paired reading", sample),
            )
        )
    return facts
