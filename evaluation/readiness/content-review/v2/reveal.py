"""Validate frozen v2 blind review, then join to held-back identity key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BLIND_REVIEW_SHA256_BEFORE_REVEAL = (
    "eb2c91ff3da870b309bc93db768aaf3a2baf984f7db9bbf90e67dde876c7f1f6"
)
PACKETS_SHA256_BEFORE_REVIEW = "b6b906712190b46e42a7bb7ebb47398f89ea850f08e5ab83c62b3e79f2a67c07"


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_summary() -> dict:
    if digest(HERE / "BLIND_REVIEW.json") != BLIND_REVIEW_SHA256_BEFORE_REVEAL:
        raise ValueError("v2 blind review changed after pre-reveal hash")
    if digest(HERE / "PACKETS.json") != PACKETS_SHA256_BEFORE_REVIEW:
        raise ValueError("v2 packets changed after review")
    review = read(HERE / "BLIND_REVIEW.json")
    packets = {p["label"]: p for p in read(HERE / "PACKETS.json")["packets"]}
    key = read(HERE / "REVEAL_KEY.json")["labels"]
    if set(packets) != set(key) or {p["label"] for p in review["packets"]} != set(key):
        raise ValueError("v2 review, packet, and key labels differ")
    rows = []
    for scored in review["packets"]:
        label = scored["label"]
        packet = packets[label]
        source = key[label]
        if scored["case"] != packet["case"] or scored["case"] != source["case"]:
            raise ValueError("v2 case identity differs")
        if digest(ROOT / source["trace"]) != source["trace_sha256"]:
            raise ValueError("v2 source trace changed")
        if {c["id"] for c in scored["checks"]} != {c["id"] for c in packet["checks"]}:
            raise ValueError("v2 reviewed checks differ from packet")
        for check in scored["checks"]:
            scores = check["scores"]
            if len(scores) != 4 or any(score not in (0, 1, 2) for score in scores):
                raise ValueError("v2 criterion scores out of range")
            if sum(scores) != check["total"]:
                raise ValueError("v2 check arithmetic differs")
            if check["missing_grounding"] and (scores[0] != 0 or not check["unsupported_claim"]):
                raise ValueError("v2 missing grounding violates rubric")
        total = sum(c["total"] for c in scored["checks"])
        if total != scored["total"] or scored["maximum"] != len(scored["checks"]) * 8:
            raise ValueError("v2 packet arithmetic differs")
        rows.append(
            {
                "case": scored["case"],
                "arm": source["arm"],
                "blind_label": label,
                "score": total,
                "maximum": scored["maximum"],
                "missing_grounding_checks": [
                    {"check_id": c["id"], "unsupported_claim": c["unsupported_claim"]}
                    for c in scored["checks"]
                    if c["missing_grounding"]
                ],
            }
        )
    paired = {
        arm: {
            "score": sum(row["score"] for row in rows if row["arm"] == arm),
            "maximum": sum(row["maximum"] for row in rows if row["arm"] == arm),
            "cases": sorted(row["case"] for row in rows if row["arm"] == arm),
        }
        for arm in ("domain", "general")
    }
    if any(paired[arm]["cases"] != [3, 29] or paired[arm]["maximum"] != 48 for arm in paired):
        raise ValueError("v2 paired denominator changed")
    if sum(row["score"] for row in rows) != review["overall"]["score"]:
        raise ValueError("v2 review grand total differs")
    return {
        "blind_review_sha256_before_reveal": BLIND_REVIEW_SHA256_BEFORE_REVEAL,
        "packets_sha256_before_review": PACKETS_SHA256_BEFORE_REVIEW,
        "reviewer_type": review["reviewer_type"],
        "independently_verified_plant_expertise": review["independently_verified_plant_expertise"],
        "paired_valid_outputs_only": rows,
        "paired_content_totals": paired,
        "fixed_cycle4_all_case_contract_success": {
            "domain": {"valid": 2, "denominator": 4, "failed_cases": [52, 47]},
            "general": {"valid": 4, "denominator": 4, "failed_cases": []},
        },
        "development_handoff_52": "Separate post-run development confirmation; excluded from primary and paired scores",
        "limit": "AI content screen without verified plant expertise; no diagnosis accuracy or model/harness superiority claim",
    }


if __name__ == "__main__":
    (HERE / "CONTENT_RESULTS.json").write_text(
        json.dumps(build_summary(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
