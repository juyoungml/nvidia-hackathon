# Current result checkpoint — 2026-09-28

The current evidence is [evaluation/results/README.md](../../evaluation/results/README.md) and its preserved trace set: three actual PreDist complaints on the same substation and two separately labeled derived probes. Local Nano schema-v2 triage and hosted Ultra run end to end. The three real complaints all escalated, just as the keyword rule did. The no-report probe produced an invented service-loss rationale, so Nano's incremental value is not established. Citation coverage is incomplete: case 52 omits the measurement source and case 32 omits the current complaint source. No undefined tags in the four investigation answers does not imply full grounding.

NAT 1.8.0 executed a separate deterministic replay of three registered public tools. [OpenShell 0.1.2](../../integrations/openshell-README.md) enforced allowed reading and denied file read/write/direct TCP in an isolated public-fixture test. Neither result means the full model pipeline runs under NAT or OpenShell. The original one-case notes below are preserved as history; latest results supersede their completion status.

# POC result — public energy-equipment incident replay

## 검토용 요약

공개된 지역난방 설비 사건을 신고 당시로 되돌려 실행했다. NVIDIA Nemotron 3 Ultra가 계측·과거 장애·정비 타임라인 도구를 3회 호출했다. 최근 24시간 144개 계측에서 2차측 난방 공급온도는 설정값을 따라갔지만, 고객 실내에 열이 도달했는지 보여주는 값은 없었다. 모델은 고객 측 온도·유량을 다음 확인 항목으로 제시했다.

같은 공개 보고서의 사후 원인·조치 문장은 모델에 주지 않았다. 따라서 이번 결과는 **근거를 수집해 다음 확인을 제안한 POC**이며 원인 진단 정확도나 시간 절감 성과가 아니다. 초기 실행에서는 모델이 신호의 1차측·2차측을 혼동해 도구 출력을 수정했다. 현재 결과에도 공개 자료에 없는 `s_hc1_flow`, `s_hc1_valve_position`이라는 태그 표현이 남아 있다. 실행 코드는 이제 이런 이름을 별도 경고로 표시하며, 기존 저장소의 실행 기록은 재실행 시 덮어쓰지 않는다.

2026-09-28 KST. This is a feasibility result for team review, not a claim of field accuracy.

## The story in one sentence

**에너지 설비의 알람을, 근거 있는 다음 점검으로.**

At the report time, a customer says there is no heat, but the published sensor at the substation shows the secondary heating supply temperature tracking its setpoint. An agent should recognize that the sensor does not measure heat delivery to the customer's rooms, inspect the earlier intervention, and propose the next evidence to collect.

## Public case and data boundary

- Dataset: [PreDist v2](https://zenodo.org/records/19496480), CC BY 4.0, manufacturer 1, district-heating substation 21.
- Decision time: 2016-12-12 15:55; reported problem category: `no heat`.
- Agent-visible: 144 measurements in the preceding 24 hours, prior incident report dated 2016-12-06, and earlier disturbance timestamps.
- Held out: the current incident's retrospective diagnosis and remedy in [held-out-52.json](../../evaluation/held-out-52.json). The agent code reads only [replay-52.json](../../data/replay-52.json).
- No employer/customer data or source repository was used. This is a district-heating substation, not an electric power station.

## What ran

The [POC runner](../../poc/run.py) called `nvidia/nemotron-3-ultra-550b-a55b` through NVIDIA's hosted NIM API. The model called three read-only tools: `get_recent_measurements`, `get_prior_incidents`, and `get_maintenance_timeline`. Its [saved trace](../../poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json) records the model/tool sequence and cited source IDs. The three model requests took 12.8 seconds in this single run; this is an observation, not a latency benchmark.

The output correctly identified the key evidence gap: the measured secondary heating supply follows its setpoint (mean absolute gap 0.31 °C; 144/144 samples within 2 °C), but there is no room/radiator temperature or secondary circuit flow to prove that heat reached the customer. It cited the earlier report that the heating curve was raised on 2016-12-06 and suggested checking customer-side conditions. It did not consistently prioritize the controller settings that the later report identified.

The later report records an incorrect controller parameter setting and a reset. That outcome was **not** available to the agent at decision time. The POC therefore supports a narrower claim: the agent requested a relevant next record, not that it diagnosed the root cause correctly or improved a benchmark score.

## Failures observed

- Initial Nemotron 3.5 Lightning hosted tool-call request returned an agent service error; Nemotron 3 Super returned HTTP 500. Plain text authentication with Lightning succeeded. This may be endpoint/runtime-specific, and it is not evidence that the models lack tool-call capability.
- Local Nemotron 3 Nano 4B called tools but produced an invalid comparison between outdoor and supply temperatures. That [trace](../../poc/trace-52-ollama-nemotron-3-nano-4b.json) is retained as a failure case.
- The first Ultra draft confused primary and secondary signal names and speculated about component faults. We changed tool outputs to include explicit side labels and prohibited unsupported component claims. The current trace is better, but it still suggests `s_hc1_flow` and `s_hc1_valve_position` tags that are not in the published feature list. These must be phrased as **measurements to obtain**, not existing signals. The runner now flags undefined signal names.

These failures are why the product needs source-aware tool schemas and an output check before any external claim. One successful case does not establish reliability.

## Review decision

The POC supports continuing with **evidence-to-next-check** as the product story. Next, run at least two additional public cases and a simple search-and-summary baseline, score citation correctness and unsupported claims, then decide whether NeMo Agent Toolkit evaluation adds value. Security remains a deployment design until OpenShell isolation is actually exercised.

To rerun the model with the public replay: place `NVIDIA_API_KEY` in a local `.env` (excluded from Git), then run `NVIDIA_MODEL='nvidia/nemotron-3-ultra-550b-a55b' python3 poc/run.py`.
