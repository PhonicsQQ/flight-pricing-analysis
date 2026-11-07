# Phase two: a small prospective measurement pilot

Prepared 11-05-2026, before the future observations. Status: planned, not scheduled. No additional searches have run. Machine-readable protocol: `config/prospective-protocol.json`; requests: `config/prospective-queries.json`.

## Scope and budget

Follow BWI–ATL, BWI–MCO, and BWI–DEN departing **11-27-2026**. Collect each at **12:00–12:30 PM America/New_York** on **11-12-2026, 11-19-2026, and 11-26-2026**. These are 15, 8, and 1 days before departure. Use the first successful retrieval in the window; never choose a favorable later snapshot. Selection is by established coverage and calendar, not observed fare. This deliberately captures a Thanksgiving travel period and cannot represent normal-season travel.

Nine planned attempts plus one unallocated failure/debug reserve fit the ten remaining project attempts (190 used of 200). All collector safeguards remain: Free-plan verification, account reserve of 40, per-call limit one, durable ledger, lock, and no refresh within 24 hours. Other account usage or collection can reduce capacity; stop rather than increase the cap. The last verified account balance was 61 on 11-05-2026, not a promise of future availability. Spending stays $0.

## Measurement and evaluation

The target is the change in **current quoted lowest fare at the actual retrieval times**, using `price_insights.lowest_price` when valid and consistent with returned options and requested currency/filters. The provider's current minimum is not established as every possible airline fare. Save the full raw response and compare returned current flight minima; flag discrepancies and exclude ambiguous endpoints from the primary calculation. Missing/error responses are unavailable, never zero or sold out.

Do not use a later-returned historical value to replace what was observed at a checkpoint. Preserve timestamp, request parameters, outcome, snapshot ID, current fare, and quality status. Confirm matched query parameters and one adult/nonstop/economy current options at both endpoints. Report actual elapsed hours: the two calendar dates are seven days apart, but collection may differ by up to 30 minutes. This is distinct from the retrospective exact-calendar-date analysis.

The only prediction is **no change ($0)**, fixed before the pilot. No fitting, probabilities, or adaptive buying policy. The 11-12→11-19 interval checks the measurement pipeline. The **11-19→11-26 interval is reserved for final evaluation**, with the same predeclared baseline; do not tune it from the first outcome. Preserve the first baseline snapshot when it arrives. Report individual signed changes and zero-change absolute errors, the mean absolute error, and exclusions. No model-performance claim from three outcomes.

Both intervals reuse the same three trip groups. This is a future-period measurement test, **not** a group-held-out modeling test. Historical data for these trips has already been explored. A future modeling study would need additional unexamined trip groups and market periods under a separately agreed budget. This pilot does not automatically authorize that expansion.

## Execution

```sh
python3 -m flights.prospective
```

Dry run prints dates, window, and the three query IDs without loading credentials or making network calls. On each planned date, run once per ID:

```sh
python3 -m flights.prospective --live --only QUERY_ID
```

The wrapper rejects execution outside the planned date/time window before loading credentials. Each invocation permits one search; there is no automatic retry. If a window is missed, record it as missing. Do not backfill from historical series, shift dates silently, reset the ledger, or manufacture a forecast. Document amendments before subsequent collection, and distinguish amended runs from this protocol.

Nothing runs in the background. No reminder or automation has been created. The original October 30 analysis and its demo remain frozen; the prospective pilot gets separate artifacts and does not silently refresh the headline findings.
