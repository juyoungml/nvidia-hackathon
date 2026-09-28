# Strategy — Plant Reliability Agent

## 핵심 결정

가상의 발전소 설비 이상을 입력받아 Nemotron이 읽기 전용 도구를 직접 선택·호출하고, 상충하는 증거를 확인한 뒤 출처가 연결된 점검 계획을 내놓는다. 심사에는 합성 자료만 제출한다. 실제 고객 적용은 사내 Nemotron/NIM과 로컬 검색으로 데이터 경계를 유지하는 확장 방향으로 설명한다.

이 전략은 [해커톤 소개](https://fastcampus.co.kr/NVIDIA_hackathon)의 “계획·도구 호출·산업 문제 해결” 요구와 [AI Day Seoul](https://www.nvidia.com/ko-kr/ai-days/)의 에이전틱 AI, 피지컬 AI, 안전한 배포 주제에 맞춘 가설이다. 실제 구현·평가로 확인한 것만 제출 문안에 쓴다.

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
