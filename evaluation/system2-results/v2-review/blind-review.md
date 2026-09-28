# Blinded paired review — contract v2

Review selected evidence and suggested checks. Fact IDs show reference links only; they do not prove the rationale or action is correct.

## Pair 1 — PreDist-M1-fault-52

### Response A

Observations:
- F-46253c9e467c: Reported problem: no heat (2016-12-12 15:55:00)
- F-b45e0f50730a: Last measurement time: 2016-12-12 15:50:00 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1e7ecd90bb5d: Measurement sample count: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-e67e4656247f: secondary_heating_circuit_supply_temperature_c mean: 64.89 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1c85f00bbfb8: Secondary supply/setpoint absolute gap mean: 0.31 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-cecb8a6f47ee: Secondary supply/setpoint absolute gap max: 1.6 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-24f2f5b9ece6: Secondary supply/setpoint absolute gap samples_within_2C: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-e28ba199fb91: outdoor_temperature_c last: 4.75 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1162dd37046d: problem: not enough heat
- F-d4658b929c69: event_description: The heaters are not getting warm enough. Supply temperature is 44°C at 9°C outdoor temperature. Heating curve increased.
- F-534816eba1b3: report_date: 2016-12-06 13:12:00
- F-27e89a2c6343: primary_network_meter_flow_l_per_hour first: 2208.0 l/h (2016-12-11 15:55:00 to 2016-12-12 15:55:00)

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-46253c9e467c, F-e67e4656247f, F-1c85f00bbfb8
  - Rationale: Secondary supply temp tracks setpoint closely (mean gap 0.31°C) yet 'no heat' is reported; room/radiator temps are needed to confirm whether heat actually reached occupied spaces.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-27e89a2c6343
  - Rationale: Only primary network-side flow is available; secondary/customer circuit flow (e.g. blocked valve, pump, or airlock) is unmeasured and needed to explain a no-heat complaint.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-d4658b929c69, F-534816eba1b3
  - Rationale: A prior 'not enough heat' fault 6 days earlier led to a heating curve increase; verify whether that change was completed/held and check for further timestamped adjustments before this report.

### Response B

