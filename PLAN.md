# Plan — feasibility, demo, submission

## 오늘의 순서

1. 팀 2~5인과 계정·팀명을 확정한다. 전원 개별 신청이 필요하다.
2. [DATA_SOURCES.md](DATA_SOURCES.md)의 공개 데이터 접근성과 라이선스를 확인하고, 실제 관측 사건 하나를 고른다.
3. 그 사건의 당시 자료만 도구로 연결해 Nemotron의 실제 도구 호출을 시험한다.
4. 정상/상충/근거 부족 세 경우를 검증한다.
5. 시간 여유가 있을 때만 NeMo Agent Toolkit과 NemoClaw/OpenShell 통합을 시도한다.
6. 22:30 KST까지 제출 PDF와 링크를 검수하고 팀원별 제출을 시작한다.

## 공개 사건 재생과 평가

첫 사건은 공개 데이터의 실제 관측 구간을 기준으로 고른다. 같은 데이터에서 정상 구간, 모순이 있는 구간, 정보가 부족한 구간을 찾는다. 공개 자료만으로 특정 조건을 만들 수 없으면 팀 작성 시나리오라고 명시하고 실측 평가와 분리한다.

| 사건 | 숨겨진 조건 | 기대 행동 |
| --- | --- | --- |
| 정상 | 공개된 당시 신호와 사건 기록이 함께 해석 가능 | 관련 도구를 호출하고 출처가 있는 점검 순서를 제시 |
| 상충 | 당시 신호와 로그가 서로 다른 설명을 시사 | 충돌을 명시하고 추가 확인을 요청; 단정 금지 |
| 근거 부족 | 필요한 기록이 없거나 품질이 낮음 | 없는 근거를 만들지 않고 결론 보류 |

각 사건에 작성자가 별도 `expected_behavior`를 두고, 이후의 확인된 장애 보고를 에이전트에게 숨긴 상태에서 모델을 실행한다. 가능하면 각 사건을 2~3회 반복하고 동일 질문에 대한 단순 검색+요약 기준선도 실행한다. 기록할 지표는 필요한 도구 호출, 근거 ID의 정확성, 모순 발견, 결론 보류, 안전 경계, 소요 시간이다. 시험 수가 적으므로 일반적인 현장 정확도나 통계적 우월성으로 해석하지 않는다.

NeMo Agent Toolkit을 연결하면 [공식 `nat eval` 기능](https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html)으로 중간 단계와 실행 설정을 저장한다. 시간이 허락하면 trajectory 평가와 프로파일러도 켠다. 모델 평가 점수만 의존하지 않고 사건별 규칙 검사를 함께 둔다. 핵심 사건은 공개 기록에서 선정하고, 팀이 만든 질문·주석은 원천 기록과 분리한다.

Planning date: 2026-09-28 KST. Deadline: **23:59 KST today**. Keep at least one hour of buffer for form upload, team-member applications, and link checks. The local clock was 10:49 KST when planning began; recheck time before scheduling work.

## Immediate prerequisites

- Confirm a **2–5 person team**, team name, and who will submit the representative portfolio. Every member must complete their own form. This is an eligibility gate, not a coding task.
- Confirm which GitHub account/organization and NVIDIA account the team will use. This repository starts private under `juyoungml`; publish only a reviewed clean-room deliverable if public access is needed for judges.
- Confirm whether a Linux/NVIDIA GPU host is already available. Do not make NemoClaw or local NIM setup the critical path without one.

## Experiments, in order

