# Public data anchors and provenance

Reviewed 2026-09-28 KST. Dataset metadata and licenses below come from the publishers' own pages unless otherwise stated. PreDist v2 replay 52 has been ingested and executed; additional same-asset cases are being evaluated. The original candidate table below records selection-time findings, not current completion status.

## Catchphrase

**에너지 설비의 알람을, 근거 있는 다음 점검으로.**

English: **From energy-asset alarms to evidence-backed next checks.**

This promises a reviewable investigation step, not automatic plant control or a proven root cause. If the submitted demo uses only wind turbines, name that asset type in the subtitle: “공개 풍력 설비 데이터로 검증한 조사 에이전트.”

## Candidates

| Source | Public evidence that can be joined | License / accessibility | Fit and limit |
| --- | --- | --- | --- |
| [EDP Wind Farm 1](https://edp.com/en/innovation/data) | Turbine SCADA, operation/alarm logs, confirmed failure logbook for the same wind farm. The [IEA Wind inventory](https://iea-wind.org/wp-content/uploads/2024/07/EDP-OpenData-Details.pdf) describes 23 failure records, 256,231 operation-log rows, and 10-minute signals over the training period. | Individual EDP pages state [CC BY-SA 4.0](https://edp.com/en/innovation/data/wind-farm-1-record-failure-history-2016). A [2017 failure XLSX](https://edp.com/sites/default/files/document/2025-04/opendata-wind-failures-2017.xlsx) responds successfully; some current SCADA/log download links redirect to inaccessible pages, so the entire set is **not yet access-verified**. | Best match to an electricity-generation investigation if all three sources can be fetched and joined. Confirm turbine IDs, timestamps, and an episode before choosing it. Attribute EDP and observe ShareAlike when redistributing adapted data. |
| [PreDist v2](https://zenodo.org/records/19496480) | Measurements from 93 district-heating substations, incident fault reports, disturbances, corrective/preventive maintenance activities, normal-event examples. | Open Zenodo archive, 266.8 MB. The [Zenodo record API](https://zenodo.org/api/records/19496480) identifies the license as CC BY 4.0. | Strongest fallback for a multi-source *energy equipment* case. It is district heating, not an electric generating station; describe it accurately. |
| [MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt%203%20dataset) | Real compressor pressure, oil temperature, motor current, and valve signals with published failure and maintenance intervals. | UCI explicitly states CC BY 4.0; 208.3 MB download. | Operationally easy fallback, but the equipment is a metro-train compressor rather than an energy asset. Use only if the energy sources fail the access/quality gate and adjust the catchphrase. |
| [EDP thermal boiler units](https://edp.com/en/innovation/data/boiler-unit-y-year-xxx4) | Real thermal-generation process readings at 1-minute frequency. | EDP states CC BY-SA 4.0; data are anonymized by year. | Domain fit is excellent, but no linked failure/maintenance ground truth was verified. Use for background or a separate signal demo, not to invent incident labels. |
| [Hill of Towie wind farm](https://zenodo.org/records/22662930) | 10-minute SCADA and alarm logs, descriptions, turbine metadata, and shutdown-duration data. | Publisher states CC BY 4.0. Annual archives are about 1.4–1.6 GB each. | Provenance is clear but large for today's deadline; alarm logs alone do not certify a root cause. Secondary fallback. |

## Recommended decision gate

**Try EDP first for 45 minutes.** Obtain one time-aligned SCADA slice, operation-log slice, and confirmed failure row for the same turbine. Check the exact license and file URLs. If the signals/logs remain inaccessible or mismatched, use PreDist and pitch the first demo as energy-equipment investigation rather than power-plant fault diagnosis. MetroPT-3 is a final fallback with a change of asset label. Avoid joining records from different plants as if they describe one incident.

The [Mendeley metadata description of EDP](https://data.mendeley.com/datasets/zjxjnjp3xs/1) reports eight files with SCADA, event logs, and failure logs. This is useful for field inventory, but it is not proof that those files can be downloaded from the current EDP portal. The original EDP license governs original EDP data even when a secondary index uses a different metadata license.

## Replay protocol

1. Select a real public equipment episode and record source URL, dataset version, license, turbine/substation ID, and timestamp.
2. Set a decision time **before** the confirmed failure or later maintenance report. Give the agent only records that existed by then. Keep later reports as held-out evaluation evidence.
3. Keep source labels visible: `observed telemetry`, `published operation log`, `published later outcome`, and `team-authored scenario wrapper`.
4. Use a short, clearly authored operator question only to start the replay; do not present it as an actual historical ticket.
5. Score source citation, relevant tool calls, conflict detection, useful next check, and justified abstention. A later failure label can assess component-family prioritization, but it does not prove the proposed inspection would have worked in the real plant.

No private employer/customer record is a seed, prompt, retrieval source, or evaluation target. Public source data used through NVIDIA's hosted endpoint must be attributed and checked against the endpoint's trial terms. Store only a small attributed replay slice in the demo repository if its license permits it; otherwise provide an acquisition script and hashes.
