# Plant Reliability Agent

> **최신 실행 체크포인트:** [Cycle 4 실제 조사 비교](evaluation/cycle4/RESULTS.md). Ultra 2/4, Sonnet 5 4/4가 출력·참조 검사를 통과했다. 두 Ultra 실패는 조회 예산 후 최종 생성 전환 문제였고, 별도 개발 수정은 기존 사례 1건에서 확인했다. 원래 비교 수치는 보존하며 진단 정확도·하네스 우위로 해석하지 않는다. 아래 이전 주기 결과는 이 최신 기록과 구분한다.

**에너지 설비의 알람을, 근거 있는 다음 점검으로.** NVIDIA Korea Agentic AI Hackathon 2026 공개 자료 기반 POC입니다. 회사·고객 자료를 사용하지 않습니다. 현재 서비스명은 임시명입니다.

## 먼저 보기 — API 키 불필요

Python 3.12+ 환경에서 저장소 루트로 이동합니다.

```sh
python3 scripts/serve_demo.py --port 8772
```

- 랜딩: http://127.0.0.1:8772/web/
- **실제 Nano → Ultra 실행 기록 재생:** http://127.0.0.1:8772/web/investigation.html
- 공개 계측·수동 bbox 탐색: http://127.0.0.1:8772/web/evidence.html

서버는 127.0.0.1에만 바인딩하고 정해진 공개 파일만 제공합니다. `.env`, `.git`, 임의 경로와 사후 평가 데이터는 제공하지 않습니다. 저장 trace 재생은 실시간 모델 호출이 아닙니다.

## 실제 실행 범위

- 공개 PreDist 지역난방 설비의 신고를 당시 정보로 재생합니다. 현재 사건의 사후 진단은 모델 입력에서 제외했습니다.
- 로컬 Ollama `nemotron-3-nano:4b`가 집계 특징과 신고를 보고 좁은 선별 결정을 내립니다. 출처 종류를 검증한 뒤 프로그램이 정확한 원본 ID를 연결합니다.
- hosted NIM `nvidia/nemotron-3-ultra-550b-a55b`가 읽기 도구로 계측·이전 기록을 조회하고 다음 점검을 제안합니다.
- [NAT 1.8.0 별도 도구 워크플로](integrations/README.md)는 세 공개 도구 호출을 실행했습니다. 모델 루프 전체가 NAT에서 실행된 것은 아닙니다.
- [OpenShell 0.1.2 최소 정책 시험](integrations/openshell-README.md)은 허용 읽기와 비허용 파일 읽기·쓰기·직접 TCP 차단을 확인했습니다. 공개 fixture만 대상으로 했으며 모델 루프 보호 검증은 아닙니다.
- DOE 원본 계통도 영역은 수동 지정입니다. PreDist 사건의 도면이 아니며, 자동 도면 이해 정확도를 입증하지 않습니다.

결과와 실패: [POC_RESULT.md](POC_RESULT.md), [평가 자료](evaluation/results), [공급자·출력 실패 기록](poc/runtime-probe-log.json). 8시간→30분은 기준 가정과 목표이며 실측 식별 시간 개선이 아닙니다.

## 모델 재실행

```sh
uv sync --group dev --locked
ollama pull nemotron-3-nano:4b
# .env에 본인 NVIDIA_API_KEY를 입력합니다. 키를 커밋하거나 공유하지 마세요.
uv run python poc/run.py --mode pipeline --replay data/replay-52.json
```

Ollama 서버가 로컬 11434 포트에서 실행되어 있어야 합니다. `.env` 형식은 `NVIDIA_API_KEY=본인키`입니다. 키가 포함된 파일은 제출 ZIP에 없습니다. 실패한 hosted Nano 모델을 성공한 것으로 대체하지 않았고, 현재 재현 경로는 로컬 Nano + hosted Ultra입니다.

기본 trace는 `.artifacts/poc-runs/` 아래 고유 파일명으로 저장합니다. 정적 데모는 검토한 `poc/trace-52-pipeline.json`을 읽습니다. NVIDIA 호출은 프로세스당 18 rpm으로 제한합니다. 계정 전체 40 rpm이므로 다른 프로세스와 합산해 관리해야 합니다.

## 평가·품질

```sh
uv run ruff check .
uv run ruff format --check .
uv run vulture poc scripts tests integrations submission evaluation --min-confidence 80
uv run python -m unittest discover -s tests -v
node --check web/landing.js
node --check web/investigation.js
```

실제 사건과 파생 스트레스 시험을 구분합니다. 출처 ID 존재·미정의 신호·불확실성 표현 검사는 구조 검사이며 진단 정확도를 뜻하지 않습니다. API 시간은 현장 원인 식별 시간과 다릅니다. 과거 신고 날짜는 확인되지만 그 회고적 서술의 실제 공개 시점은 확인되지 않았습니다.

## 자료와 제출

내용 검토는 [마크다운 보고서](submission/REPORT.md)와 [심사 피드백 검토](submission/REVIEW_RESPONSE.md)를 기준으로 합니다. 기존 PDF·ZIP은 이전 검토본이며, 내용 확정 후 재생성해야 합니다.

- [공개 데이터 출처](data/README.md) / [이미지·도면 출처](web/assets/SOURCES.md)
- [전략](STRATEGY.md) / [현재 계획](PLAN.md) / [아키텍처](ARCHITECTURE.md)
- [폼 초안](submission/FORM_DRAFT.md) / [2분 발표 동선](submission/DEMO_SCRIPT.md)

제출 파일은 설명 PDF, 실행 코드, 공개 자료와 저장된 결과를 담은 ZIP으로 준비합니다. private GitHub 접근 권한을 심사위원에게 요구하지 않습니다. 팀명·2~5인 구성·팀원 전원의 개별 신청은 제출 전 확인해야 합니다. 사용자 제공 공고의 마감은 2026-09-28 23:59 KST입니다.
