# Blind content review, v2

Reviewer: AI content reviewer. Independently verified plant expertise: **no**. This is an internal content screen, not diagnosis accuracy or field utility. I used only the supplied canonical check text, rationales, cited facts, and displayed limits. Scores are in rubric order: factual/time grounding, component meaning, actionable check, calibrated uncertainty.

| Anonymous packet | Check | Scores | Total | Grounding issue or reason |
|---|---|---:|---:|---|
| Q5e28db05 | C-room-impact | 2/2/2/2 | 8 | Cited report and 10:50 secondary supply support the premise; room/radiator measurement tests actual delivery. |
| Q5e28db05 | C-secondary-flow | 0/2/2/2 | 6 | Missing grounding: “Primary network flow ~958 l/h and heat power ~43 kW are present.” Cited endpoints/minimum do not directly support the flow summary, and no heat-power fact is cited. Secondary measurement remains a concrete check. |
| Q5e28db05 | C-controls | 0/2/2/2 | 6 | Missing grounding: “Setpoint dropped from ~60 °C to ~32 °C between 11:00 and 15:30.” Cited facts support the 15:00 gap, but not the starting time/value. Timestamped controller review is concrete. |
| Qa176cd2a | C-room-impact | 0/2/2/2 | 6 | Missing grounding: “a falling 33.2C setpoint.” The cited last setpoint is 33.2 °C; no earlier setpoint establishes the trend. Room verification addresses the delivery limit. |
| Qa176cd2a | C-secondary-flow | 0/2/2/2 | 6 | Missing grounding: “Only primary network meter flow readings are available for the window.” Cited primary readings do not establish a complete source inventory. The check distinguishes the two circuits. |
| Qa176cd2a | C-maintenance | 2/2/2/2 | 8 | Both dated activity entries precede the report. Record/completion verification is concrete and does not assign the current cause. |
| Q56769be9 | C-room-impact | 1/2/2/2 | 7 | The 63.9 °C last value is cited for a 24-hour window, but its precise sample time is absent, making “while” imprecise relative to the 14:18 report. Room verification is apt. |
| Q56769be9 | C-secondary-flow | 0/2/2/2 | 6 | Missing grounding: “Supply temperature near setpoint.” No setpoint is cited for this check; the 8.55 °C first outdoor reading also makes “~10°C” loose. Secondary flow/design comparison is feasible. |
| Q56769be9 | C-controls | 2/2/2/2 | 8 | Cited episodes support gaps above 2 °C and a 13.4 °C maximum. Controller-record review addresses an uncertainty without declaring a fault. |
| Qed762431 | C-room-impact | 2/2/2/2 | 8 | Cited 14:10 paired supply/setpoint and 14:18 report support the premise; room conditions remain unmeasured. |
| Qed762431 | C-secondary-flow | 2/2/2/2 | 8 | 144 total minus 90 within 2 °C supports 54 exceeding 2 °C; the 13.4 °C maximum is cited. Secondary flow/design comparison addresses the remaining question. |
| Qed762431 | C-maintenance | 0/2/2/2 | 6 | Missing grounding: “Only two prior 'activity' timeline entries from Dec 2015 are on file.” Two entries are cited, but completeness is not. Record/completion verification preserves uncertainty. |

| Anonymous packet | Score |
|---|---:|
| Q5e28db05 | 20/24 |
| Qa176cd2a | 20/24 |
| Q56769be9 | 21/24 |
| Qed762431 | 22/24 |

Case 3: **40/48**. Case 29: **43/48**. Overall: **83/96**.
