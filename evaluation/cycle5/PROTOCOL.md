# Cycle 5 — breadth check over all eligible PreDist v2 manufacturer-1 reports

Frozen before any cycle-5 inference, 2026-09-28 23:20 KST. Cycle 4 files and numbers are untouched; cycle 5 is a separate, larger, single-run breadth check.

## Case list and selection rule (fixed before running)

Rule: every manufacturer-1 fault report in PreDist v2 `faults.csv` (33 reports, all problem categories — not only heating complaints), in report-ID order, whose substation operational CSV was extracted from the public Zenodo archive (CC BY 4.0, DOI 10.5281/zenodo.19496480), with >=100 samples in the 24 h before the report date and nonempty `s_hc1_supply_temperature`, its setpoint and `p_hc1_return_temperature`.

Result (`case-manifest.json`, with input SHA-256): 32 eligible cases — reports 1, 3, 5, 6, 7, 10, 11, 13, 15, 23, 24, 29, 32, 34, 36, 37, 38, 40, 44, 45, 47, 49, 52, 53, 57, 60, 62, 63, 64, 65, 67, 69. Report 20 is ineligible (14 samples in window). No case was dropped after seeing outputs.

Inputs are built by `run_cycle5.py prepare` with the same window, cutoff and withholding logic as `scripts/build_holdout_cases.py` (verified identical rows/prior records to `data/replay-52.json` and `data/holdout-29.json`). Later diagnosis, remedy and fault label are not in any input.

Exposure: reports 3, 5, 13, 29, 32, 37, 47, 52, 60, 62, 63 were used in earlier cycles/development; the other 21 are fresh for both arms. Results are reported for all and for the fresh subset.

## Arms (same output contract as cycle 4)

- Ultra: `nvidia/nemotron-3-ultra-550b-a55b`, `poc.live_investigation.run_live_case`, temporal tools on, up to 6 planning requests, handoff policy `bounded_finalize_v2` (current policy), then one native-schema final plan request. Shared thread-safe pacer at 34 rpm (account limit 40 rpm).
- Sonnet: Claude Code + `claude-sonnet-5` via unchanged `evaluation.live_claude.run_live_claude` (restricted Read/Glob/Grep + StructuredOutput, USD 0.50 guard, 300 s timeout).

Both arms receive the identical bundle from `build_live_bundle(replay, temporal_enabled=True)`. One run per arm/case, no retries, no best-of selection, no configuration changes after the first inference. Crashes are stored as run failures.

## Measured

Per case and arm: completed with a valid output (native plan parsed); reference/format check pass = the unchanged v2 validator inside each harness returns `validation.status == "valid"` (same checker as cycle 4, not loosened); tool-call count; wall time; budget-exhausted flag (Ultra `investigation_budget_exhausted`; Sonnet budget/timeout subtype).

Not measured: diagnosis accuracy, rationale entailment, plant/economic effect. A reference/format pass is not a correct diagnosis.

## Time box

Runs were launched before 23:38 KST; any case without a finished trace at the reporting cutoff is reported as not completed, not dropped.

## Amendment A (23:23 KST, before any rerun outcome was seen)

The first Ultra pass at 6 concurrent workers hit NVIDIA HTTP 500/429 on many cases (provider failures, not semantic errors). At 23:23 the Ultra runner was restarted at 3 workers; in-flight cases without a saved trace were restarted from scratch (no output had been seen). Saved first-attempt traces are kept as the primary result. Cases whose first Ultra attempt ended in a provider HTTP error get exactly one rerun (`ultra-rerun-<id>.json`) at low concurrency if time permits; results are reported both as first-attempt and with provider-error reruns, labelled separately. No rerun is made for semantic/contract failures. Sonnet is unchanged.

## Amendment B (23:30 KST)

The Amendment-A rerun (2 workers, started 23:28:45) itself hit HTTP 429 within seconds on 11 of 13 cases (0–5 tool calls), i.e. the account was rate-limited, not the model failing. Those 11 cases whose rerun again ended in a provider HTTP error get one further attempt (`ultra-rerun2-<id>.json`) at 1 worker, launched before 23:38. The "Ultra with provider reruns" view uses the last attempt for a case only when every earlier attempt was a provider HTTP error; a contract/reference failure on any attempt is final. First-attempt numbers are always reported alongside.

## Amendment C (2026-09-28 23:41 KST, written before the run)

The 11 Ultra cases that never reached the model because of NVIDIA API errors (3, 15, 23, 29, 37, 40, 44, 53, 60, 67, 69) are run once more at a lower rate (2 workers, shared pacer at 20 requests/min, half the 40 rpm account limit), tagged `-rerun3`. A probe request at 23:41 returned HTTP 200. Only provider-error cases are rerun; model or contract failures are never rerun. First-attempt numbers stay reported alongside.

## Amendment D (23:43 KST, written before the run)

The Amendment C attempt was stopped after 6 cases: every request returned HTTP 429, and a single standalone probe request also returned 429, so the hosted endpoint was throttling independent of our rate. Those aborted attempts (all HTTP 429, no model output) are discarded. The same 11 cases are rerun with 1 worker at 12 requests/min and a transport-level retry on HTTP 429/500/502/503 (up to 4 retries, honoring Retry-After or backing off 10 s, 20 s, …) via `NVIDIA_HTTP_RETRIES=4`, tagged `-rerun3`. Retries only repeat the identical request; they never change prompts, tools or validation. Model and contract failures are still never rerun.

## Amendment E — tool fix run (2026-09-29, written before the run)

All 6 remaining Ultra failures were the same tool-argument error: `query_measurement_window` rejected windows longer than 24 rows. The tool now clips such a request to the latest 24 rows (nearest the decision time) and reports the clip (`clipped.requested_start`, `matched_rows`, `returned_rows`); the tool description tells the model this. This changes the tool contract for every case, so it is evaluated as a separate arm, not merged into earlier numbers: all 32 cases are run once more for Ultra with the fixed tool, tagged `-clip` (1 worker, 12 requests/min, `NVIDIA_HTTP_RETRIES=4`). The validator and prompts are otherwise unchanged. Sonnet is not rerun (it never hit the limit). Reported alongside, never replacing, the first-attempt and rerun numbers.

## Amendment F (2026-09-29, written before the run)

In the tool-fix run, cases 13 and 15 ended with an NVIDIA API read timeout (90 s) before any model output. As with HTTP errors, API timeouts count as provider errors and are rerun once with the same settings, tagged `-clip-rerun`. Model or contract failures are never rerun.
