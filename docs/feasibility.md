# Feasibility report — October 30, 2026

## Current status after authorized main collection

The main sample is now collected: **167 usable histories from 168 trips, 10,282 daily observations, $0 spent, 64 free searches remaining.** See [the final collection report](collection-report.md) for validation evidence, counts, exceptions, and limits. This supports descriptive analysis of the sampled provider histories. Historical fare semantics, longer-term revisions, and publication permissions remain provisional. Earlier stages below are retained as chronological research records.

## Latest result: authorized extension succeeded

**We now have one structurally usable, browser-matched one-way trip history.** On the user's approval, the lifetime cap was extended from 10 to 13 requests. All three added diagnostics succeeded and returned 62-point histories.

| Request | Definition | History | Interpretation |
| --- | --- | --- | --- |
| 11 | Minimal one-way BWI–ATL, November 6 | 62 daily points, August 30–October 30 | One independent trip |
| 12 | Same query with `no_cache=true` | Identical 62 timestamp/price pairs | Repeat of the same trip, not new independent data |
| 13 | Round-trip BWI–ATL, November 6–13 | 62 points | Diagnostic control, excluded from one-way study |

All 62 one-way date/price pairs match the saved browser accessibility labels using the browser evidence date of October 30 and the provisional Baltimore calendar convention. Timestamps occur at 04:00 UTC in this sample. No within-series duplicate dates, missing days, invalid prices, or returned-parameter mismatches were found. Exact calendar-horizon matching yields 61 one-day, 59 three-day, and 55 seven-day pairs for this single trip. These are correlated within-trip pairs, not independent training examples. The series ends seven days before departure and is incomplete through departure.

The working request retained route/date, one-way type, one adult, economy, nonstop, USD and US/English. It omitted explicit zero children/infants/bags, basic-exclusion false, sorting, and deep-search settings. Basic inclusion and the omitted passenger counts follow provider defaults. Since several optional parameters were removed together and retrieval time changed, the precise cause of the earlier omissions is not isolated. This is not proof that any one parameter is broken.

Reproduce the offline verification with `python3 -m flights.verify_pilot`. Results are stored in `data/verification/extension-comparison.json`; all raw snapshots remain separate and ignored. The main baseline analytical tables remain empty because the successful series is explicitly labeled diagnostic, not silently promoted into the original sample. The audit now separately counts independent one-way trips with history and round-trip controls.

**Current decision:** API history acquisition is feasible for at least one tested trip. Validate coverage on additional routes and historical filter meaning before broad collection. One same-session repeat does not establish long-term revision stability. The precise cheapest-offer universe, historical tax/fare conditions, timezone semantics outside this sample, and publication permissions remain unresolved. No model or population-level findings are justified yet.

Total searches: 13 successful; cap reached. Additional paid cost: $0. All 21 offline tests pass. The original failure report below is retained as the record of the first ten attempts and is superseded by this update. No support inquiry was sent.

## Original ten-request outcome (superseded by extension)

**Decision: do not expand collection. Ten successful API searches returned current flight options but no historical series. The proposed historical analysis is not currently feasible through these tested API settings.**

## Actual collection results

| Measure | Observed result |
| --- | --- |
| Authenticated search attempts | 10, all successful, no search retries |
| Independent baseline route/departure combinations queried | 6 |
| Filter experiments | 2 on the same ATL trip; not independent trips |
| Search-mode diagnostics | 2 on the same ATL trip; not independent trips |
| Responses containing `price_insights` | 0 of 10 |
| API histories / historical observations obtained | 0 / 0 |
| Usable 1-, 3-, and 7-day change pairs | 0 for every horizon |
| Free plan verification | Account API reported Free Plan, monthly price $0 |
| Spending | $0; no plan/settings changes |
| Local request budget remaining | 0 of 10; collection stopped |

Baseline queries covered BWI–ATL, BWI–MCO, and BWI–DEN, each departing November 6 or December 1, 2026. All six returned between 7 and 15 current itinerary options. The absence of history is not evidence of no flights or sold-out travel.

The two original contrasts changed nonstop to any stops, then included to excluded basic economy, for ATL November 6. They also returned current flights without history. Historical filter comparisons therefore have **zero overlapping observations**, not evidence that the histories are identical.

