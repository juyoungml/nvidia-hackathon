# System 2 comparison protocol v1

Frozen before comparative model calls, 2026-09-28. A harmless Claude availability probe was performed; it is not an evaluation sample.

## Hypothesis and claim boundary

A domain-specific investigation harness may produce more grounded and useful next checks than a general coding-agent harness on the same industrial evidence. This is a hypothesis, not a promised outcome.

The primary comparison is whole-system: Nemotron Ultra with domain tools versus Claude Code with Sonnet 5 and restricted file-reading tools. Model and harness both differ. A positive result therefore does not identify the harness alone as the cause. It is not a general ranking of models or coding agents. A Sonnet packet-only secondary arm can examine presentation effects, but also does not isolate the complete harness effect.

## Arms

| Arm | Runtime | Access |
|---|---|---|
| D: domain investigation | Nemotron Ultra / Python bounded tool loop | Case-specific readonly evidence tools and canonical fact catalog |
| G: general file agent | Claude Code 2.1.283 / exact model claude-sonnet-5 | Read, Glob, Grep in an isolated public-only working directory; no command execution, web tools, customizations or unrelated MCP |
| P: optional evidence packet | Claude Code / exact same Sonnet 5 | Same whole evidence packet, no tools; secondary presentation ablation only |

No Nano gate or reranker is required in these arms. Streaming and preemptive monitoring are excluded.

## Common task

Given this asset's reported problem at decision_time, identify what the available evidence establishes, what remains unknown, and two or three justified next checks for an engineer. Do not give a final root cause or recommend changing controls. Use only the supplied public evidence; cite/select the provided fact IDs. Return the common JSON schema.

## Information equivalence

Use a single deterministic case bundle: current problem-only report, the four public reader outputs, signal definitions and a fact catalog generated from these values. G receives them as public files; D receives the same permissible values through tools. The bundle records file hashes and a corpus hash. Do not give one side hidden outcomes, private files, previous answers or evaluator labels. Historical report availability caveats are part of the shared evidence.

Domain prompts and tool structure are the intended treatment. Common output schema and validation are applied to both arms, with raw responses preserved. Never compare a cleaned domain display to an unvalidated Claude response without also showing raw validation and withholding outcomes.

The fact catalog is an information representation, not an answer key for which check to choose. Observations select immutable facts. Free-text rationales remain model-authored and need semantic review. Valid IDs do not establish relevance or support for the proposed action.

## Cases and selection

- Development/regression: public incidents 52, 62, 32 on substation 21. Existing results have been inspected; do not claim these as unseen tests.
- Missing measurements: a separately labeled derived stress test, not a new field incident.
- New-asset cases: first chronologically eligible no/insufficient-heat incident from each of two other substations with compatible fields and at least 100 samples in the preceding 24h. Record availability-based exclusions before inference. Do not select based on model results. If two cannot be acquired within the source timebox, report the shortfall.
- Current diagnosis/remedy remain held out; the same public account cannot establish historical narrative availability.

## Execution budget

Initial pass: one run per arm per case, D then G with no prompt edits after viewing comparative outputs. If interfaces need repair, preserve the failed attempt and mark a new protocol version; do not mix pre/post-repair results in one aggregate. If time allows, repeat the same fixed configuration once and show both runs, not the best. Report incomplete cells and provider failures.

Bounded domain tool rounds: 6. Baseline process timeout: 180 seconds per run. Claude API budget guard: at most USD0.50 per run where supported, not a quoted actual cost. No fallback model. Record exact resolved model, CLI version, available tools, effort/default setting, request/usage metadata where exposed. These are controlled experiments, not strict compute-equivalent inference budgets; hidden reasoning and runtime overhead differ.

Hosted NVIDIA jobs are serialized and paced below the user-provided 40 requests/minute account limit. Local file-reading comparison starts in a fresh public-only temp directory, never the repository or a company project. Existing authenticated Claude account is used without printing credentials.

## Evaluation and decision

1. Execution: success/error, elapsed wall time, model request time when observable, tool/file access count, provider-reported usage. Missing counters are unavailable, not zero.
2. Raw output: valid schema, selected unknown fact IDs, omitted required fields and abstention. Preserve all raw answers.
3. Display contract: displayed observations are canonically rendered from selected facts; unsupported observation text is not silently accepted or given invented citations. A withheld answer is not counted as a fully grounded success.
4. Human/author review: selection relevance, rationale supported by evidence, next-check feasibility/priority, unnecessary checks, unsupported diagnoses and appropriate uncertainty. Author review is not independent expert judgment; report reviewer type.
5. Comparison: per-case differences before any aggregate. Fixed-summary baseline remains a reference, not an operator oracle. Never convert API latency into plant identification time.

A successful system runs and returns a valid supported packet. A better system must improve a relevant quality dimension without concealing extra errors, work or latency. If no such difference appears, retain the conclusion 'comparative advantage not established'. Do not target a judging score or change labels to make a winning result.

## V1 pilot finding and v2 amendment (before v2 inference)

V1 is an integration pilot, not a ranking result. The validator enforced bounds/support relations that were not all disclosed in the shared schema. Claude's outer JSON fence caused an immediate format rejection despite substantive file reads. Domain Ultra on cases52/60/63 returned report-only selections without querying tools. These failures are preserved; no v1 answer is rewritten.

V2 will expose every enforced field/count/length/support rule identically to both arms. A single outer JSON code fence may be removed as a deterministic transport normalization applied to both, with normalization logged; no inferred facts, removed checks, shortened rationales or invented citations. Other malformed content is withheld. The shared renderer labels outputs reference-checked, not semantically verified.

The available-source manifest distinguishes unread evidence from queried evidence with absent values. Domain Ultra is explicitly informed it can inspect sources before claiming unavailability. Completeness of investigation is audited separately from JSON validity; a report-only response is not sufficient evidence of investigation. General Claude has the same manifest and corpus files. Domain-specific tool access and general file tools remain the treatment.

Only one interface revision is planned in this comparison cycle. V2 cases52/60/63 are regression/pilot-exposed, not pristine holdouts. Two further assets may be selected by the same chronological eligibility rule, excluding21/4/7, before v2 calls. If unavailable, report that no fresh holdouts were used. Do not tune prompts after v2 outputs. Non-superiority is an acceptable conclusion.

V2 case order frozen: 52 (development), 60/63 (v1-pilot exposed), 3/13 (fresh assets12/24). Input hashes and selection metadata are in system2-case-manifest.json. One D then one G per case. V2 shared task also states unique check IDs, nonblank rationales, and use only provided catalog IDs. The comparison review is author-reviewed, not independently expert-graded. No v2 prompt changes after observing outputs.

## Exploratory same-model control

After the five primary v2 pairs, one separate case52 probe may expose the same domain readers to Claude Code Sonnet5 through an explicit public-only MCP server, with builtin file/shell/web tools disabled. This keeps Sonnet5 fixed against its file-agent case52 result while changing the evidence interface. It is exploratory, post-hoc, and one familiar case; it is not pooled with primary v2 rates or treated as causal proof across tasks. The task/catalog/corpus remain v2, no fallback models or answer-driven prompt tuning. If the restricted configuration cannot invoke only the intended tools, report the configuration failure rather than relaxing access. Record exact flags and tool calls.