| ID | Trial | Evidence to save | Pass condition | Time box / fallback |
| --- | --- | --- | --- | --- |
| E0 | Check one joinable public episode from EDP within 45 minutes; if unavailable, inspect PreDist. | Exact file URLs, license, timestamp/asset joins, held-out outcome. | One asset has sensor, event, and outcome records that can be replayed without future leakage. | 45 min; use documented fallback and keep the asset description accurate. |
| E1 | Call two available Nemotron models with an attributed public snapshot and two function schemas. | Model IDs, request/response shape with secrets removed, latency, tool-call arguments. | At least one model reliably emits valid calls and a useful follow-up. | 60–90 min; choose the better model and stop comparison. |
| E2 | Implement read-only tools over a small, attributed slice of the selected public dataset. | Data provenance note, tool schemas, sample outputs. | Every returned claim has a record ID; no company file is present and the future outcome stays hidden. | 90 min; use local JSON/SQLite and deterministic matching. |
| E3 | Run a complete agent investigation with a conflicting record. | Full trajectory: plan, calls, outputs, final packet. | Model uses 2+ tools, notices the conflict, and asks for a physical check before concluding. | 2–3 h; simplify the interface before reducing the evidence behavior. |
| E4 | Test three cases: normal, conflicting, missing evidence. | Expected vs actual results, observed failures. | No invented source citation; missing evidence is acknowledged; no direct equipment control instruction. | 60 min; fix only failures that affect the core demo. |
| E5 | Try NeMo Agent Toolkit integration. | Runnable config, version, trace. | E3 still passes through the toolkit. | 90 min; retain a truthful custom loop if integration fails. |
| E6 | Try NemoClaw/OpenShell only on an available supported host. | Policy, denied action, audit trace, host/runtime details. | A real blocked action is visible and normal read-only calls still work. | 60–90 min after core demo; otherwise document the future deployment design honestly. |

The order is deliberate: a real tool-using agent and traceable public evidence are the entry. Toolkit and sandbox integration should strengthen the entry without jeopardizing the deadline.

The NVIDIA account's stated API limit is **40 requests/minute**. The POC paces its own hosted requests at 36/minute and retries HTTP 429 with `Retry-After` or short backoff. Run evaluations with one worker unless a shared account-level limiter is added; other applications using the same key are outside this process's control.

## Delivery milestones

| Local time target | Reviewable result | Decision |
| --- | --- | --- |
| By 13:00 | E1 model choice and confirmed team eligibility | If no valid tool call, change model or agent loop immediately. |
| By 16:00 | Public replay slice, tools, first end-to-end trajectory | Freeze the scenario and avoid new feature ideas. |
| By 19:00 | Usable demo, three evaluation cases, evidence trace | Decide if NAT/OpenShell additions are stable enough to include. |
| By 21:30 | README, run instructions, demo recording or screenshots, submission PDF draft | Freeze code and run a clean-room review. |
| By 22:30 | One final PDF below 100 MB, accessible link, exact form text | Start team-member submissions; keep 23:59 as hard stop. |

These are targets, not claims that work has been completed. Adjust after the first experiment using the current clock.

## Submission package

The user-provided Google Form requests a service name, **one file up to 100 MB** (or a Word/PDF containing the repository or deployment URL), a problem statement of about 300 Korean characters, a solution description of about 500 Korean characters, NVIDIA technology stack, and optional additional URL. Name the uploaded file `NVIDIA 해커톤_팀명_프로젝트명.pdf` using the actual team and project names.

The PDF should contain: one-sentence problem, one-sentence solution, a single public-data replay with source attribution, visible agent trajectory, NVIDIA components actually run, privacy boundary, reproduction steps, and links. Provide a live link only if it works for an unauthenticated judge; otherwise make the repository and recording self-contained. Never put credentials, employer/customer records, or private-only URLs in the PDF.

Before submitting, open the PDF and all links from a clean browser session, run the documented example, verify every claim against the saved trajectory, and check repository files plus Git history for sensitive material. Each team member then submits their individual application using the same agreed service identity.

## Scope guard

Do not add predictive maintenance, automatic plant control, broad document ingestion, model fine-tuning, or a multi-agent hierarchy to the preliminary demo unless the core gates above have passed and there is surplus time. The final's mission is unknown, so keep the domain tools reusable.
