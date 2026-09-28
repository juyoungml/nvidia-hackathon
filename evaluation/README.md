# Public replay comparison

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
