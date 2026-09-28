# Observed replay results — 2026-09-28

These are single runs of three published PreDist incidents and two separately labeled derived probes. The [comparison](comparison.json) keeps the exact final text and structural checks; [trace fixtures](traces/) keep gate decisions, read-only tool calls, and model output. The deterministic summary baseline used the same replay evidence but made no model or tool calls. It is not a field diagnostic benchmark.

| Replay | Kind | Nano gate | Rules gate | Ultra tools | Current report ID cited | Measurement ID cited | Undefined tags | Nano / Ultra request time |
| --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| fault 52 | Published incident | Review, valid | Review | 2 | No | No | 0 | 6.70 / 22.90 s |
| fault 62 | Published incident | Review, valid | Review | 2 | Yes | Yes | 0 | 11.50 / 17.29 s |
| fault 32 | Published incident | Review, valid | Review | 2 | No | Yes | 0 | 6.26 / 18.63 s |
| no-report window | Derived probe | Review, valid; erroneous service-loss rationale | No review | 0 | N/A | N/A | N/A | 10.09 / 0 s |
| missing measurements | Derived probe | Review, valid | Review | 2 | Yes | No observed rows | 0 | 3.54 / 12.32 s |

The three published complaints all escalated; this alone does not show that Nano adds value over the simple complaint keyword rule, which also escalated all three. The no-report probe produced a Nano escalation and an invented service-loss rationale even though no complaint was supplied. Since no published report is not a verified normal operating label, this is a probe failure, not a measured field false-positive rate. No Ultra call was made on that gate-only probe. In the artificial missing-measurement probe, the investigator stated that there were zero sensor samples and withheld a root-cause conclusion.

The structural audit found no invalid full-form source IDs or undefined signal tags in the four investigation answers, but citation **coverage** is incomplete. Fault 52's answer gave numeric readings without citing the measurement source ID; fault 32 omitted the current complaint source ID. Fault 62 cited both. This is why manual claim-by-claim review remains necessary. Prior-report retrospective narratives have uncertain real-time availability and should not be treated as guaranteed operator knowledge.

These durations are model request times. They exclude preparation, field checks, operator work, and fault identification. No time saving, diagnostic accuracy, or statistical superiority is established by this small replay.