Request 9 changed only the ATL baseline sort setting to the documented default (`sort_by=1`). Request 10 then changed `deep_search` to false. Both succeeded but omitted insights. Exact parameters, sanitized provider responses, retrieval times, and a durable ledger are saved locally. The diagnostics did not change the intended fare constraints. No later-day refresh was performed because both reserve requests were used for debugging.

The account endpoint initially reported 250 monthly searches left and reported 241 immediately before the last search. A final post-search balance was not requested; do not present 241 as the final balance. Account throughput reported 250/hour, whereas the public pricing page reviewed earlier advertised 50/hour; the collector uses verified account capacity. Ledger attempts, provider billing counts, and possibly delayed account counters are distinct.

## Browser verification

Three matching Google Flights URLs were inspected using visible UI, with one-way, one passenger, economy including basic, nonstop, airports, date, and USD settings checked. Local accessibility captures are under `data/verification/`; these are evidence only, not a substitute research dataset.

| Trip | Browser observation | API comparison |
| --- | --- | --- |
| BWI–ATL, November 6 | Expanded “Price history for this search”; 62 accessible points from 61 days ago through today | API omitted history under all three tested search-mode combinations |
| BWI–MCO, November 6 | Expanded price insights showed current/typical price information; no historical chart appeared in the inspected panel | API omitted all price insights |
| BWI–DEN, December 1 | Expanded “Price history for this search”; 62 accessible points | API omitted history |

We can confirm that two sampled browser pages expose historical charts while corresponding API responses omit them. We cannot perform point-by-point API/browser agreement testing because the API returned no points. No conclusion is established about why extraction omitted the field. Search mode diagnostics did not resolve it. Browser history could reflect a narrower set of offers than the absolute cheapest visible booking option; that universe remains unverified.

## Supported and unsupported claims

Confirmed: authentication works; current flight results are available for all six baseline trips; the tested API requests did not supply historical series; browser histories exist for at least two of the inspected trips; no money was spent.

Unresolved: whether history is accessible consistently via this provider; minimum-fare definition; historical filter/passenger/tax consistency; timezone semantics; revisions; publication and redistribution permission. Current browser tax/fee wording does not establish historical comparability. Neither the API omissions nor a small browser sample justify a general conclusion about all routes or one-way searches.

No price-change frequencies, weekday effects, buying strategies, forecasts, or model performance are reported. Browser verification points remain separate from normalized API observations. We have not silently switched to browser scraping as a collection source.

## Recommended next step

A [documentation recheck](documentation-recheck.md) found no missing documented history activation parameter. It also records remaining untested diagnostics and the distinction between sorting by price and the separate Cheapest tab. No additional API searches were used for that review.

Seek provider clarification about the reproducible missing-history discrepancy and historical semantics/permissions before spending more search credits. A ready-to-send draft is in `docs/provider-inquiry.md`; it has **not** been sent. Provider search IDs and full reproduction parameters are available in local raw snapshots if support requests them, without sharing an API key.

If the provider cannot supply suitable histories, the closest defensible alternative is a prospective study of current minimum quotes for a small fixed set of trips. For example, four trips observed daily for 28 days require 112 searches before retries. This takes four weeks, gives only four independent histories, and supports a small descriptive study rather than credible broad modeling. Current-quote completeness and publication rights would still need validation. This is a material scope change requiring the user's decision, not an authorized fallback collection.

A licensed historical dataset is another option, but none has yet been identified or validated. Do not purchase data or activate paid services. The published Starter price reviewed previously was $25/month, already above the project's total budget.

## Software verification and provenance

The Python installation initially failed TLS certificate validation before any searches were sent. Using the macOS system CA bundle fixed connectivity without disabling verification; the collector now supports that fallback when its default CA file is absent. The empty secret template was restored after setup; credentials remain only in ignored local configuration.

The audit distinguishes six attempted baseline trips from zero usable historical trips. Twenty offline tests pass, covering budget/concurrency/caching, safe diagnostic modes, missing-history processing, exact horizons, timestamps, and snapshot behavior. These tests are synthetic and excluded from research counts.

Sources reviewed during this project: [API documentation](https://serpapi.com/google-flights-api), [history schema](https://serpapi.com/google-flights-price-insights), [pricing](https://serpapi.com/pricing), [account API](https://serpapi.com/account-api), and [legal terms](https://serpapi.com/legal). Terms dated August 27, 2026 do not resolve public redistribution permission for this project; keep all data and browser evidence local pending clarification. No provider contact has been made.