Observations:
- F-46253c9e467c: Reported problem: no heat (2016-12-12 15:55:00)
- F-b45e0f50730a: Last measurement time: 2016-12-12 15:50:00 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1e7ecd90bb5d: Measurement sample count: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-93b39b46d22e: secondary_heating_circuit_supply_temperature_c last: 68.3 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-9db9d7f33910: secondary_heating_circuit_supply_setpoint_c last: 68.6 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1c85f00bbfb8: Secondary supply/setpoint absolute gap mean: 0.31 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-24f2f5b9ece6: Secondary supply/setpoint absolute gap samples_within_2C: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-fbb20eec0816: primary_network_meter_heat_power_kw last: 132.0 kW (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-59bbecd029bb: primary_network_meter_flow_l_per_hour last: 2496.0 l/h (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-534816eba1b3: report_date: 2016-12-06 13:12:00
- F-d4658b929c69: event_description: The heaters are not getting warm enough. Supply temperature is 44°C at 9°C outdoor temperature. Heating curve increased.
- F-8ece65de9685: event_start: 2016-12-06 13:12:00

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-46253c9e467c, F-93b39b46d22e, F-9db9d7f33910, F-1c85f00bbfb8
  - Rationale: Supply temperature tracks setpoint (mean gap 0.31°C) but the customer reports no heat; room/radiator temperatures are needed to confirm delivery.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-fbb20eec0816, F-59bbecd029bb
  - Rationale: Primary heat power (132 kW) and primary flow (2496 l/h) are present, but primary flow is not secondary circuit flow; secondary flow measurement is required to verify heat transport to the customer circuit.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-534816eba1b3, F-d4658b929c69, F-8ece65de9685
  - Rationale: A prior 'not enough heat' fault on 2016-12-06 with heating curve increase was logged; maintenance records should be checked for actions taken and whether they resolved the earlier issue.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 2 — PreDist-M1-fault-60

### Response A

Observations:
- F-9bbe792a0045: Reported problem: no heat (2015-03-18 18:54:00)
- F-dd9011d62d52: Last measurement time: 2015-03-18 18:50:00 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-6ff5c26c5cfa: Measurement sample count: 144 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-dc13385eb733: secondary_heating_circuit_supply_temperature_c first: 48.7 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-63373edd6035: secondary_heating_circuit_supply_temperature_c last: 45.2 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-456a99219d53: secondary_heating_circuit_supply_setpoint_c last: 45.55 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-19132f4b4712: Secondary supply/setpoint absolute gap max: 4.0 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-895e958010cf: Secondary supply/setpoint absolute gap mean: 0.85 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-ca2beb6959da: Secondary supply/setpoint absolute gap samples_within_2C: 142 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-2c66e1e84dfe: primary_network_meter_flow_l_per_hour mean: 585.32 l/h (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-a4068ebd07e3: event_start: 2015-02-27 00:00:00
- F-4a77b8692889: type: activity

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-9bbe792a0045, F-dc13385eb733, F-895e958010cf, F-ca2beb6959da
  - Rationale: Secondary supply temp tracked setpoint within 2°C for 142/144 samples, yet 'no heat' was reported; room/radiator readings are needed to confirm actual heat delivery.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-2c66e1e84dfe, F-9bbe792a0045
  - Rationale: Only primary network-side flow is recorded; secondary/customer circuit flow, which would reveal a delivery restriction behind the substation, is not available.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-a4068ebd07e3, F-4a77b8692889
  - Rationale: An 'activity' record from 2015-02-27 exists for this asset; confirm what work was performed and whether it bears on the current no-heat report.

### Response B

Response withheld by the common display contract.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 3 — PreDist-M1-fault-63

### Response A

Observations:
- F-69316e2d375d: Reported problem: not enough heat (2015-03-26 07:15:00)
- F-a687d0803fd1: Last measurement time: 2015-03-26 07:10:00 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-c8cb3c25b2cc: Measurement sample count: 144 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-a01df1be2631: outdoor_temperature_c mean: 13.26 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-9be51bd7f6bf: secondary_heating_circuit_supply_temperature_c mean: 39.17 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-46bad74a3812: secondary_heating_circuit_supply_setpoint_c mean: 39.02 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-d78afb06f6f7: Secondary supply/setpoint absolute gap mean: 0.83 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-a98e3d3b2120: Secondary supply/setpoint absolute gap samples_within_2C: 142 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-dfa23fbd5bd0: primary_network_meter_heat_power_kw last: 14.67 kW (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-f5d1722b5f67: primary_network_meter_flow_l_per_hour last: 296.67 l/h (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-97ec1ee13138: event_start: 2015-02-27 00:00:00
- F-8b4aa49e516a: type: activity

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-9be51bd7f6bf, F-46bad74a3812, F-d78afb06f6f7
  - Rationale: Secondary supply temp tracks its setpoint closely (mean gap 0.83°C), but this alone does not confirm rooms/radiators actually received adequate heat.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-f5d1722b5f67
  - Rationale: Only primary network meter flow is available and is declining; secondary/customer circuit flow, which drives room heat delivery, is not present in this dataset.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-97ec1ee13138, F-8b4aa49e516a
  - Rationale: A logged activity/disturbance starting 2015-02-27 predates this report; verify what work occurred and whether it was completed or left in an interim state.

### Response B

Response withheld by the common display contract.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 4 — PreDist-M1-fault-3

### Response A

Observations:
- F-ef44adf80dfa: Reported problem: no heat (2015-12-01 10:56:00)
- F-9ed405e5b246: Last measurement time: 2015-12-01 10:50:00 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-66f181445725: Measurement sample count: 144 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-48cab40b6611: secondary_heating_circuit_supply_temperature_c first: 60.1 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-b7507a067c23: secondary_heating_circuit_supply_temperature_c last: 33.5 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-33dccbc149c8: secondary_heating_circuit_supply_temperature_c min: 31.2 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-9c66c7e1f3c5: secondary_heating_circuit_supply_setpoint_c first: 60.0 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-2a7e55330ddf: secondary_heating_circuit_supply_setpoint_c last: 33.2 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-cb28a4f26b14: secondary_heating_circuit_supply_setpoint_c min: 32.0 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-43ca19ae022d: Secondary supply/setpoint absolute gap max: 13.7 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0babad9264aa: Secondary supply/setpoint absolute gap mean: 0.56 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0652747a3cb7: Secondary supply/setpoint absolute gap samples_within_2C: 139 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)

Limits:
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-ef44adf80dfa, F-b7507a067c23, F-2a7e55330ddf
  - Rationale: Customer reports no heat while secondary supply temperature dropped to 33.5°C with setpoint at 33.2°C; room/radiator temperatures are needed to confirm delivery failure scope.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-ef44adf80dfa, F-48cab40b6611, F-b7507a067c23
  - Rationale: Secondary supply temperature fell from 60.1°C to 33.5°C over 24h; secondary circuit flow measurement is required to determine if flow loss caused the temperature drop and heat loss.
- C-controls: Review timestamped controller settings, alarms, and parameter changes with an engineer.
  - Selected supporting fact IDs: F-43ca19ae022d, F-0babad9264aa, F-0652747a3cb7
  - Rationale: Supply/setpoint gap reached 13.7°C max with 5 samples outside ±2°C; timestamped controller settings and alarms should be reviewed to identify control anomalies during the temperature drop.

### Response B

Observations:
- F-ef44adf80dfa: Reported problem: no heat (2015-12-01 10:56:00)
- F-9ed405e5b246: Last measurement time: 2015-12-01 10:50:00 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-66f181445725: Measurement sample count: 144 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-9c66c7e1f3c5: secondary_heating_circuit_supply_setpoint_c first: 60.0 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-2a7e55330ddf: secondary_heating_circuit_supply_setpoint_c last: 33.2 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-b7507a067c23: secondary_heating_circuit_supply_temperature_c last: 33.5 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-43ca19ae022d: Secondary supply/setpoint absolute gap max: 13.7 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0babad9264aa: Secondary supply/setpoint absolute gap mean: 0.56 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0652747a3cb7: Secondary supply/setpoint absolute gap samples_within_2C: 139 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-8b748d964212: primary_network_meter_heat_power_kw first: 44.0 kW (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-7f0c28debb69: primary_network_meter_heat_power_kw last: 42.62 kW (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-37c78c517194: primary_network_meter_flow_l_per_hour first: 966.0 l/h (2015-11-30 10:56:00 to 2015-12-01 10:56:00)

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-ef44adf80dfa, F-0babad9264aa, F-0652747a3cb7
  - Rationale: Secondary supply mostly tracks setpoint (mean gap 0.56°C, 139/144 within 2°C) yet 'no heat' is reported; room/radiator data is needed to reconcile.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-37c78c517194, F-8b748d964212, F-7f0c28debb69
  - Rationale: Only primary network flow/power is available and heat power stays near 41-44 kW; secondary circuit flow is needed to confirm delivery to the customer loop.
- C-controls: Review timestamped controller settings, alarms, and parameter changes with an engineer.
  - Selected supporting fact IDs: F-9c66c7e1f3c5, F-2a7e55330ddf
  - Rationale: Setpoint fell from 60.0°C to 33.2°C over the window; timestamped controller/schedule records would show if this was a scheduled setback or a parameter fault.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 5 — PreDist-M1-fault-13

### Response A

Response withheld by the common display contract.

### Response B

Observations:
- F-74d2687f0f6a: Reported problem: not enough heat (2016-01-12 12:39:00)
- F-e533c7b71c19: Last measurement time: 2016-01-12 12:30:00 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-76f097b4bb71: Measurement sample count: 144 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-3aaa69be60f2: outdoor_temperature_c first: 2.7 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-cbd43dbf4315: outdoor_temperature_c last: 3.2 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-5be6a6a884ef: secondary_heating_circuit_supply_temperature_c mean: 76.01 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-587b0e46b55e: secondary_heating_circuit_supply_temperature_c min: 61.1 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-e31ef65b2ab3: Secondary supply/setpoint absolute gap max: 14.6 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-2abfdf6f84a3: Secondary supply/setpoint absolute gap mean: 1.18 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-25d1b55d4995: Secondary supply/setpoint absolute gap samples_within_2C: 134 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-b70027084428: primary_network_meter_flow_l_per_hour first: 494.67 l/h (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-12c8e7cd8315: event_start: 2015-12-08 00:00:00

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-74d2687f0f6a, F-2abfdf6f84a3, F-25d1b55d4995
  - Rationale: Secondary supply mostly tracked setpoint (mean gap 1.18°C, 134/144 samples within 2°C) but no room/radiator data exists to confirm reported heat loss reached occupied spaces.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-b70027084428
  - Rationale: Only primary network-side flow is available; secondary/customer circuit flow, which governs delivered heat, is not present in this measurement set and should be obtained.
- C-sensor: Confirm sensor identity, calibration, and timestamp alignment before interpreting a trend.
  - Selected supporting fact IDs: F-587b0e46b55e, F-e31ef65b2ab3
  - Rationale: Supply temperature dipped to 61.1°C and the supply/setpoint gap peaked at 14.6°C; confirm sensor identity, calibration, and timestamp alignment before treating these as real deficits.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

