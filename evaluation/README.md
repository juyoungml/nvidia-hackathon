# 평가

모든 평가의 통과 기준은 **근거 연결 검사**입니다. 점검안이 스키마에 맞고, 인용한 근거 ID가 그 실행에서 실제로 조회한 사실인지를 봅니다. 진단 정확도, 인용이 설명을 뒷받침하는지, 현장 유용성은 판정하지 않습니다. 각 사이클의 프로토콜은 실행 전에 작성·고정했고, 이후 결과를 소급해 바꾸지 않습니다. 사이클 사이의 점수는 합산하지 않습니다.

## 사이클별 결과

| 평가 | 규모 | 요약 | 문서 |
|---|---|---|---|
| **Cycle 5 (현재 기준)** | PreDist 32건, 사건당 1회 | Sonnet 5 32/32, Nemotron 3 Ultra 첫 시도 15/32 → API 오류 재실행 후 26/32 (81%) → 24행 도구 보정 후 32/32, 남은 실패 6건은 모두 24행 초과 시간 창 요청 | [PROTOCOL](cycle5/PROTOCOL.md) · [RESULTS](cycle5/RESULTS.md) |
| Cycle 4 | 4건 | 실제 조사 루프와 시점별 근거. Ultra 2/4, Sonnet 5 4/4 | [PROTOCOL](cycle4/PROTOCOL.md) · [RESULTS](cycle4/RESULTS.md) |
| Cycle 3 | 개발/시험 분리 | 검증 피드백 한 번으로 출력을 복구할 수 있는지 시험 | [PROTOCOL](cycle3/PROTOCOL.md) · [RESULTS](cycle3/RESULTS.md) |
| System 2 비교 v1/v2 | 파일럿 | 초기 System 2와 Claude Code + Sonnet 5 비교 | [SYSTEM2_PROTOCOL](SYSTEM2_PROTOCOL.md) · [RESULTS](system2-results/RESULTS.md) |
| 초기 replay 비교 | 3건 + 점검용 2건 | 결정적 요약 기준선과 Nano/Ultra trace 구조 비교 (아래 설명) | [results/](results/README.md) |

## 보조 검토

- [내용 평가 v2](readiness/content-review/v2/CONTENT_RESULTS.md): 표시된 점검 문구를 가린 채 AI 검토자가 채점한 내부 선별 결과 (전문가 검증 아님). 첫 검토는 [ERRATUM](readiness/content-review/ERRATUM.md)과 함께 기록으로 남겼습니다.
- [trajectory 감사](audit-results/trajectory-audit.md): 두 구성의 조회 경로에 같은 휴리스틱을 적용한 검토 신호.
- [제출 준비도](readiness/): 기준([RUBRIC](readiness/RUBRIC.md)), 점검표([SCORECARD](readiness/SCORECARD.md)), QA 기록.

## 파일 구성

```text
cycle3/ cycle4/ cycle5/   사이클별 프로토콜, 사건 입력·해시, trace, 결과
held-out-*.json           초기 replay 사건의 회고 라벨 (모델 입력·웹 서버에서 제외)
holdout-outcomes/         holdout 사건의 회고 라벨 (모델 입력·웹 서버에서 제외)
readiness/                제출 준비도, 내용 평가, ablation
results/ system2-results/ audit-results/   초기 비교와 감사 결과
*.py                      실행·비교·감사 스크립트 (run_live_cycle.py 등)
```

## 초기 replay 비교 스크립트 (영문)

`evaluate.py` builds the same deterministic search-and-summary baseline for each replay and checks saved agent traces. The baseline reads the same replay fields available to the agent, but does not call a model or tools. This is a narrow reference response, not an optimized plant operator or diagnostic oracle.

The automated checks report whether cited IDs exist in the replay, whether tag-like signal names are defined, whether uncertainty wording appears, tool calls, and model request latency. They do **not** establish that a citation supports its sentence, that uncertainty is appropriate, that a suggested check is useful or safe, or that a root cause was correctly diagnosed. The full final answers remain in the result JSON for human review. API request time is separate from field identification time, which has not been measured.

Three replays (`52`, `62`, `32`) correspond to actual published incident rows. The two `derived-*.json` files are separately labeled probes for a no-report sensor window and an artificial evidence outage; they must not be counted as real incidents or evidence of a true-negative operating state. The historical reports are only filtered by report date; narrative availability at the replay time remains unverified.

Run the structural comparison with:

```sh
uv run python evaluation/run_cases.py --output-dir .artifacts/poc-runs
```

This invokes local Ollama Nano and hosted NVIDIA Ultra serially; the no-report probe stops at the Nano gate even if the gate says to escalate, so it measures the gate error without an unnecessary Ultra request. Individual traces have unique filenames and are never overwritten. To run only the no-report probe, pass `--case data/derived-no-report-20161210.json`.

Compare any selected trace set with:

```sh
uv run python evaluation/evaluate.py \
  --replay data/replay-52.json --replay data/replay-62.json --replay data/replay-32.json \
  --replay data/derived-no-report-20161210.json \
  --replay data/derived-missing-measurements-52.json \
  --trace .artifacts/poc-runs/trace-52-<model>.json \
  --output evaluation/results/comparison.json
```

Repeat `--trace` for each saved run. Traces must match a listed replay `case_id`. No held-out file is read by this evaluator; those files are for later manual retrospective analysis only.
