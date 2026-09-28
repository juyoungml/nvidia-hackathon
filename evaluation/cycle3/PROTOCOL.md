# Cycle 3 — trajectory-driven output recovery

Frozen before inference, 2026-09-28. Goal: test whether one explicit validation-feedback correction recovers usable outputs without weakening the existing v2 evidence contract. This does not promise superiority over Sonnet or change earlier results.

## Development and test split

Manifest: `evaluation/cycle3/manifest.json`.

- Exposed development/regression: cases 52, 60, 63, 3, 13.
- Fresh test: first chronologically eligible reports on two remaining assets, report37/asset19 and report5/asset11. Input hashes and eligibility audit are fixed before any model run. Current diagnoses remain excluded.
- All are PreDist heating complaints, still a narrow domain. New assets do not establish general power-plant diagnosis accuracy.

## Matched arms

D: Nemotron Ultra with the current public-reader tools. G: Claude Code + exact Sonnet5 in the established restricted file-reader configuration. Same task, catalog, allowed corpus and contract v2; confirm per-case corpus hashes before comparison.

Both arms opt into `validate_repair_once` policy v1. An invalid initial response receives **one** extra no-tool model request with the unchanged task/schema, original output, precise validation feedback and evidence already read. No new facts, hidden labels, manual citation attachment, deterministic truncation of the answer, validator relaxation, or further retry. If correction fails, withhold the response. An initially valid response is not corrected just because its content looks weak.

Claude correction gets no file tools and no mounted case files. Only successfully read original sources enter its correction packet; a successfully read full fact catalog permits its contents. Domain correction uses its already-read tool evidence. Keep the initial source-read state. Provider failures are recorded separately; no replacement model. Case37/5 answers must not be inspected to alter prompts or select cases.

## Execution

One D run followed by one G run per case, in manifest order. No configuration edits after the first inference. Keep initial raw outputs, validation attempts, corrected outputs, feedback prompt, repair count, model request/wall timing and available usage separately. The runner checks frozen protocol SHA-256 and input hashes; output files use exclusive creation.

Hosted NVIDIA requests follow the existing process rate limiter below the stated account40rpm. Claude uses the existing USD0.50 run budget guard; a repair uses remaining reported budget, if known. CLI cost is not necessarily actual billing. D and G do not have equal hidden reasoning, token pricing or hardware; this remains a whole-system comparison.

## Outcomes and analysis

Report **initial → final** contract/display acceptance for each arm, separately for development and fresh test. Report the number of repairs, recovery success, repeated failures and added time. Do not compare the new mix of7 cases with v2's5 as if the difference were solely policy effect. Initial vs final within a run is the local recovery observation; it does not prove field usefulness.

Run the same trajectory-audit heuristics on both arms. Direction, numerical and causal flags are review candidates, not automatic semantic errors. Manually inspect selected supporting facts for displayed rationales. Counts of reference-valid facts are not diagnosis accuracy. A withheld output is not an all-correct answer.

Temporal evidence extraction is being implemented independently. It is **not** part of this cycle's model input, preserving isolation of the repair-policy change. A later temporal-tool experiment needs its own frozen corpus and comparison. Do not add a Nano gate, reranker, streaming simulator, or visual redesign to this cycle.

## Stop rule

Finish the fixed run set once, including failures, then audit and decide. No benchmark changes to force a win. A provider or code failure that prevents continuation must be logged and versioned rather than silently resumed with different conditions. Old traces are immutable.
