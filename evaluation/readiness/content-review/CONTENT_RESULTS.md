# V1 rationale-only blind screen, then identity reveal

**Superseded for complete displayed-check scoring.** The [packet erratum](ERRATUM.md) explains that this first packet omitted canonical check text and displayed limits. The original review and hashes remain as an immutable rationale-only screen. Its 39/48 totals must not be used as final check-quality scores; the separately blinded [v2 review](v2/CONTENT_RESULTS.md) assesses the complete displayed checks.

The independent AI reviewer scored the four anonymous packets against the [fixed rubric](RUBRIC.md) and saved [BLIND_REVIEW.json](BLIND_REVIEW.json) before the [reveal key](REVEAL_KEY.json) was opened. Its recorded pre-reveal SHA-256 is `a62becf0b6ea51a09f76bc58c05415bcd8be8baecd12c7d5eb955a2dc6546e7b`; the original packet SHA-256 is `580bf00669cb453ab88b671f4d0e5ab874c4ca25275731c1b94fd5877fca7aa3`. The [reveal script](reveal.py) verifies these hashes, frozen trace hashes, score arithmetic, and packet/check identity. [Machine summary](CONTENT_RESULTS.json) retains the details. Plant-domain expertise was **not independently verified**; this is an AI content screen, not expert validation.

| Case | Ultra domain path | Sonnet restricted-reader path |
|---|---:|---:|
| 3, development exposed | 19/24 | 18/24 |
| 29, fresh at the original cycle-4 run | 20/24 | 21/24 |
| **Paired valid outputs only** | **39/48** | **39/48** |

These totals use only the two cases where **both** original cycle-4 paths produced a valid plan. Every check is scored on factual/time grounding, component meaning, actionability, and uncertainty (0–2 each). The tie does not establish equivalent field utility or either model's superiority. The fixed **all-case output-contract** result remains Ultra **2/4** and Sonnet **4/4**: Ultra cases 52 and 47 were withheld after the planner request cap, and are not silently added to the paired content denominator. The later case-52 `bounded_finalize_v2` run remains development-only.

The reviewer marked missing grounding in **3 of 6 checks per path**. Material examples from the source-linked rationales:

| Case/path/check | Unsupported or imprecise material claim |
|---|---|
| 3 Ultra, secondary flow | “heat power ~43 kW” cites only primary-flow values (966.0, 952.88, 919.0 l/h), with no cited heat-power fact. |
| 3 Ultra, controls | “Setpoint dropped from ~60 °C to ~32 °C between 11:00 and 15:30” has no cited 11:00 or ~60 °C setpoint; cited episode starts at 14:50. The 13.7 °C gap at 15:00 is supported. |
| 3 Sonnet, room impact | “a falling 33.2C setpoint” cites the last value and 10:50 pair only, without an earlier setpoint to establish a fall. |
| 3 Sonnet, secondary flow | “Only primary network meter flow readings are available for the window” cites primary-flow values, not an inventory proving absence of secondary flow. |
| 29 Ultra, secondary flow | “Supply temperature near setpoint” cites no setpoint value; “outdoor temp ~10°C” refers imprecisely to the first 8.55°C reading without its time. |
| 29 Sonnet, maintenance | “Only two prior 'activity' timeline entries ... are on file” cites two entries, not an inventory proving exclusivity. |

The reviewer also gave partial grounding to Ultra case 29's “while ... reads” wording because the cited last-value summary does not provide the exact sample time. Neither path may turn these scores into diagnosis accuracy: no post-event ground truth was shown in packets, and no plant expert or operator judged priority, feasibility, or real benefit. The scored check facts and rationales are unchanged frozen model outputs. Suggested corrections belong in a separately tested future configuration; retroactive wording edits cannot repair the original result.
