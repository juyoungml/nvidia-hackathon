# Complete displayed-check blind content review

The fresh AI reviewer scored only the anonymous [v2 packets](PACKETS.json) against the [fixed v2 rubric](RUBRIC.md), then saved [BLIND_REVIEW.json](BLIND_REVIEW.json) before the [identity key](REVEAL_KEY.json) was opened. The pre-reveal review SHA-256 is `eb2c91ff3da870b309bc93db768aaf3a2baf984f7db9bbf90e67dde876c7f1f6`; packet SHA-256 is `b6b906712190b46e42a7bb7ebb47398f89ea850f08e5ab83c62b3e79f2a67c07`. The [reveal script](reveal.py) verifies hashes, frozen source traces, packet/check identity, and score arithmetic; [machine results](CONTENT_RESULTS.json) retain each mapped score. Plant expertise was **not independently verified**. This is an internal AI screen, not expert or field validation.

| Originally valid paired case | Ultra domain path | Sonnet restricted-reader path |
|---|---:|---:|
| 3, development exposed | 20/24 | 20/24 |
| 29, fresh at the original cycle-4 run | 21/24 | 22/24 |
| **Paired complete-check content** | **41/48** | **42/48** |

Each of three checks per plan received 0–2 for factual/time grounding, component meaning, actionable verification, and calibrated uncertainty (8 maximum). The one-point difference on two paired cases does not establish model or harness superiority, diagnosis accuracy, or real operator value. The **original all-case output-contract result stays Ultra 2/4 and Sonnet 4/4**: Ultra cases 52 and 47 were withheld after a planning cap. They remain failures in the primary denominator and have no scored final checks. The later case-52 handoff run is a separate development confirmation.

The reviewer marked material citation gaps in **3 of 6 checks for each path**, despite all scored plans passing reference-ID checks. Examples from the frozen rationales:

| Case/path | Material unsupported claim in a proposed check |
|---|---|
| 3 Ultra | “heat power ~43 kW” has no cited heat-power fact; the flow check cites only primary-meter values. Its control check's “~60 °C” at “11:00” lacks the cited reading, though the 13.7 °C gap at 15:00 is cited. |
| 3 Sonnet | “a falling 33.2C setpoint” cites no earlier setpoint. “Only primary network meter flow readings are available” cites primary values but no complete data inventory. |
| 29 Ultra | “Supply temperature near setpoint” cites no setpoint value in that check; the cited first outdoor value is 8.55°C, loosely described as “~10°C” without its time. |
| 29 Sonnet | “Only two prior 'activity' timeline entries ... are on file” cites two entries, not an inventory proving there are only two. |

Ultra's case-29 room-impact wording also blurs the last reading's exact time; its cited summary covers a 24-hour window. The displayed canonical action texts and limits made some checks more actionable than their rationales alone suggested. The [v1 erratum](../ERRATUM.md) preserves the earlier rationale-only review and explains why its 39/48 tie is not the full displayed-check result. The v2 review has no access to post-event diagnoses or actual field outcomes. Any future rationale correction needs a separately tested model/configuration; editing these frozen outputs would invalidate this comparison.
