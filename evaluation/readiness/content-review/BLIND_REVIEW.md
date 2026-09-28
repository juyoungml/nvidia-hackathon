# Blind check-content review

Reviewer: AI reviewer; domain expertise was not independently verified. This is an internal content screen of the four anonymous packets supplied for cases 3 and 29. Each check uses the fixed 0–2 grounding, component meaning, actionability, and uncertainty criteria. Scores describe proposed-check quality, not diagnosis accuracy or the origin of any packet.

| Case | Packet | Check | Grounding | Components | Action | Uncertainty | Total | Missing grounding |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 3 | Paa639619 | C-room-impact | 2 | 2 | 2 | 2 | 8/8 | No |
| 3 | Paa639619 | C-secondary-flow | 0 | 2 | 2 | 2 | 6/8 | Yes |
| 3 | Paa639619 | C-controls | 0 | 2 | 2 | 1 | 5/8 | Yes |
| 3 | Pef137f64 | C-room-impact | 0 | 2 | 0 | 2 | 4/8 | Yes |
| 3 | Pef137f64 | C-secondary-flow | 0 | 2 | 2 | 2 | 6/8 | Yes |
| 3 | Pef137f64 | C-maintenance | 2 | 2 | 2 | 2 | 8/8 | No |
| 29 | P8119cb42 | C-room-impact | 2 | 2 | 2 | 2 | 8/8 | No |
| 29 | P8119cb42 | C-secondary-flow | 2 | 2 | 2 | 2 | 8/8 | No |
| 29 | P8119cb42 | C-maintenance | 0 | 2 | 1 | 2 | 5/8 | Yes |
| 29 | Pd1d3ec43 | C-room-impact | 1 | 2 | 2 | 2 | 7/8 | No |
| 29 | Pd1d3ec43 | C-secondary-flow | 0 | 2 | 2 | 2 | 6/8 | Yes |
| 29 | Pd1d3ec43 | C-controls | 2 | 2 | 2 | 1 | 7/8 | No |

## Case 3

**Paa639619 — 19/24.** C-room-impact correctly places the no-heat report at 2015-12-01 10:56 and the 33.5 °C secondary supply at 10:50. Measuring room or radiator temperatures and mapping affected areas tests actual delivery. C-secondary-flow correctly separates primary from secondary flow and asks for a direct secondary measurement, but **“heat power ~43 kW” has no cited heat-power source**. Its cited primary-flow summaries are 966.0, 952.88, and 919.0 l/h. C-controls gives a supported 13.7 °C supply/setpoint gap at 2015-11-30 15:00 and a feasible timestamped-record review, but **“Setpoint dropped from ~60 °C to ~32 °C between 11:00 and 15:30” lacks a cited 11:00 or ~60 °C reading**. The cited episode begins at 14:50 with setpoint 45.9 °C and supports 32.0 °C at 15:00 and 15:30. The controls check gives some caution by requesting review, yet does not explicitly bound what the gap establishes.

**Pef137f64 — 18/24.** C-room-impact correctly distinguishes the 33.5 °C secondary supply and 33.2 °C setpoint from room heat delivery. **“A falling 33.2C setpoint” is unsupported**: only the last setpoint and the 10:50 pair are cited. The rationale names a delivery uncertainty but gives no concrete room or radiator verification. C-secondary-flow proposes a useful direct measurement against a design range and acknowledges that the range is unsupplied. **“Only primary network meter flow readings are available for the window” is a completeness claim unsupported by the four cited primary-flow summaries**, which do not establish the absence of secondary-flow data. C-maintenance accurately cites activity events on 2014-10-21 and 2015-07-08, asks to verify completion evidence, and does not infer this event's cause from prior activity.

The two case-3 packets total **37/48** across six checks.

## Case 29

**P8119cb42 — 21/24.** C-room-impact accurately places the 2019-01-09 14:18 report after the 14:10 pair of 63.9 °C secondary supply and 63.8 °C setpoint; room or radiator temperature would test delivery. C-secondary-flow uses the 24-hour summaries correctly: 144 samples, 90 within 2 °C, so 54 outside 2 °C, with maximum absolute gap 13.4 °C. Its secondary-flow measurement against the design range addresses a real uncertainty. C-maintenance cites two December 2015 activity entries, but **“Only two prior 'activity' timeline entries ... are on file” has no cited inventory proving exclusivity**. It appropriately leaves relevance and completion unknown, while giving no specific record or inspection method for verification.

**Pd1d3ec43 — 20/24.** C-room-impact cites the 14:18 report and the last secondary-supply value of 63.9 °C, but **“while ... reads” blurs the reading time**: the cited summary gives a 24-hour window and no exact sample timestamp. The requested room/radiator measurements and impact scope are useful. C-secondary-flow distinguishes supply temperature from flow and requests direct measurement, but **“Supply temperature near setpoint” has no cited setpoint value**. The cited outdoor temperature is the *first* 8.55 °C reading, imprecisely restated as “~10°C” without its time. C-controls accurately describes multiple cited episodes with absolute gaps over 2 °C and the 13.4 °C gap at 2019-01-09 07:40. Reviewing timestamped controller records is actionable. Its uncertainty score is 1 because it omits the cited caveat that the 2 °C threshold is descriptive, not a verified operating limit.

The two case-29 packets total **41/48** across six checks. Across both cases, the four packets total **78/96** across twelve checks. These scores do not evaluate failed or withheld plans, all-case success, expert agreement, or diagnosis accuracy.
