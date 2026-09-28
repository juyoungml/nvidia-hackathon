# PreDist public-data replay

`replay-52.json` is an attributed slice of [PreDist v2](https://zenodo.org/records/19496480), DOI [10.5281/zenodo.19496480](https://doi.org/10.5281/zenodo.19496480), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data were published by Fraunhofer IEE and enercity Netz GmbH. The original dataset authors should be credited in any presentation or redistribution.

The published incident replays use manufacturer 1, substation 21, at the report times for faults 52 (2016-12-12), 62 (2019-01-21), and 32 (2019-10-19). Each agent input contains only the current problem category, the preceding 24 hours of measurements, and records dated earlier than the decision time. The same report's later diagnosis, remedy, and fault label live only in the matching `evaluation/held-out-<id>.json` file and must never enter the agent prompt or tool output. Each replay records SHA-256 hashes for the four public source CSVs and its selection rule.

`derived-no-report-20161210.json` samples a public measurement window without supplying an incident report. It is a gate probe, not a verified normal case; no listed report does not prove normal operation. `derived-missing-measurements-52.json` artificially removes the measurements from fault 52 to test abstention. It is not a published missing-data incident. Neither derived probe has a new held-out outcome.

Rebuild the published incidents from the licensed public CSVs with `uv run python scripts/build_replay.py --source-dir <directory> --report-id 52` (also 62 and 32). Rebuild the derived probes with `uv run python evaluation/build_derived.py --source-dir <directory>`. The cached source path is local preparation data and is not included in this repository.

Earlier published reports have dates before the replay decision time, but PreDist does not establish exactly when their retrospective narratives became available to an operator. Treat them as historical context under that assumption, not guaranteed real-time records.

This is a district-heating substation, not an electricity generating station. Sensor readings and published incident fields retain their original provenance. The team has not asserted that the published remedy would have been available to an engineer at the report time.
