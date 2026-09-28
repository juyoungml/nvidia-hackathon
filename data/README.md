# PreDist public-data replay

`replay-52.json` is an attributed slice of [PreDist v2](https://zenodo.org/records/19496480), DOI [10.5281/zenodo.19496480](https://doi.org/10.5281/zenodo.19496480), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data were published by Fraunhofer IEE and enercity Netz GmbH. The original dataset authors should be credited in any presentation or redistribution.

The published incident replays use manufacturer 1, substation 21, at the report times for faults 52 (2016-12-12), 62 (2019-01-21), and 32 (2019-10-19). Each agent input contains only the current problem category, the preceding 24 hours of measurements, and records dated earlier than the decision time. The same report's later diagnosis, remedy, and fault label live only in the matching `evaluation/held-out-<id>.json` file and must never enter the agent prompt or tool output. Each replay records SHA-256 hashes for the four public source CSVs and its selection rule.

`derived-no-report-20161210.json` samples a public measurement window without supplying an incident report. It is a gate probe, not a verified normal case; no listed report does not prove normal operation. `derived-missing-measurements-52.json` artificially removes the measurements from fault 52 to test abstention. It is not a published missing-data incident. Neither derived probe has a new held-out outcome.

Rebuild the published incidents from the licensed public CSVs with `uv run python scripts/build_replay.py --source-dir <directory> --report-id 52` (also 62 and 32). Rebuild the derived probes with `uv run python evaluation/build_derived.py --source-dir <directory>`. The cached source path is local preparation data and is not included in this repository.

Earlier published reports have dates before the replay decision time, but PreDist does not establish exactly when their retrospective narratives became available to an operator. Treat them as historical context under that assumption, not guaranteed real-time records.

This is a district-heating substation, not an electricity generating station. Sensor readings and published incident fields retain their original provenance. The team has not asserted that the published remedy would have been available to an engineer at the report time.

## Cross-substation holdout

`holdout-60.json` and `holdout-63.json` are two additional public PreDist v2 manufacturer-1 cases, on substations 4 and 7 respectively. Their inputs contain the current problem category, 24 hours of measurements (144 samples each), and earlier dated records only. The same reports' retrospective descriptions and labels are kept separately in `evaluation/holdout-outcomes/` and must be excluded from every agent input and tool response.

The choice was fixed before model runs: scan reports chronologically for the first two “no heat” or “not enough heat” events outside substation 21, on distinct substations, with at least 100 samples in the preceding 24 hours and populated `s_hc1_supply_temperature`, its setpoint, and `p_hc1_return_temperature`. Reports 60 and 63 meet that rule. Their source file SHA-256 hashes and time cutoffs are recorded in each input. No other candidates were run to select favorable outcomes.

Rebuild with `python3 scripts/build_holdout_cases.py --source-dir .artifacts/public-source`. Extract manufacturer-1 `faults.csv`, `disturbances.csv`, `feature_descriptions.csv` (saved locally as `features.csv`), and operational `substation_4.csv` and `substation_7.csv` from the official [Zenodo archive](https://zenodo.org/api/records/19496480/files/predist_dataset.zip/content) into that ignored local source directory. `scripts/inspect_remote_zip.py` supports HTTP-range extraction. The published report date establishes the replay cutoff, but PreDist does not establish when older retrospective narratives became available to an operator.

Reports 60 and 63 were used in the first comparison pilot. For the next comparison, the selection was frozen before model runs by applying the same chronological rule while excluding substations 21, 4, and 7. The next two eligible reports on distinct substations are 3 (substation 12) and 13 (substation 24). `holdout-3.json` and `holdout-13.json` each contain 144 preceding measurements; their outcomes are isolated in `evaluation/holdout-outcomes/`. Extract manufacturer-1 operational `substation_12.csv` and `substation_24.csv` into the same ignored source directory, then rebuild with `python3 scripts/build_holdout_cases.py --source-dir .artifacts/public-source --batch next`. The original batch remains the default.

## Cycle 3 fresh cases

`holdout-37.json` (asset19, 144 measurements) and `holdout-5.json` (asset11, 145 measurements) were fixed before cycle3 inference by the same chronological eligibility rule excluding previously used assets21/4/7/12/24. The protocol, input/corpus hashes, and eligibility counts are in `evaluation/cycle3/manifest.json`. Their current outcomes remain separately under `evaluation/holdout-outcomes/`. They are narrow heating complaints, not proof of broader plant-domain coverage.
