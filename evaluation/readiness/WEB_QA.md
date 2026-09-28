# Web review log

2026-09-28. Local preview used `python3 -m http.server 8765 --directory web` and the Codex in-app browser.

## Visual checks completed before the final text and architecture edits

- Desktop default viewport (1280 × 720): landing hero, navigation, System 2 introduction, incident, check list, fact inspector, and tool timeline were visually reviewed. The key content was legible without clipping in the inspected views.
- Mobile viewport (390 × 844): landing hero and System 2 introduction with the case selector and status panel were visually reviewed. Their inspected views had no horizontal overflow or clipped controls.
- The temporary viewport override was reset after review. Browser screenshots were displayed inline during review; no screenshot file was saved, so this log does not claim a permanent image artifact.

## Interaction and content checks

- On the System 2 page, switching from case 29 to case 52 updated the URL to `?case=52`, the displayed incident date and status, the tool list, cited facts, and the budget-handoff warning. Accessibility output showed four cited facts and six tool calls for the selected case-52 check.
- The default case 29 displayed its three checks, seven calls including `finish_investigation`, three cited facts for the first selected check, and the original source fields and values.
- After the later text and architecture edits, `node --check web/system2.js` passed. The export script generated both JSON assets, and static checks confirmed that all selected observation and check fact IDs exist in their respective exports, all local landing/demo links resolve to files, and every JavaScript target ID exists in the demo HTML. No further browser visual review was performed after those edits.

These are UI and static-asset checks, not a domain correctness or security assessment.

## Later source figure and copy revision

- The landing hero was narrowed to the 2019-01-09 14:10 paired sample: 63.9°C measured supply and 63.8°C setpoint. It does not describe the entire 24-hour window as tracking. The values match the last row of `data/holdout-29.json`.
- `web/assets/system2-case29-trend.png` was generated from all 144 time-ordered paired measurements in that public case. The 1600 × 650 PNG was visually inspected as a standalone image; both series, axes, timestamps, and the last pair were legible. It is labelled as a redraw, not an original SCADA capture.
- After these edits, Ruff formatting/lint, JavaScript syntax, local HTML asset-link existence, and exported fact-reference checks passed. The revised landing layout was not rechecked in a browser.
