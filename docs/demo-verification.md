# Demo verification — November 5, 2026

## Traveler-first revision

The opening now presents takeaways, fixed-lead waiting comparisons, and a timing comparison table. Detailed trip histories and methodology are collapsed until requested. See `docs/traveler-analytics.md` for metric definitions. Updated automated totals: 31 Python tests and six Node tests; all 72 route/lead/horizon combinations are reconciled with independent Python calculations. The new bundle is approximately 311 KB. Original checks below describe the first build.

## Automated evidence

- 30 Python tests passed, including actual-data export with credentials removed and socket creation blocked; the exporter performs no network operations and does not load `.env`.
- Four Node tests passed: exact calendar horizons across DST, no next-available substitution, equal trip weighting with unequal history lengths, gaps/missing histories, duplicate rejection, and unchanged outcomes.
- The browser calculation module was reconciled against all three saved Python horizon summaries for counts, rise frequencies, and mean dollar/percentage changes.
- Export preserves all 168 planned selections, including the one missing MCO December 21 history; 167 histories contain 10,282 observations.
- Exported trip fields are allowlisted. Credential, account, provider metadata and booking-token keys are absent. Only generated static artifacts are served; raw responses and private configuration are outside the serving root.
- Frozen input and referenced raw-response hashes verify unchanged. The same-trip sensitivity uses this freeze and retains extreme prices.

## Browser checks

The local in-app browser successfully loaded the real-data build at approximately 810 × 930 pixels. Visual review confirmed the explorer, readable chart, controls, data counts, and caveats. Screenshot: local `artifacts/demo-preview.png`.

Exercised ATL, MCO and DEN route choices; departure changes; the missing MCO December 21 selection; seven-day outcome reveal; a last-observation selection with no exact future observation; and switching the summary to three days. The three-day summary showed 9,781 pairs and +4.6% mean change, matching Python. The ATL November 6 example revealed October 23 → October 30, $104 → $139, +$35 (+33.7%). Browser console inspection found no warnings or errors in the final build.

Phone-width layout is implemented with CSS breakpoints but was not tested on a physical phone or dedicated device emulator. No public deployment was performed. Browser operation uses one same-origin saved JSON request; the CSP limits connections to the local origin and no third-party code/assets are loaded.

## Reproduction

See `docs/demo-and-deployment.md`. Node is a development-check dependency only; running the exported demo requires Python's standard library and a browser. `artifacts/demo/build.json` records current build sizes and file hashes. The complete bundle is approximately 300 KB. No additional flight searches, API spending, account changes, or external publication occurred during this work.
