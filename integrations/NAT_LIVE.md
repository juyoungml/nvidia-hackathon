# NAT-backed live investigation

`poc.live_investigation` offers two read backends: `direct` and `nat`. With `nat`, each model-selected read is routed through the registered `public_predist_live_tools` function group and `public_predist_live_read` workflow in NAT 1.8.0. The six readers include the four source tools, temporal episodes, and a bounded measurement-window query. The hosted Nemotron request still uses the existing NVIDIA chat API client; NAT executes selected local tools, not the model loop.

From the repository root, install the pinned optional environment and run the keyless equivalence smoke:

```sh
uv venv --python 3.12 .artifacts/nat-venv
uv pip install --python .artifacts/nat-venv/bin/python -r integrations/requirements.lock
.artifacts/nat-venv/bin/python integrations/run_nat_live_smoke.py
.artifacts/nat-venv/bin/python -m unittest tests.test_nat_live -q
```

[The smoke record](nat-live-smoke.json) contains the NAT version, public input hash, all six reader names, direct/NAT equality verdicts, fact counts, and result hashes. It contains no key and makes no model call. The source path, decision cutoff, prior-record times, query bounds, and 24-row query cap are validated before evidence reaches the model. An invalid tool request withholds the plan.

For one fresh live run, place an NVIDIA API key in the repository-root `.env` as `NVIDIA_API_KEY=...`, then invoke:

```sh
.artifacts/nat-venv/bin/python -m poc.live_investigation \
  --case replay-52.json \
  --output .artifacts/live-case52-nat.json \
  --read-backend nat \
  --handoff-policy bounded_finalize_v2
```

The command refuses an existing output and any path inside frozen `evaluation/cycle4`. `--handoff-policy` is required: `explicit_finish_v1` requests a final plan only after the finish tool; `bounded_finalize_v2` also permits a handoff after six valid read turns have exhausted the six-request cap and at least one non-report fact was retrieved. Other stops and provider errors withhold the display. The output retains model requests, responses, selected tool calls, NAT version, source-read state, validation, and human-review flags. Use `--read-backend direct` to compare the same public reader implementation without NAT. The displayed plan is a reviewable suggestion, and review flags for times or quantities outside cited facts are heuristics, not semantic proof.

The public [case-52 integration trace](nat-live-case52.json) is a development smoke, separate from frozen cycle 4. Its one hosted run made six planning requests; Nemotron selected all six readers, each executed through NAT 1.8.0. The six valid read turns exhausted the planning budget, so `bounded_finalize_v2` requested one native-schema final plan. The selected plan passed structural/reference checks and has no current heuristic time or quantity review flags. The trace records `planning_cap_handoff` and explicitly notes that the investigator did not call the finish tool or attest sufficiency. This is not a new benchmark result, a comparison win, or expert validation of the plan's meaning.
