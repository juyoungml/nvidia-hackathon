# NeMo Agent Toolkit public replay integration

`nat_replay.py` registers the four existing read-only `poc.run.run_tool` readers as the `public_predist_tools` function group. `public_predist_replay_workflow` invokes the three tools used by the saved Ultra investigation in a fixed order. This is a **deterministic NAT tool execution**, not a NAT model agent run or a new Nemotron inference. The saved [Ultra trace](../poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json) remains the evidence of model-selected tool calls. The NAT replay checks that the same public evidence readers can be registered and executed by the toolkit.

From the repository root:

```sh
uv venv --python 3.12 .artifacts/nat-venv
uv pip install --python .artifacts/nat-venv/bin/python -r integrations/requirements.lock
.artifacts/nat-venv/bin/python integrations/run_nat_replay.py
```

This keeps toolkit dependencies out of the project environment and requires no API key. `requirements.lock` pins the resolved Python dependencies. NVIDIA's 1.8.0 core package discovers a built-in `nat_tools` plugin that imports `langchain_core`; the explicit second dependency in `requirements.in` prevents an import warning on this host. The command prints the toolkit version, tool names, source IDs, and a SHA-256 digest of the complete tool results. It also writes the same small, public-data-only trace to `integrations/trace.json`. The pinned case ID rejects other input. The four registered tool names are `public_replay__get_recent_measurements`, `public_replay__get_prior_incidents`, `public_replay__get_maintenance_timeline`, and `public_replay__get_signal_definitions`; the workflow calls the first three. Registration is in `nat_replay.py`; workflow config is in `nat_replay.yml`.

Verified on macOS arm64 with Python 3.12.11 and `nvidia-nat` 1.8.0: all three calls completed; `uv pip check` passed. The output digest for the current replay data was `6d27290042d0f83afd1d2cfbad40245d200568b8c030269b4962016bb164e1bc`. The digest changes if public replay data changes. No inference endpoint was called.

OpenShell was assessed only for local feasibility. This host is macOS arm64 with Docker 29.7.2 running, which [NVIDIA's support matrix](https://docs.nvidia.com/openshell/latest/reference/support-matrix.html) lists as a supported Docker Desktop setup. The `openshell` and `nemoclaw` commands are absent. No gateway, sandbox, policy, or denied-egress test was run, so there is no OpenShell enforcement evidence yet. An actual policy test would require a separately configured local gateway and sandbox, inspection of the effective policy, and both allowed and denied network probes. Do not describe this integration as OpenShell protected.

References: [NAT custom function groups](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/custom-components/custom-functions/function-groups.html), [custom functions](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/custom-components/custom-functions/functions.html), and [workflow execution](https://docs.nvidia.com/nemo/agent-toolkit/latest/run-workflows/about-running-workflows.html).
