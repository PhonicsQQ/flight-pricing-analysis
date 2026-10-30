# Sampling plan

## Pilot: frozen October 30, 2026

Candidates are probes, not confirmed coverage or a representative sample. Retain failures and empty histories in the coverage report. Do not silently substitute routes after seeing prices.

| Queries | Origin/destination | Departure | Role |
| --- | --- | --- | --- |
| 1–2 | BWI–ATL | November 6 and December 1, 2026 | Baseline, 7/32-day lead at anchor |
| 3–4 | BWI–MCO | November 6 and December 1, 2026 | Baseline |
| 5–6 | BWI–DEN | November 6 and December 1, 2026 | Baseline |
| 7 | BWI–ATL | November 6 | Any stops vs baseline nonstop |
| 8 | BWI–ATL | November 6 | Exclude basic vs baseline include basic |
| 9 | Same successful baseline query | Same original departure | Reserve for refresh after ≥24 hours |
| 10 | Selected query if needed | Logged explicitly | Debugging/verification reserve |

Retries consume reserves; the collector will not exceed 10 attempts to complete the table. The initial run limit of eight includes retries, so some planned queries may remain unexecuted. Run the offline audit after collection before deciding how to use remaining slots. The plan samples only two departure weekdays; it cannot support weekday inference by itself.

November/December dates are subject to seasonal and holiday travel patterns. Before expansion, predeclare a holiday calendar and surrounding-window indicators (not just holiday dates), including Thanksgiving-period effects. Do not interpret a December 1 fare pattern as a pure weekday effect. Near-term and farther-out histories have different right-censoring: a future departure's observed minimum is only a partial-window minimum.

## Conditional expansion, not yet authorized to execute

After the pilot establishes coverage/meaning, a possible design is 6 covered destinations × 28 consecutive departure dates = 168 baseline route/date searches, across four weeks and all weekdays. This depends on finding six suitable covered routes; otherwise revise the design explicitly instead of assuming they exist. Freeze route criteria, departure dates, holiday strata, and exclusions before examining outcome patterns. Use a deterministic balanced design, never call it random.

With 250 free searches available and no other account usage, 10 pilot attempts + 168 expansion attempts + 20 refresh/debug attempts = 198, leaving 52 credits unallocated. Actual remaining account quota governs; retries, other usage, and billing-cycle boundaries may reduce scope. The current code cannot execute this expansion; its lifetime cap remains 10.

Choose departure dates so lead-time coverage includes near and far trips and multiple weeks where possible. Report every trip's available interval and remaining days to departure. Distinguish 168 trips from the potentially thousands of correlated observations within them. Keep overlapping filter/snapshot variants together when counting independent histories or evaluating models.

## Actual pilot outcome, October 30, 2026

All eight initial searches succeeded but omitted `price_insights`. The two reserved slots were used for targeted diagnostics on BWI–ATL November 6: request 9 changed only `sort_by` from 2 to 1; request 10 retained sort 1 and changed `deep_search` to false. Both also omitted insights/history. The exact diagnostic manifests are saved under `config/`. No refresh slot remains, so temporal revisions were not tested. The lifetime cap is exhausted; do not reset the ledger.

## User-authorized extension to 13 attempts

Requests 11–13 were explicitly approved after documentation review: a minimal ATL one-way query, the same with `no_cache=true`, and a November 6–13 round-trip control. All three returned 62 points. The one-way snapshots represent only one trip and match the saved browser chart. The round trip remains outside the study. The cap is now 13 and exhausted; see the latest feasibility report for remaining gates.

## Authorized main collection, frozen October 30, 2026

Validation returned histories for all six minimal route/date queries. Stop/basic contrasts changed historical prices; full historical fare semantics remain provisional. Adding `bags=0` to the minimal ATL request again omitted insights, so the main collection omits it. Two saved browser charts (ATL and DEN) have matching ordered prices. No redistribution permission is implied.

Freeze `config/study.json`: ATL, MCO, DEN from BWI, each departing on every date October 31–December 25 inclusive (56 dates, 8 per weekday, 168 trips). Route selection is based on observed history availability, not low fares. This is a convenience sample of three BWI routes. Dates cover lead times 1–56 days at collection, and include holiday travel. Predeclared holiday windows are Veterans Day ±3 days, Thanksgiving ±7, Christmas ±7. Windows are research labels, not causal adjustment guarantees. Flight histories are right-censored at retrieval, and calendar/lead time are linked in this single collection wave.

Reuse exact-query cache, including original minimal ATL data via explicit manifest membership; preserve raw diagnostic roles. With 24 completed requests and six cached main-study queries, expect 162 new requests, totaling 186 attempts before retries. Lifetime cap 200 and account quota floor 40 protect verification capacity; both count conservatively. Stop on failed/unknown requests or quota limits. Later-day refresh is reserved but cannot be performed during this same-day run.

## Main collection completed

All 168 frozen queries succeeded; 167 returned usable histories. Orlando December 21 is retained as a successful query without history. One transport timeout was retried successfully. Actual project attempts: 187; verified provider free quota remaining: 64; spending: $0. Later-day refresh remains reserved, not performed. See `docs/collection-report.md`.
