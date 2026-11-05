# Traveler-first analytics

The demo now starts with practical historical questions: when did waiting become expensive, what did it cost when fares rose, and when did it save money? Individual histories, tables, weekday analysis, revisions, and methods are available in an expandable deep dive.

The opening lead-time cards retain the original equal-trip summaries over bins. The waiting tool introduces a separate, exact-lead comparison: select a route, a starting lead of 60/45/30/21/14/7 days, and wait 1/3/7 days. A trip is eligible only if both exact observations exist. Each trip contributes one pair. This removes repeated-observation weighting within that scenario, but does not make trips independent or eliminate calendar confounding.

Displayed metrics:

- Fraction of eligible trips with a higher/lower/unchanged later fare.
- Median additional cost **among increases**, and median saving **among decreases**. No conditional observations means unavailable, not zero.
- Median dollar change and median percentage change across all eligible trips, calculated separately; the two medians need not refer to the same trip.
- A table comparing starting leads, with an eligible-trip count for every row. Changing the lead or route may change the cohort.

These are retrospective two-price comparisons, not a validated adaptive strategy or future probability. The “latest safe day” answer remains: no dependable cutoff established. Every frozen history stops before departure; a missing endpoint is not evidence of no flights or no risk. No best booking date is selected from the table.

Example verified from the frozen data: across all routes, a 14-to-7-day comparison has 21 eligible trips. Twenty rose and one fell. Median additional cost among increases: $63; the single decrease saved $20. Median change across all 21: +$58. These differ from the 8–14-day-bin summary because that summary averages several eligible starting dates within each trip.

Verification: 72 combinations (four route selections × six starting leads × three horizons) reconciled between browser JavaScript and independent Python exact-lead lookups for eligibility, direction frequencies and median changes. Synthetic tests cover conditional medians, missing matches and no-increase cases. Original report and frozen data are unchanged; no API searches were used.
