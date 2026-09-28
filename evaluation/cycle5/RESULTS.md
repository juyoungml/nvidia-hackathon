# Cycle 5 results — 32 PreDist v2 incidents, single run per arm

Protocol: `PROTOCOL.md` (case list, selection rule and Amendments A/B written before the corresponding runs). Per-case data: `results.json`. Traces: `traces/`. Inputs and hashes: `cases/`, `case-manifest.json`. Figure: `figures/eval-cycle5.png`. Cycle 4 is unchanged and not pooled with this cycle.

## Cases

33 manufacturer-1 reports; 32 eligible (report 20 excluded: 14 samples in the 24 h window). All 32 were attempted and all 32 produced a saved trace for both arms. 21 are fresh (never used before), 11 were exposed in earlier cycles. Problem mix: no heat 11, not enough heat 8, no DHW 6, leakage 4, other 2, noise 1.

## Headline (reference/format check = unchanged v2 validator in each harness)

| Arm | Pass (all 32) | Pass (21 fresh) | Provider HTTP errors | Contract failures | Median wall s (non-provider runs) | Median tool calls (non-provider runs) |
|---|---|---|---|---|---|---|
| Ultra, first attempt | 15/32 (47%) | 11/21 (52%) | 13 (11×500, 2×429) | 4 | 45.2 (n=19) | 6 |
| Ultra, provider-error reruns (Amendments A/B) | 16/32 (50%) | 12/21 (57%) | 11 (still 429/500 after 3 attempts) | 5 | 43.5 (n=21) | 6 |
| Claude Code + Sonnet 5 | 32/32 (100%) | 21/21 (100%) | 0 | 0 | 48.2 (n=32) | 11 |

Among Ultra runs that actually reached the model without a provider error, 16/21 (76%) passed. Every Ultra run that got past the provider produced either a valid plan or a contract failure; there were no "never finished" runs — `bounded_finalize_v2` handed off at the planning cap in 6 cases (`investigation_budget_exhausted`), all 6 of which passed. Sonnet: no budget/timeout hits; total CLI-reported cost USD 7.86 (~0.25/case); resolved model `claude-sonnet-5` in every run.

## Failure modes

- Ultra provider errors (11 of 32 cases unresolved): NVIDIA HTTP 500 during the 6-worker first pass, then HTTP 429 on almost every request after 23:28 even at 1 worker with 34 rpm pacing — the account appears to have been rate-limited (possibly shared with other users of the key). These cases (3, 15, 23, 29, 37, 40, 44, 53, 60, 67, 69) say nothing about model quality; most failed at 0 tool calls.
- Ultra contract failure (5 cases: 5, 11, 47, 62, 64): the model called `query_measurement_window` with a range exceeding the 24-row limit; the harness treats an invalid tool argument as terminal (no repair, per protocol), so the plan is withheld. This is the one systematic Ultra failure mode seen at scale.
- Sonnet: none.

## Caveats

- One run per arm/case (plus disclosed provider-only reruns for Ultra); no variance estimate. Provider instability makes the Ultra first-attempt rate a lower bound on the harness+model, not a model-quality measurement.
- A reference/format pass means the plan is schema-valid and cites only retrieved fact IDs. It is not diagnosis accuracy, rationale entailment or engineering usefulness; outcomes were not graded.
- Tool-call counts are not comparable across arms: Sonnet counts Claude Code Read/Glob/Grep/StructuredOutput calls; Ultra counts its bounded public read tools.
- Model and harness differ between arms; no causal attribution to either.
- 11 of 32 cases were exposed in earlier cycles; fresh-only numbers are shown separately.
- Cases now include non-heating complaints (DHW, leakage, noise, other); the tool surface is still the heating-circuit-oriented bundle.


## Update after Amendment D (2026-09-29 00:0x KST)

The 11 Ultra cases that had never reached the model were rerun with 1 worker, 12 requests/min and transport-level retry on HTTP 429/500/502/503 (Amendment D). All 11 produced a model result: 10 passed, 1 (case 40) failed with the same `window contains more than 24 rows` tool error.

| | Pass | NVIDIA API errors | Real failures | Fresh 21 |
|---|---:|---:|---:|---:|
| Ultra, first attempt | 15/32 | 13 | 4 | 11/21 |
| Ultra, after API-error reruns (A–D) | **26/32 (81%)** | 0 | 6 (all >24-row window requests: 5, 11, 40, 47, 62, 64) | 18/21 |
| Claude Code + Sonnet 5 | 32/32 | 0 | 0 | 21/21 |

All 26 plans Ultra completed passed the reference check (no fabricated citations). Ultra wall times after reruns include API back-off waits and are not comparable to Sonnet's. `results.json` and `figures/eval-cycle5.png` are regenerated from all traces.
