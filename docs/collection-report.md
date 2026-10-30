# Collection report — October 30, 2026

**Main collection complete: 168 planned trip searches, 167 usable histories, 10,282 daily observations. Spending: $0. Verified remaining monthly free quota: 64 searches at 12:51 PM America/New_York.**

## Coverage

| Route | Planned/collected trips | Usable histories | Daily observations |
| --- | ---: | ---: | ---: |
| BWI–ATL | 56 | 56 | 3,444 |
| BWI–MCO | 56 | 55 | 3,381 |
| BWI–DEN | 56 | 56 | 3,457 |
| Total | 168 | 167 | 10,282 |

Departures span October 31–December 25, 2026, with eight of each weekday per route in the planned sample. This is a balanced convenience sample of three empirically covered BWI routes, not a random or representative sample of air travel. The one unavailable history is BWI–MCO departing December 21; its successful response contained 12 current options. It is not classified as sold out and was not silently replaced.

The study contains 95 histories of 62 days and 72 of 61 days. No internal calendar gaps, invalid/nonpositive prices, conflicting daily duplicates, or returned-parameter mismatches were detected in usable study histories. All are incomplete through departure. There are 183 adjacent changes exceeding a twofold increase or falling below half the prior price; they are retained and flagged for inspection, not treated as errors automatically.

Exact calendar-date joins provide 10,115 one-day, 9,781 three-day, and 9,113 seven-day pairs. These are correlated observations from 167 trip histories, not that many independent trips. No probabilities, confidence intervals, model performance, or buying-strategy claims have been estimated yet.

## Validation findings

All six minimal validation route/date searches returned histories. Comparing nonstop against any-stops changed 16/61 overlapping ATL historical prices, 18/61 MCO prices, and 62/62 DEN prices. Excluding basic economy changed 62/62 ATL prices and 56/62 DEN prices. These experiments support filter sensitivity in the sampled histories; they do not prove exact historical fare inclusion rules universally.

Adding `bags=0` to the working minimal ATL query alone again omitted insights. The study omits that optional parameter and follows the documented default, while retaining explicit one-adult, economy, nonstop, currency, locale, route and departure constraints. This is an empirical parameter sensitivity, not a confirmed provider root-cause diagnosis.

Two saved browser histories were checked: ATL November 6 matched all 62 date/price pairs using the provisional Baltimore date convention; DEN December 1 matched all 62 ordered prices. A same-session fresh ATL fetch was identical. Later-day revisions remain untested. Current returned options all passed the single-segment/economy checks; for all 167 histories, current `lowest_price` matched both the minimum returned option and the final historical point. Current consistency does not prove historical tax/fare comparability or coverage of every possible offer.

## Budget and provenance

The project ledger contains 187 attempts: 186 successful responses and one transport timeout, followed by one successful retry of that query. These totals include feasibility experiments and controls, which are excluded from the 168-trip main sample. The provider account reported 64 monthly searches remaining after completion. Local attempts and provider credit consumption differ; all attempts count conservatively toward the 200-attempt project cap. The collector additionally stops at a 40-search provider quota reserve. No paid services, overages, or plan changes were activated.

The manifest was frozen before expanded outcomes were inspected. Exact-query cache reuse admits the original minimal ATL diagnostic by explicit manifest membership without altering its raw provenance. Raw snapshots, request outcomes, normalized rows, and analytical exports are preserved separately. Credentials and all collected/derived data remain ignored by Git; the secret scan passed. Public redistribution/display permission is still unresolved.

## Reproduction and next work

Run `python3 -m flights.process` and `python3 -m flights.collection_report` offline from the repository root. The frozen sample is `config/study.json`. Private outputs are `data/processed/study-coverage.json`, `study-summary.json`, `study-daily.json`, and `study-changes.json`. Account evidence is `data/account/latest.json`. Twenty-three offline tests pass, including budget persistence, concurrent-run exclusion, protected quota floor, manifest constraints, duplicate handling, missing-history handling, and exact horizon joins.

Proceed to descriptive charts and trip-aware change summaries using the saved dataset. Inspect large jumps and compare observation-date conventions before weekday conclusions. Mark Thanksgiving, Christmas and Veterans Day windows using the predeclared labels. Calendar effects and lead time are linked in this single collection wave. A later-day refresh of a few fixed queries is needed to assess revisions; reserve requests rather than pretending a same-day repeat answers that question. Do not schedule or execute a future refresh until the later date. Modeling remains gated on a defensible chronological evaluation design. Public demo exports remain gated on permissions.
