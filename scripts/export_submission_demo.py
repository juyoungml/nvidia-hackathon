"""Export a small, source-linked public replay for the static System 2 demo."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "29": ROOT / "evaluation/cycle4/traces/domain-29.json",
    "52": ROOT / "evaluation/cycle4/development/handoff-v2-case52.json",
}

# This assessment was made after the frozen run. It must not be written into
# trace.review_flags or treated as an original runtime validation result.
POSTRUN_REVIEW = {
    "29": {
        "kind": "independent_ai_content_screen",
        "source": "evaluation/readiness/content-review/v2/CONTENT_RESULTS.md",
        "expert_validated": False,
        "by_check": {
            "C-secondary-flow": [
                "점검 이유의 '공급온도가 설정값에 가깝다'는 비교에는 설정값 근거가 인용되지 않았습니다.",
                "'외기온 약 10°C'는 구간 첫 값 8.55°C를 시각 없이 부정확하게 요약했습니다.",
            ]
        },
    }
}


def export(case: str, source: Path) -> None:
    trace = json.loads(source.read_text())
    display = trace["display"]
    facts = {fact["id"]: fact for fact in trace["evidence"]["facts"]}
    checks = []
    selected_ids = set()
    for check in display["suggested_next_checks"]:
        ids = [fact["id"] for fact in check["because_facts"]]
        selected_ids.update(ids)
        checks.append(
            {
                "id": check["id"],
                "text": check["text"],
                "rationale": check["model_authored_suggestion_rationale"],
                "fact_ids": ids,
            }
        )
    selected_ids.update(item["id"] for item in display["observations"])
    output = {
        "case": case,
        "case_id": trace["case_id"],
        "decision_time": trace["evidence"]["decision_time"],
        "model": trace["model"],
        "method": trace["method"],
        "source_trace": str(source.relative_to(ROOT)),
        "source_corpus_sha256": trace["corpus_sha256"],
        "status": display["status"],
        "finish_reason": trace["finish_reason"],
        "development_only": trace.get("development_only", False),
        "budget_exhausted": trace.get("investigation_budget_exhausted", False),
        "review_notes": trace.get("review_notes", []),
        "postrun_review": POSTRUN_REVIEW.get(case),
        "observed_fact_ids": [item["id"] for item in display["observations"]],
        "facts": {fid: facts[fid] for fid in sorted(selected_ids)},
        "limits": display["limits"],
        "checks": checks,
        "tool_calls": [
            {"name": call["name"], "arguments": call["arguments"]} for call in trace["tool_calls"]
        ],
        "wall_seconds": trace["wall_seconds"],
    }
    target = ROOT / f"web/assets/system2-{case}.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"{target.relative_to(ROOT)}: {len(checks)} checks, {len(selected_ids)} cited facts")


if __name__ == "__main__":
    for case, source in CASES.items():
        export(case, source)
