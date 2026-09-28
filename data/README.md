# PreDist public-data replay

`replay-52.json` is an attributed slice of [PreDist v2](https://zenodo.org/records/19496480), DOI [10.5281/zenodo.19496480](https://doi.org/10.5281/zenodo.19496480), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data were published by Fraunhofer IEE and enercity Netz GmbH. The original dataset authors should be credited in any presentation or redistribution.

The case replays manufacturer 1, substation 21 at the 2016-12-12 15:55 report of “no heat.” The agent input contains the current problem category, the preceding 24 hours of measurements, and earlier published incidents and disturbances. The same report's later diagnosis, remedy, and fault label are stored in `evaluation/held-out-52.json` for retrospective comparison and must never enter the agent prompt or tool output.

This is a district-heating substation, not an electricity generating station. Sensor readings and published incident fields retain their original provenance. The team has not asserted that the published remedy would have been available to an engineer at the report time.
