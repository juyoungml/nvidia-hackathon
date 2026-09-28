# Strategy — Plant Reliability Agent

## 핵심 결정

가상의 발전소 설비 이상을 입력받아 Nemotron이 읽기 전용 도구를 직접 선택·호출하고, 상충하는 증거를 확인한 뒤 출처가 연결된 점검 계획을 내놓는다. 심사에는 합성 자료만 제출한다. 실제 고객 적용은 사내 Nemotron/NIM과 로컬 검색으로 데이터 경계를 유지하는 확장 방향으로 설명한다.

이 전략은 [해커톤 소개](https://fastcampus.co.kr/NVIDIA_hackathon)의 “계획·도구 호출·산업 문제 해결” 요구와 [AI Day Seoul](https://www.nvidia.com/ko-kr/ai-days/)의 에이전틱 AI, 피지컬 AI, 안전한 배포 주제에 맞춘 가설이다. 실제 구현·평가로 확인한 것만 제출 문안에 쓴다.

## 예선 Top 10을 위한 심사 메시지

**한 문장:** "설비 이상이 발생했을 때, Nemotron 에이전트가 여러 기록을 직접 조사하고 증거 충돌을 찾아, 엔지니어가 검토할 수 있는 근거·점검 순서·보류 사유를 만든다. 회사 자료 없이 재현 가능한 합성 사건으로 검증했다."

합성 데이터는 제품의 핵심 가치가 아니다. 공개 데모가 실제 고객 데이터를 노출하지 않도록 하면서, 올바른 도구 선택·근거 인용·모순 발견·결론 보류를 객관적으로 시험하는 장치다. 무작위로 생성한 문서 수보다 **설비 상태 → 기록 → 원인 후보 → 확인 행동**의 인과관계와 사건별 정답표가 중요하다. 실데이터를 변형한 합성 자료나 실측 성과처럼 보이는 수치는 금지한다.

**왜 Nemotron인가:** Nemotron이 가상 증상에서 도구를 선택하고, 결과를 비교하며, 다음 조회와 최종 답변을 결정한다. 이 능력은 모델 이름을 적는 것으로 입증되지 않는다. 동일 입력의 도구 호출 trace, 모델 ID, 실패 사례를 제출한다. NeMo Agent Toolkit은 도메인 도구의 등록·실행 흐름과 평가·프로파일링을 재현 가능하게 만들 때 가치가 있다. [공식 평가 문서](https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html)는 중간 단계, trajectory 평가, 지연·토큰·도구 span을 기록한다. 실제 통합 전에는 "NAT 기반"이라고 주장하지 않는다.

**심사에 제시할 증거:** 90초 이내의 전체 데모, 정상·상충·근거 부족 사건의 trace, 사건별 기대 행동과 실제 행동, 출처 없는 주장 수, 필요한 도구 호출 성공률, 결론 보류 성공 여부, 민감정보·쓰기 권한 차단 결과(실행한 경우), 재현 명령과 모델/설정 버전. 작은 평가라도 동일 조건의 단순 검색+요약 기준선과 비교하면 agent의 추가 가치가 드러난다.

**차별점:** 산업 도메인에서 답변의 유창함보다 조사 경로와 안전한 보류를 평가한다. 제품은 설비 제어를 자동화하지 않고 엔지니어의 판단 준비 시간을 줄인다. 실제 절감 시간·금액은 별도 현장 검증 전까지 주장하지 않는다.

Last reviewed: 2026-09-28 (KST). This is a working hypothesis for the **online preliminary challenge**. The one-day final's mission will be announced on site, so this project must remain adaptable.

## Decision in one sentence

Build a working industrial investigation agent that takes a fictional plant incident, chooses and calls read-only tools, checks conflicting evidence, and produces a cited inspection plan. Show how the same architecture can run on site with NVIDIA models and policy controls, without submitting company or customer data.

Working product name: **Plant Reliability Agent**. Name, team, and demo scenario can change without changing the core workflow.

## Why this fits the event

- The [hackathon page](https://fastcampus.co.kr/NVIDIA_hackathon) asks for an agent that plans, calls tools, and solves a real industrial problem, using NVIDIA's agent stack. The published judging criteria are NVIDIA agent technology depth, practical and industrial value, completeness, and originality.
- [AI Day Seoul](https://www.nvidia.com/ko-kr/ai-days/) is organized around agentic AI and Claws, physical AI and robotics, and AI infrastructure. Its program includes Build-a-Claw with NemoClaw and DGX Spark, plus a workshop on safe LLM agents. The [session catalog](https://www.nvidia.com/ko-kr/ai-days/session-catalog/) currently says more sessions will be added; do not infer a specific judging theme from an unpublished agenda.
- NVIDIA's [Agent Toolkit announcement](https://nvidianews.nvidia.com/news/enterprise-software-leaders-build-ai-agents-with-nvidia) connects Nemotron models, agent harnesses and skills, OpenShell policy, and local-to-enterprise computing. Its factory-operations example is a useful comparison, not a claim that this project is affiliated with it.

**Inference:** A convincing entry will show the *work* the agent performs: its plan, tool calls, evidence trail, handling of uncertainty, and controlled handoff to an engineer. A generic chat response or a diagram of unimplemented components will not demonstrate this.

## User and problem

The target user is a plant maintenance or operations engineer responding to an equipment anomaly. Incident records, prior work, permits, and technical references live in separate systems. Finding the relevant evidence and deciding the next safe inspection can take substantial time. The agent assembles a traceable investigation packet; it does not assert an unverified root cause or operate plant equipment.

The first demo should be one fictional rotating-equipment incident with at least two plausible causes and one conflicting record. This makes the agent's choices and uncertainty visible in a short presentation.

## Demo contract

Input: a fictional equipment symptom and operating context.

Output:

1. A short investigation plan and visible sequence of tool calls.
2. Candidate explanations linked to individual fictional source records.
3. Contradictions, missing evidence, and confidence limits.
4. A ranked, read-only inspection checklist and an explicit human review point.
5. An optional impact estimate computed by a deterministic tool from **fictional assumptions**, labeled as a scenario rather than measured savings.

The minimum tools are `find_incidents`, `get_maintenance_history`, `search_technical_references`, and `calculate_impact`. The model must actually choose at least two tools and use their returned evidence. At least one test must make it withhold a conclusion because evidence is insufficient.

## NVIDIA technology choices

| Layer | First attempt | What it must demonstrate | Fallback / decision |
| --- | --- | --- | --- |
| Reasoning | A currently available [Nemotron model on build.nvidia.com](https://build.nvidia.com/models) via NVIDIA NIM API | Structured tool calls and useful synthesis on fictional data | Try a second Nemotron model if the first fails the tool-call gate; record model ID and result. |
| Agent workflow | [NeMo Agent Toolkit tool-calling agent](https://docs.nvidia.com/nemo/agent-toolkit/1.8/components/agents/tool-calling-agent/tool-calling-agent.html) | Registered domain tools, bounded iterations, and reproducible trace | A small explicit tool loop is acceptable for the preliminary demo if integration time threatens submission; describe the actual implementation accurately. |
| Retrieval | Local indexed fictional records, optionally [NeMo Retriever](https://docs.nvidia.com/nemo/retriever/latest/reference/retriever-cli-quickstart/) | Source IDs and excerpts used in final claims | Start with deterministic local search; add Retriever only if it improves the demonstrated decision. |
| Security | [NemoClaw/OpenShell](https://docs.nvidia.com/nemoclaw/latest/security/best-practices.html) where a suitable Linux host is available | Enforced file/network boundaries and a denied action in the trace | If runtime setup is not feasible today, include a truthful policy design and make the demo's tools read-only; never claim OpenShell was executed unless verified. |
| Deployment story | Hosted NIM for fictional preliminary data; self-hosted NIM for future customer deployment | A clear migration path without customer content leaving site | A DGX Spark or on-prem deployment is a future architecture until run and verified. |

The [NVIDIA Skills catalog](https://build.nvidia.com/skills) contains installable agent guidance. It is distinct from a model inference API. The application must use a real NVIDIA model/API and domain tools; listing Skills alone does not prove a functioning agent.

## Information boundary

**Public repository, submission, and hosted NVIDIA API:** original application code, fictional incident/work-order/reference records, fictional identifiers, public facts with citations, and results measured only on the fictional demo. Label every sample and performance claim by provenance.

**Company-controlled environment only:** employer/customer records, source documents, equipment tags, file paths, screenshots, repository history, internal metrics, credentials, and any derivative that could reveal an actual incident or site. Do not copy an existing company repository into this one. Redacting a real record is not sufficient without a separate release review; write fictional cases from scratch.

NVIDIA's [API Catalog trial terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf) prohibit confidential, controlled, or sensitive input. The [hosted NIM deployment guide](https://docs.nvidia.com/nemo/retriever/26.5.0/extraction/deployment-options/) says to self-host when customer data cannot leave the network. The preliminary endpoint may receive **fictional data only**. Before any public push or submission, inspect both tracked files and Git history for identifiers, secrets, and copied source material.

## What we will claim

- **Can claim after verification:** tool calls made by Nemotron, observed outputs, source-linked response, exact model and toolkit versions, synthetic evaluation results, and any OpenShell policy enforcement actually run.
- **Cannot claim from this demo alone:** a customer deployment, proven root-cause accuracy in a real plant, production-grade safety, measured financial recovery, private-data protection by prompt instructions alone, or DGX Spark execution.

## Selection gates

1. **Product gate:** can the fictional incident produce a useful, inspectable action plan in under three minutes of presentation?
2. **Agent gate:** did Nemotron select multiple tools based on the task, and did different evidence cause a different decision?
3. **Safety gate:** are actions read-only, source boundaries explicit, and unsupported conclusions withheld?
4. **Submission gate:** can a reviewer open the demo/repository from the uploaded PDF and reproduce the example without private access?

If a component does not help pass one of these gates today, defer it.

## Source and event notes

The user-provided application form says the online challenge closes **2026-09-28 23:59 KST**; ten teams advance to the 2026-10-07 final, where the mission is revealed. Five finalists pitch at AI Day Seoul in November. This repository's plan targets the online preliminary submission only.
