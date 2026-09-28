# NVIDIA 연동

System 2 (원인 조사, 구현)에 붙인 NVIDIA 도구의 연동 코드와 실행 기록입니다. 전체 구조는 [docs/architecture.md](../docs/architecture.md)를 보세요.

| 연동 | 상태 | 문서·기록 |
|---|---|---|
| NeMo Agent Toolkit 1.8.0: 읽기 도구 6종 실행 (`--read-backend nat`) | 구현 (선택 경로). 모델 루프는 `poc/live_investigation.py`가 담당 | [NAT_LIVE.md](NAT_LIVE.md), [동등성 기록](nat-live-smoke.json), [사례 52 실행](nat-live-case52.json) |
| NeMo Agent Toolkit: 초기 도구 4종 고정 순서 replay | 이전 시험 (모델 호출 없음) | 아래 설명, [trace.json](trace.json) |
| OpenShell 0.1.2: 읽기만 허용, 쓰기·외부 연결 차단 | 공개 fixture로 별도 시험, 조사 루프에는 미적용 | [openshell-README.md](openshell-README.md), [trace](openshell-trace.json) |
| Nemotron 3 Ultra 구조화 출력 확인 | 단순 스키마 제약 수용 확인 | 아래 설명, [probe 기록](structured-output-probe.json) |

NAT 의존성은 프로젝트 환경과 분리된 `.artifacts/nat-venv`에 [requirements.lock](requirements.lock)으로 설치합니다.

## NeMo Agent Toolkit public replay integration (초기 4종, 영문)

`nat_replay.py` registers the four existing read-only `poc.run.run_tool` readers as the `public_predist_tools` function group. `public_predist_replay_workflow` invokes the three tools used by the saved Ultra investigation in a fixed order. This is a **deterministic NAT tool execution**, not a NAT model agent run or a new Nemotron inference. The saved [Ultra trace](../poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json) remains the evidence of model-selected tool calls. The NAT replay checks that the same public evidence readers can be registered and executed by the toolkit.

From the repository root:

```sh
uv venv --python 3.12 .artifacts/nat-venv
uv pip install --python .artifacts/nat-venv/bin/python -r integrations/requirements.lock
.artifacts/nat-venv/bin/python integrations/run_nat_replay.py
```

This keeps toolkit dependencies out of the project environment and requires no API key. `requirements.lock` pins the resolved Python dependencies. NVIDIA's 1.8.0 core package discovers a built-in `nat_tools` plugin that imports `langchain_core`; the explicit second dependency in `requirements.in` prevents an import warning on this host. The command prints the toolkit version, tool names, source IDs, and a SHA-256 digest of the complete tool results. It also writes the same small, public-data-only trace to `integrations/trace.json`. The pinned case ID rejects other input. The four registered tool names are `public_replay__get_recent_measurements`, `public_replay__get_prior_incidents`, `public_replay__get_maintenance_timeline`, and `public_replay__get_signal_definitions`; the workflow calls the first three. Registration is in `nat_replay.py`; workflow config is in `nat_replay.yml`.

Verified on macOS arm64 with Python 3.12.11 and `nvidia-nat` 1.8.0: all three calls completed; `uv pip check` passed. The output digest for the current replay data was `6d27290042d0f83afd1d2cfbad40245d200568b8c030269b4962016bb164e1bc`. The digest changes if public replay data changes. No inference endpoint was called.

The separate [OpenShell local probe](openshell-README.md) exercised a temporary sandbox with public fixtures. Its [trace](openshell-trace.json) records an allowed read and denied read, write, and direct TCP connection. That sandbox was not attached to the investigation or model endpoint, so it is not evidence that the live workflow runs under OpenShell.

The [live NAT path](NAT_LIVE.md) registers all six current public readers. Each model-selected read can execute through NAT, with the same result and fact construction as the direct path. [The local smoke record](nat-live-smoke.json) checks all six readers without a model call. The older fixed three-reader workflow above remains a separate replay.

References: [NAT custom function groups](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/custom-components/custom-functions/function-groups.html), [custom functions](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/custom-components/custom-functions/functions.html), and [workflow execution](https://docs.nvidia.com/nemo/agent-toolkit/latest/run-workflows/about-running-workflows.html).

## Hosted Ultra structured-output feasibility

The isolated [probe](structured_output_probe.py) sends at most two requests to hosted Nemotron 3 Ultra with a synthetic one-item array schema. The prompt explicitly asks for two disallowed `BETA` items; the schema permits exactly one `ALPHA`. Run it once with `uv run python integrations/structured_output_probe.py --execute`. It reads the existing `.env` key without writing it to the trace and saves the exact request parameters, HTTP results, raw content, latency, and local schema verdict in [the probe record](structured-output-probe.json). No replay cases or tool calls are involved.

On 2026-09-28, both `response_format: {"type":"json_schema", ...}` and `guided_json` returned HTTP 200 from `nvidia/nemotron-3-ultra-550b-a55b`, each with `{"items":["ALPHA"]}`. The observed outputs satisfy the one-item and enum constraints despite the conflicting prompt. This is positive feasibility evidence for simple hosted schema constraints, not proof that every JSON Schema feature, the full v2 task schema, or simultaneous tool calling works. The hosted server did not expose its NIM version in these responses. Keep the current repair policy and common validator until those combinations are verified in a separately frozen protocol.

NVIDIA's [Ultra guide](https://docs.nvidia.com/nim/large-language-models/2.0.6/day-0/get-started-nemotron-3-ultra.html) explicitly documents JSON mode for this model; that mode alone does not impose the task's schema. NVIDIA's [structured-generation guide](https://docs.nvidia.com/nim/large-language-models/1.14.0/structured-generation.html) describes schema-guided decoding via `guided_json`. The hosted probe above establishes acceptance and observed conformance for both tested request shapes on the actual endpoint.
