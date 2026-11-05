# First descriptive analysis

Implemented in `flights/analyze.py`; run with the locked analysis environment. Local report: `artifacts/analysis-v1/report.md`. Five PNG/SVG figures, CSV summaries, flagged jumps, observed minima, and numerical results are generated from the checksum-verified October 30 freeze. No network or credentials are used.

The unit of weighting is a route/departure history. Each summary averages observations within each eligible history, then gives histories equal weight. Pooled distribution summaries are explicitly labeled observation-weighted. Exact 1/3/7-day labels require a genuine price on the matching calendar date; no interpolation is used. There are no eligible seven-day pairs starting 1–7 days before departure in this snapshot.

Uncertainty resamples whole histories within route (2,000 draws, fixed seed), retaining within-history dependence. A departure-week block sensitivity uses eight blocks across routes. These do not fully account for shared observation-date shocks or establish population representativeness. Weekday standardization uses common route/lead cells with at least three distinct trips for each weekday; it does not remove calendar confounding.

All large jumps are retained. The optional sensitivity that excludes affected histories changes the population and is not a correction of presumed errors. Minima include tied dates and describe only the available window. Current search metadata is not used as historical features.

## Revision checks completed November 5

All three refreshes succeeded on November 5 using three free searches (61 account searches remaining; 190 lifetime project attempts). Each history still contains 62 observations, with six added dates and six oldest dates removed. Of 56 overlapping timestamps per trip, ATL had no revised prices; MCO had one (October 29: $123 → $94), and DEN had one (October 30: $168 → $134). The cause is unknown. This directly demonstrates that historical prices can be revised; any predictive evaluation must preserve what was available at each retrieval. The frozen analysis is unchanged. Detailed local report: `artifacts/refresh-checks/report.md`; reproduce with `python3 -m flights.refresh_report`.

The original plan and commands below are retained for provenance, not an instruction to repeat these completed requests.

Three selected queries in `config/refresh-three.json` cover ATL November 6, MCO November 20, and DEN December 4. Their exact prior retrieval timestamps and eligibility are in local `data/verification/refresh-plan.json`. All are eligible by October 31 at 12:48 PM Eastern. No refresh or automation was executed when this analysis was prepared.

Use a dry run to obtain their IDs, then refresh each explicitly, with limit 1:

```sh
python3 -m flights.collect run --plan config/refresh-three.json
python3 -m flights.collect run --plan config/refresh-three.json --only SEARCH_ID --refresh --limit 1 --live
python3 -m flights.process
```

The account and ledger limits still apply. Compare overlapping historical timestamps in the processor revision audit before treating retrievals as stable. Keep the existing freeze unchanged. A three-query check can detect revisions but cannot prove universal stability.

## Next decision

Reserve genuinely future observations for evaluation before model selection. Do not present the explored historical sample as an untouched test set. A useful local demo can first explain these descriptive findings and coverage; predictions should wait for point-in-time validation and honest baseline comparisons. Public display and redistribution remain unresolved, so data-derived artifacts stay local.
