# Blinded check-content review rubric

Fixed before packet generation on 2026-09-28. Review each proposed check using only its shown rationale and cited pre-decision facts. Do not infer an event's cause from a later outcome. Score four criteria separately, each 0–2 (maximum 8 per check):

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Factual and time grounding | A material numeric, time, trend, or causal claim is contradicted or unsupported by the cited facts; or the cited facts are absent | Main observation is supported but some material detail is imprecise or lacks a direct citation | Every material observation is supported with the right value, field role, and time window; no unsupported cause claim |
| Component meaning | Confuses primary/secondary side, setpoint/measured supply, or supply/customer-room delivery | Component relationship is mostly right but an important distinction is unclear | Correctly distinguishes relevant components and limits of inference |
| Actionable check | No concrete verification or asks for unavailable/unsafe determination | Names a check but leaves method, target, or decision value vague | Specifies a feasible measurement, record, or inspection and why it resolves a stated uncertainty |
| Calibrated uncertainty | States a fault/cause or benefit as established without evidence | Some caution, but overstates or omits an important limit | Explicitly bounds what is unknown and avoids unsupported fault attribution |

For factual grounding, **an existing fact ID alone earns no credit**. Use the cited text/value and timestamp; a missing cited source for a material claim requires 0 even if the claim may exist elsewhere in the catalog. Mark `missing_grounding=true` for that check and quote the claim and missing support. An appropriate check can score well despite an output-contract failure elsewhere, but failed/withheld plans receive no packet and stay failures in all-case success. Each check has equal weight. Compare paired cases 3 and 29 separately, showing per-case and overall sums/denominators; do not turn these content scores into diagnosis accuracy or a claim about the harness alone. Report reviewer's type and whether expertise is independently verified. This rubric is an internal screening instrument, not the submission-readiness 100-point rubric.
