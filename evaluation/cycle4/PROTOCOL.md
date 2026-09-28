# Cycle 4 — live retrieval, native plan composition, temporal evidence

Frozen before case inference, 2026-09-28. This cycle tests an integrated investigation path, not recomposition of a stored failed answer. Prior cycles remain immutable.

## Cases and hypotheses

Development/regression: reports52 and3. These expose the dependency-closure and temporal-grounding issues already inspected.
Fresh test: reports29/asset17 and47/asset28, selected from the next chronologically eligible public M1 heating complaints on unused assets with compatible fields and >=100 prior24h samples. Input metadata and hashes were fixed before inference in cases.json. Current diagnoses stay outside all inputs.

H1: deriving the observation list from model-selected check references removes duplicated-list inconsistency without inventing facts or silently truncating answers.
H2: querying timestamped paired readings and deviation episodes can support more precise temporal rationales than extrema/averages alone. This cycle evaluates an integrated change, not a causal ablation of each individual feature.
H3: compare the resulting whole system with a restricted Claude Code + Sonnet5 reader given the same permitted information. Model and harness still both differ; superiority of the harness alone cannot be inferred.

## Common information and output

The canonical shared bundle includes the report with fact IDs, the four existing public readers and their facts, descriptive temporal episodes, permitted pre-decision raw window fields and stable per-row paired facts, a source manifest, and the same plan schema. Both arms have access to the same permitted underlying information; corpus and schema hashes must match before runs.

Domain window queries return subsets with the same stable IDs as the shared files. No outcome, private record, or exclusive diagnostic hint is supplied. G chooses relevant files; it is not forced to read every file. No Bash, shell, web, arbitrary host files or unrelated MCP. Read/Glob/Grep and native StructuredOutput are the baseline tool surface.

Both arms produce a plan with unique limit IDs and2–3 distinct check types,1–4 distinct existing supporting fact IDs per check, and nonblank rationales <=240 characters. Neither model writes a second independent observation list. The program derives that list as the ordered union of the MODEL-SELECTED references and applies the unchanged v2 reference validator (maximum12 distinct facts). This is an explicit composition policy, not retroactive repair of older answers.

Both request native schema-constrained generation. Unsupported native constraints such as uniqueItems are checked locally rather than claimed to be decoder-enforced. No answer-text fallback if Claude fails to produce its structured_output field. Invalid plans remain withheld.

D final selection is limited to actually retrieved evidence. G selection is limited to fact IDs exposed by successful case/source/catalog/temporal file reads, not IDs visible only in the schema/task/index. File requests alone are insufficient. ID visibility is still a process check, not proof of semantic understanding or the rationale's entailment.

## Live execution

D: up to6 planning requests over bounded public read tools, then an explicit finish signal and one native final-plan request. The planner does not first generate an unconstrained final answer. Native composition uses this run's retrieved evidence. No inference repair or silent retry. Invalid arguments, out-of-cutoff windows, source failures, or limits are logged and withheld.
G: exact claude-sonnet-5 through Claude Code in safe/restricted configuration, native plan schema, fresh public-only directory and no persistent conversation. USD0.50 guard and300-second timeout. Record actual resolved model, tool results, schema output, wall time and usage. Budget/provider failures are not semantic errors.

NVIDIA requests use the existing18rpm process pacer under the user-provided40rpm account limit. The runner processes one D then one G for each case in order52,3,29,47. One run per arm/case; no configuration edits after the first case inference. No fallback models or best-run selection.

## Temporal scope

Temporal tools describe supply/setpoint paired values and contiguous gaps greater than2°C. This threshold is a descriptive convention, not a validated fault/protection threshold. Window requests are bounded by the replay interval and decision time and limited to24 source rows. No interpolation. Missing/irregular data and truncation are explicit.

A maximum gap's timestamp does not prove a fault or cause. Minimum/maximum are not the first/last values. Review flags identify claims needing human inspection; they do not automatically grade correctness or alter the model's rationale. Temporal measurements and source-field roles must be inspected together.

## Evaluation and stopping rule

Separate development and fresh cases. Report initial/final phases, tool choices, whether temporal sources were actually read, native output validity, reference closure, withheld outcomes, elapsed/request times and available usage. Record reviewer type; author inspection is not independent expert validation. Smaller latency with a failed output is not a successful speedup.

Compare the integrated configurations under these conditions only. Do not pool with cycle3 or call output-contract success diagnosis accuracy. No plant-clock or economic improvement is measured. Finish the fixed four-case set, preserve failures, audit and decide before another version. PDF/landing/video changes are outside this cycle.
