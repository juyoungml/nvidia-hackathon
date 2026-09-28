"""Join the completed blind review to its held-back identity key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND_REVIEW_SHA256_BEFORE_REVEAL = (
    "a62becf0b6ea51a09f76bc58c05415bcd8be8baecd12c7d5eb955a2dc6546e7b"
)
PACKETS_SHA256_BEFORE_REVIEW = "580bf00669cb453ab88b671f4d0e5ab874c4ca25275731c1b94fd5877fca7aa3"
CRITERIA = ("grounding", "component_meaning", "actionability", "uncertainty")


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_summary() -> dict:
    review_path = HERE / "BLIND_REVIEW.json"
    packet_path = HERE / "PACKETS.json"
    if digest(review_path) != BLIND_REVIEW_SHA256_BEFORE_REVEAL:
        raise ValueError("Blind review changed after its pre-reveal hash was recorded")
    if digest(packet_path) != PACKETS_SHA256_BEFORE_REVIEW:
        raise ValueError("Review packets changed after review")
    review = load(review_path)
    packets = load(packet_path)
    key = load(HERE / "REVEAL_KEY.json")
    packet_by_label = {p["label"]: p for p in packets["packets"]}
    if set(packet_by_label) != set(key["labels"]):
        raise ValueError("Packet and reveal labels differ")
    if {p["label"] for p in review["packets"]} != set(packet_by_label):
        raise ValueError("Review and packet labels differ")
    rows = []
    for scored in review["packets"]:
        label = scored["label"]
        original = packet_by_label[label]
        if scored["case"] != original["case"]:
            raise ValueError("Reviewed case differs from packet")
        source = key["labels"][label]
        if source["case"] != scored["case"]:
            raise ValueError("Reveal case differs from review")
        source_path = HERE.parents[2] / source["trace"]
        if digest(source_path) != source["trace_sha256"]:
            raise ValueError("Frozen trace changed after packet creation")
        original_checks = {c["id"]: c for c in original["checks"]}
        if {c["id"] for c in scored["checks"]} != set(original_checks):
            raise ValueError("Reviewed checks differ from packet")
        if any(
            c["total"] != sum(c["scores"][name] for name in CRITERIA)
            or any(c["scores"][name] not in (0, 1, 2) for name in CRITERIA)
            or (c["missing_grounding"] and c["scores"]["grounding"] != 0)
            for c in scored["checks"]
        ):
            raise ValueError("Review scores violate fixed rubric")
        total = sum(c["total"] for c in scored["checks"])
        if total != scored["total"] or scored["maximum"] != 8 * len(scored["checks"]):
            raise ValueError("Review packet total differs from checks")
        rows.append(
            {
                "case": scored["case"],
                "arm": source["arm"],
                "blind_label": label,
                "score": total,
                "maximum": scored["maximum"],
                "missing_grounding_checks": [
                    {"check_id": c["id"], "unsupported_claim": c["missing_support"]}
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
    if paired["domain"]["cases"] != [3, 29] or paired["general"]["cases"] != [3, 29]:
        raise ValueError("Content comparison must remain the original paired valid cases")
    return {
        "blind_review_sha256_before_reveal": BLIND_REVIEW_SHA256_BEFORE_REVEAL,
        "packets_sha256_before_review": PACKETS_SHA256_BEFORE_REVIEW,
        "reviewer": review["reviewer"],
        "paired_valid_outputs_only": rows,
        "paired_content_totals": paired,
        "fixed_cycle4_all_case_contract_success": {
            "domain": {"valid": 2, "denominator": 4, "failed_cases": [52, 47]},
            "general": {"valid": 4, "denominator": 4, "failed_cases": []},
        },
        "development_handoff_52": "Separate post-run development confirmation; excluded from primary and paired scores",
        "limit": "AI screening without independently verified plant expertise; no diagnosis accuracy or model/harness superiority claim",
    }


if __name__ == "__main__":
    output = build_summary()
    (HERE / "CONTENT_RESULTS.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
