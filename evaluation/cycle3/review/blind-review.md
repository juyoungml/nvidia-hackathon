# Blinded paired review — contract v2

Review selected evidence and suggested checks. Fact IDs show reference links only; they do not prove the rationale or action is correct.

## Pair 1 — PreDist-M1-fault-52

### Response A

Observations:
- F-46253c9e467c: Reported problem: no heat (2016-12-12 15:55:00)
- F-b45e0f50730a: Last measurement time: 2016-12-12 15:50:00 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-1e7ecd90bb5d: Measurement sample count: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-49c6415537c0: secondary_heating_circuit_supply_temperature_c first: 63.3 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-93b39b46d22e: secondary_heating_circuit_supply_temperature_c last: 68.3 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-d7de9712bbee: secondary_heating_circuit_supply_temperature_c min: 57.7 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-cecb8a6f47ee: Secondary supply/setpoint absolute gap max: 1.6 °C (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-24f2f5b9ece6: Secondary supply/setpoint absolute gap samples_within_2C: 144 (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-27e89a2c6343: primary_network_meter_flow_l_per_hour first: 2208.0 l/h (2016-12-11 15:55:00 to 2016-12-12 15:55:00)
- F-b94b6c2ec90e: type: fault
- F-1162dd37046d: problem: not enough heat
- F-d4658b929c69: event_description: The heaters are not getting warm enough. Supply temperature is 44°C at 9°C outdoor temperature. Heating curve increased.

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-46253c9e467c, F-93b39b46d22e, F-cecb8a6f47ee, F-24f2f5b9ece6
  - Rationale: Secondary supply temp stayed within 1.6°C of setpoint for all 144 samples, yet 'no heat' was reported; verify actual room/radiator temperatures to confirm scope of loss.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-27e89a2c6343, F-46253c9e467c
  - Rationale: Only primary network meter flow is present in the window; measure secondary/customer circuit flow to check whether reduced circulation could explain 'no heat' despite tracked supply temp.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-b94b6c2ec90e, F-1162dd37046d, F-d4658b929c69
  - Rationale: A fault was logged 2016-12-06 with a prior 'not enough heat' complaint and a heating-curve increase; confirm what maintenance action followed and whether it held before this report.

### Response B

Response withheld by the common display contract.

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
- F-405ca7eb2be8: secondary_heating_circuit_supply_temperature_c mean: 47.53 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-63373edd6035: secondary_heating_circuit_supply_temperature_c last: 45.2 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-456a99219d53: secondary_heating_circuit_supply_setpoint_c last: 45.55 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-895e958010cf: Secondary supply/setpoint absolute gap mean: 0.85 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-19132f4b4712: Secondary supply/setpoint absolute gap max: 4.0 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-ca2beb6959da: Secondary supply/setpoint absolute gap samples_within_2C: 142 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-e412506ba70d: primary_network_meter_heat_power_kw mean: 35.0 kW (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-a4068ebd07e3: event_start: 2015-02-27 00:00:00
- F-4a77b8692889: type: activity

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-9bbe792a0045, F-405ca7eb2be8, F-895e958010cf
  - Rationale: Secondary supply temp averages 47.5°C and stays near setpoint (mean gap 0.85°C) despite a 'no heat' report, so room/radiator temps are needed to confirm whether heat actually reached the space.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-e412506ba70d, F-19132f4b4712
  - Rationale: Only primary network heat power/flow is recorded here, not secondary circuit flow; a max supply/setpoint gap of 4.0°C also warrants direct secondary flow data to assess delivery.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-a4068ebd07e3, F-4a77b8692889
  - Rationale: A prior 'activity' event on 2015-02-27 exists in the timeline; confirm its scope and completion status before relating it to this later report.

### Response B

Observations:
- F-9bbe792a0045: Reported problem: no heat (2015-03-18 18:54:00)
- F-dd9011d62d52: Last measurement time: 2015-03-18 18:50:00 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-6ff5c26c5cfa: Measurement sample count: 144 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-0b57fb7764db: outdoor_temperature_c mean: 10.69 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-405ca7eb2be8: secondary_heating_circuit_supply_temperature_c mean: 47.53 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-a56eae412830: secondary_heating_circuit_supply_temperature_c min: 43.4 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-c21a8a5cf738: secondary_heating_circuit_supply_setpoint_c mean: 47.45 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-6c35d9a45135: secondary_heating_circuit_supply_setpoint_c min: 45.0 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-895e958010cf: Secondary supply/setpoint absolute gap mean: 0.85 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-19132f4b4712: Secondary supply/setpoint absolute gap max: 4.0 °C (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-ca2beb6959da: Secondary supply/setpoint absolute gap samples_within_2C: 142 (2015-03-17 18:54:00 to 2015-03-18 18:54:00)
- F-a4068ebd07e3: event_start: 2015-02-27 00:00:00

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-9bbe792a0045, F-405ca7eb2be8, F-a56eae412830
  - Rationale: Customer reports no heat while secondary supply temperature tracks setpoint (43.4–53.4 °C); need to verify actual room/radiator temperatures and scope of heating loss.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-9bbe792a0045, F-405ca7eb2be8, F-a56eae412830
  - Rationale: Secondary supply temperature is near setpoint but primary flow is not customer flow; measure secondary circuit flow to confirm heat delivery to rooms.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-9bbe792a0045, F-a4068ebd07e3
  - Rationale: A maintenance activity occurred on 2015-02-27; check records and completion evidence for any work that could affect current heating performance.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 3 — PreDist-M1-fault-63

### Response A

Response withheld by the common display contract.

### Response B

Observations:
- F-69316e2d375d: Reported problem: not enough heat (2015-03-26 07:15:00)
- F-a687d0803fd1: Last measurement time: 2015-03-26 07:10:00 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-c8cb3c25b2cc: Measurement sample count: 144 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-9be51bd7f6bf: secondary_heating_circuit_supply_temperature_c mean: 39.17 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-46bad74a3812: secondary_heating_circuit_supply_setpoint_c mean: 39.02 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-e85947b2b70b: Secondary supply/setpoint absolute gap max: 2.6 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-d78afb06f6f7: Secondary supply/setpoint absolute gap mean: 0.83 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-a98e3d3b2120: Secondary supply/setpoint absolute gap samples_within_2C: 142 (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-053200a22c99: primary_network_meter_heat_power_kw mean: 31.75 kW (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-dfa23fbd5bd0: primary_network_meter_heat_power_kw last: 14.67 kW (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-a01df1be2631: outdoor_temperature_c mean: 13.26 °C (2015-03-25 07:15:00 to 2015-03-26 07:15:00)
- F-97ec1ee13138: event_start: 2015-02-27 00:00:00

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-9be51bd7f6bf, F-46bad74a3812, F-e85947b2b70b
  - Rationale: Secondary supply temp tracks setpoint within ~2.6C max gap, but no room/radiator data confirms whether the reported heat loss reflects actual delivered heat.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-053200a22c99, F-dfa23fbd5bd0
  - Rationale: Only primary-side flow/heat power is available (mean 31.75kW, declining to 14.67kW); secondary circuit flow driving customer-side heat delivery is unmeasured.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-97ec1ee13138
  - Rationale: An activity timeline event on 2015-02-27 precedes the report; completion and nature of that work are unconfirmed by the available records.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 4 — PreDist-M1-fault-3

### Response A

Response withheld by the common display contract.

### Response B

Observations:
- F-ef44adf80dfa: Reported problem: no heat (2015-12-01 10:56:00)
- F-9ed405e5b246: Last measurement time: 2015-12-01 10:50:00 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-66f181445725: Measurement sample count: 144 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-48cab40b6611: secondary_heating_circuit_supply_temperature_c first: 60.1 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-b7507a067c23: secondary_heating_circuit_supply_temperature_c last: 33.5 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-9c66c7e1f3c5: secondary_heating_circuit_supply_setpoint_c first: 60.0 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-2a7e55330ddf: secondary_heating_circuit_supply_setpoint_c last: 33.2 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-43ca19ae022d: Secondary supply/setpoint absolute gap max: 13.7 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0babad9264aa: Secondary supply/setpoint absolute gap mean: 0.56 °C (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-0652747a3cb7: Secondary supply/setpoint absolute gap samples_within_2C: 139 (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-8b748d964212: primary_network_meter_heat_power_kw first: 44.0 kW (2015-11-30 10:56:00 to 2015-12-01 10:56:00)
- F-37c78c517194: primary_network_meter_flow_l_per_hour first: 966.0 l/h (2015-11-30 10:56:00 to 2015-12-01 10:56:00)

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-8b748d964212, F-b7507a067c23, F-ef44adf80dfa
  - Rationale: Primary heat power and secondary supply temp are nonzero at report time, so verify actual room/radiator temperatures to confirm scope of the 'no heat' complaint.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-37c78c517194, F-b7507a067c23
  - Rationale: Only primary network flow is available; secondary/customer circuit flow is needed to assess actual heat delivery to the building.
- C-controls: Review timestamped controller settings, alarms, and parameter changes with an engineer.
  - Selected supporting fact IDs: F-9c66c7e1f3c5, F-2a7e55330ddf, F-43ca19ae022d
  - Rationale: Secondary supply setpoint fell from 60.0 to 33.2 °C with a max 13.7 °C tracking gap; review controller settings/logs to understand this change.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 5 — PreDist-M1-fault-13

### Response A

Observations:
- F-74d2687f0f6a: Reported problem: not enough heat (2016-01-12 12:39:00)
- F-76f097b4bb71: Measurement sample count: 144 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-e533c7b71c19: Last measurement time: 2016-01-12 12:30:00 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-587b0e46b55e: secondary_heating_circuit_supply_temperature_c min: 61.1 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-e31ef65b2ab3: Secondary supply/setpoint absolute gap max: 14.6 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-25d1b55d4995: Secondary supply/setpoint absolute gap samples_within_2C: 134 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-2abfdf6f84a3: Secondary supply/setpoint absolute gap mean: 1.18 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-c89827a7e4f9: outdoor_temperature_c mean: 2.47 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-a667c2edb6fb: primary_network_meter_flow_l_per_hour last: 737.0 l/h (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-b70027084428: primary_network_meter_flow_l_per_hour first: 494.67 l/h (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-b04d38b114c2: type: activity
- F-12c8e7cd8315: event_start: 2015-12-08 00:00:00

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-587b0e46b55e, F-e31ef65b2ab3, F-25d1b55d4995
  - Rationale: Secondary supply temp dipped to a 61.1°C min with a 14.6°C max gap vs setpoint; verify room/radiator temps to confirm scope of the reported heat shortfall.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-a667c2edb6fb, F-b70027084428
  - Rationale: Only primary network-side flow is available (494.67→737 l/h); secondary/customer circuit flow is needed to assess actual heat delivery to the building.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-12c8e7cd8315, F-b04d38b114c2
  - Rationale: An 'activity' record from 2015-12-08 precedes this report by over a month; check its scope, target, and completion status relative to substation 24.

### Response B

Observations:
- F-74d2687f0f6a: Reported problem: not enough heat (2016-01-12 12:39:00)
- F-e533c7b71c19: Last measurement time: 2016-01-12 12:30:00 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-76f097b4bb71: Measurement sample count: 144 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-c89827a7e4f9: outdoor_temperature_c mean: 2.47 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-2d9343c3f820: secondary_heating_circuit_supply_temperature_c last: 74.2 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-7edfef90520f: secondary_heating_circuit_supply_setpoint_c last: 74.2 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-587b0e46b55e: secondary_heating_circuit_supply_temperature_c min: 61.1 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-664e1a9d209f: secondary_heating_circuit_supply_setpoint_c max: 89.7 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-e31ef65b2ab3: Secondary supply/setpoint absolute gap max: 14.6 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-2abfdf6f84a3: Secondary supply/setpoint absolute gap mean: 1.18 °C (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-25d1b55d4995: Secondary supply/setpoint absolute gap samples_within_2C: 134 (2016-01-11 12:39:00 to 2016-01-12 12:39:00)
- F-12c8e7cd8315: event_start: 2015-12-08 00:00:00

Limits:
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-74d2687f0f6a, F-2d9343c3f820, F-7edfef90520f
  - Rationale: Customer reports insufficient heat while secondary supply tracks setpoint; need to verify actual room/radiator temperatures to confirm delivery scope.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-74d2687f0f6a, F-587b0e46b55e, F-e31ef65b2ab3
  - Rationale: Secondary supply temperature dipped to 61.1°C with a 14.6°C max gap to setpoint; measuring secondary circuit flow will show if flow limitation caused the temperature drop and heat deficit.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-74d2687f0f6a, F-12c8e7cd8315
  - Rationale: A maintenance activity occurred on 2015-12-08; check records for completion evidence and any valve, pump, or control changes that could affect current heat delivery.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 6 — PreDist-M1-fault-37

### Response A

Observations:
- F-a4bcf4f332fc: Reported problem: no heat (2018-11-21 09:15:00)
- F-5443bc3ab0b7: Last measurement time: 2018-11-21 09:10:00 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-bc3c8bc8a41b: Measurement sample count: 144 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-60e0cfd3d785: secondary_heating_circuit_supply_temperature_c first: 57.25 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-2afa9fb125d4: secondary_heating_circuit_supply_temperature_c last: 58.3 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-adfaa143fad1: secondary_heating_circuit_supply_setpoint_c first: 56.95 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-ec17bac45866: secondary_heating_circuit_supply_setpoint_c last: 57.6 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-c292053f390c: Secondary supply/setpoint absolute gap max: 1.4 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-7fbf261dc4b4: Secondary supply/setpoint absolute gap mean: 0.61 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-2bff541f4d0b: Secondary supply/setpoint absolute gap sample_count: 144 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-e7602ff614f0: Secondary supply/setpoint absolute gap samples_within_2C: 144 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-2e7cbf1adfb6: primary_network_meter_heat_power_kw first: 347.33 kW (2018-11-20 09:15:00 to 2018-11-21 09:15:00)

Limits:
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-a4bcf4f332fc, F-60e0cfd3d785, F-2afa9fb125d4
  - Rationale: Customer reports no heat while secondary supply temperature tracks setpoint; need to verify actual room or radiator temperatures to confirm delivery failure.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-a4bcf4f332fc, F-2e7cbf1adfb6
  - Rationale: Primary meter shows heat power but this is network-side, not secondary circuit flow; measure secondary heating circuit flow to assess if water is circulating to rooms.
- C-controls: Review timestamped controller settings, alarms, and parameter changes with an engineer.
  - Selected supporting fact IDs: F-a4bcf4f332fc, F-adfaa143fad1, F-ec17bac45866, F-c292053f390c, F-7fbf261dc4b4
  - Rationale: Supply temperature tracks setpoint closely (mean gap 0.61°C, max 1.4°C); review timestamped controller settings, alarms, and parameter changes to rule out control issues affecting heat delivery.

### Response B

Observations:
- F-a4bcf4f332fc: Reported problem: no heat (2018-11-21 09:15:00)
- F-5443bc3ab0b7: Last measurement time: 2018-11-21 09:10:00 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-bc3c8bc8a41b: Measurement sample count: 144 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-2afa9fb125d4: secondary_heating_circuit_supply_temperature_c last: 58.3 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-ec17bac45866: secondary_heating_circuit_supply_setpoint_c last: 57.6 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-c292053f390c: Secondary supply/setpoint absolute gap max: 1.4 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-7fbf261dc4b4: Secondary supply/setpoint absolute gap mean: 0.61 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-e7602ff614f0: Secondary supply/setpoint absolute gap samples_within_2C: 144 (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-a66c97a34e9c: outdoor_temperature_c last: 9.3 °C (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-17954c67523c: primary_network_meter_flow_l_per_hour last: 4398.0 l/h (2018-11-20 09:15:00 to 2018-11-21 09:15:00)
- F-c642c57143fa: event_start: 2016-02-22 00:00:00
- F-64cbbe4fb0f0: type: activity

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.
- L-prior-not-current: A prior report does not establish the cause of this event.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-a4bcf4f332fc, F-2afa9fb125d4, F-ec17bac45866, F-c292053f390c
  - Rationale: Customer reports 'no heat' but secondary supply temp tracks setpoint within ~1.4°C max gap; verify actual room/radiator temperatures to confirm scope of heat loss.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-17954c67523c
  - Rationale: Only primary network-side flow is measured (F-17954c67523c); secondary/customer circuit flow is unavailable, so delivery to the building's heating loop is unconfirmed.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-c642c57143fa, F-64cbbe4fb0f0
  - Rationale: A prior 'activity' record from 2016-02-22 exists in the timeline; check maintenance logs for any completed work or parameter changes closer to decision_time.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

## Pair 7 — PreDist-M1-fault-5

### Response A

Response withheld by the common display contract.

### Response B

Observations:
- F-23b9c4141683: Reported problem: no heat (2018-11-23 08:30:00)
- F-67aa3176372c: Last measurement time: 2018-11-23 08:30:00 (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-383c12406330: Measurement sample count: 145 (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-c6c357ba15b1: secondary_heating_circuit_supply_temperature_c last: 48.0 °C (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-d865185ab874: secondary_heating_circuit_supply_setpoint_c last: 48.0 °C (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-3845078723cc: Secondary supply/setpoint absolute gap mean: 0.44 °C (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-43497bc25985: Secondary supply/setpoint absolute gap max: 2.4 °C (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-8ed165aa72d8: primary_network_meter_flow_l_per_hour last: 151.0 l/h (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-3930cf7e916a: primary_network_meter_heat_power_kw last: 8.0 kW (2018-11-22 08:30:00 to 2018-11-23 08:30:00)
- F-c507baa5efdb: event_start: 2018-07-02 10:49:00
- F-96639f831019: type: task
- F-2195fc4b35e4: problem: no DHW

Limits:
- L-no-room-evidence: Supply temperature tracking its setpoint does not establish heat delivery to rooms.
- L-primary-flow: Primary meter flow is not secondary/customer circuit flow.
- L-prior-not-current: A prior report does not establish the cause of this event.
- L-no-normal-range: No normal operating range is supplied for heat power or flow.

Suggested next checks:
- C-room-impact: Verify affected room or radiator temperatures and the scope of the reported heating loss.
  - Selected supporting fact IDs: F-c6c357ba15b1, F-d865185ab874, F-3845078723cc
  - Rationale: Secondary supply temp tracks its 48C setpoint closely through the window, yet 'no heat' was reported; need room/radiator readings to see if delivery matched supply.
- C-secondary-flow: Measure secondary heating circuit flow and compare it with the relevant design or operating range.
  - Selected supporting fact IDs: F-8ed165aa72d8
  - Rationale: Only primary network flow is available; secondary/customer circuit flow is unmeasured here and could reveal a blockage or valve issue despite normal supply temp.
- C-maintenance: Check maintenance records and actual completion evidence for relevant prior work.
  - Selected supporting fact IDs: F-c507baa5efdb, F-96639f831019
  - Rationale: A fault and follow-up task were logged in July 2018, months before this report; confirm whether that work was completed/closed or is linked to this recurrence.

Reviewer type: __________ (author review is not independent expert review)
Selection relevance: __________
Rationale support: __________
Check feasibility and priority: __________
Unnecessary checks: __________
Unsupported diagnoses or uncertainty concerns: __________

