# Data contracts (pipeline schema version 1)

The pilot uses JSON and SQLite to avoid dependencies before source feasibility is known. Convert validated analytical tables to Parquet when useful; never overwrite raw snapshots. Every query hash covers all nonsecret parameters, including filters, currency, locale, and departure date. Filter experiments are distinct queries but not additional independent trips.

## Request ledger: `data/ledger.sqlite`, table `attempts`

| Column | Meaning |
| --- | --- |
| `snapshot_id` | Unique attempt identifier, allocated before network I/O |
| `search_id` | SHA-256 prefix of canonical exact query parameters |
| `requested_at` | Reservation time, UTC ISO timestamp |
| `params_json` | Exact parameters excluding credentials |
| `outcome` | `reserved`, `success`, or `failed_or_unknown` |
| `http_status` | Status code, 0 for transport/non-JSON failure, null before completion |
| `raw_path` | Relative snapshot path, null if interrupted before save |

Every row consumes one collection slot. Reservations survive crashes. No monthly reset: expansion must be an intentional code/configuration change after review. Account checks are not search attempts and do not consume provider search credits. This ledger does not track other account clients.

## Raw snapshot: `data/raw/<snapshot_id>.json`

Envelope fields: schema version, provider, snapshot/search IDs, experiment role, exact parameters, request start/retrieval timestamps, outcome, HTTP status, a limited account-quota summary, and response JSON. Secrets are redacted recursively, including their occurrences in strings/URLs. Account identity, email, and full account response are not stored. Raw means provider JSON with security redaction plus provenance, not byte-for-byte HTTP capture. Non-JSON/transport failures retain a diagnostic category rather than a fabricated flight response. Provider search metadata remains in the response where supplied; the provider schema version is not assumed.

## Normalized observations: `data/normalized/observations.json`

One row per parseable timestamp/price pair per snapshot, including duplicates. Fields include search/snapshot IDs, retrieval time, experiment role, trip ID (airport pair plus date), origin/destination, departure date, requested currency, original historical timestamp, decoded UTC timestamp, UTC observation date, Baltimore observation date and timezone convention, price (null if invalid), lead days, both weekdays, quality flags, and structural eligibility.

Unparseable pairs/timestamps are counted as issues in the per-snapshot audit and remain in raw JSON. Missing/invalid/nonpositive prices do not become zero. Currency is **requested** currency, not an independent historical currency certification. Returned parameter discrepancies quarantine rows. Current price level, typical range, and flight details are never copied into historical observations.

Unix seconds are a provisional interpretation. Lead days = departure's calendar date minus the historical observation's Baltimore calendar date. Preserve UTC dates to evaluate timezone sensitivity before weekday analysis. Daylight saving means calendar-day horizons need not equal fixed elapsed hours.

## Analytical selection: `data/processed/daily.json`

For the descriptive audit, take the latest successful snapshot for each exact query. This does not patch a new missing history with an old one. Keep only baseline-role rows for the main daily table; filter experiments stay available in normalized data and audit summaries.

Within one snapshot, identical repeated values on a date collapse to the latest timestamp. Conflicting prices on the same timestamp or calendar date are excluded from daily calculations; they are retained in normalized/raw data. Invalid prices, future timestamps relative to retrieval, observations after departure, and returned-parameter mismatches are excluded. Large jumps are reported for review and remain eligible. No interpolation.

## Horizon pairs: `data/processed/changes.json`

Same query and snapshot, exact calendar date + 1, 3, or 7 days. Both endpoints must exist and be eligible. Fields include origin/destination, trip/search/snapshot IDs, observation and label dates, start lead time/price, future price, horizon, dollar change, percentage change relative to the starting price, and direction (up/down/unchanged). These are retrospective audit labels, not automatically leakage-safe training data.

## Audit: `data/processed/feasibility.json`

Contains snapshot/query/independent-trip counts, usable baseline days, exact-horizon counts, per-snapshot coverage, missing calendar days, flags and schema issues, current-only price insights, minimum observed prices and all tied dates/lead times, large jumps, matching filter comparisons, and overlapping historical price revisions. The revision list detects price differences; inspect raw histories separately for added/removed timestamps. Zero snapshots yields `NO_DATA`. No audit result automatically authorizes modeling or publication.

## Main-study exports

`python3 -m flights.collection_report` builds `study-coverage.json`, `study-summary.json`, `study-daily.json`, and `study-changes.json` using only the frozen `config/study.json` query hashes. Raw roles are preserved; explicit manifest membership admits the previously collected minimal ATL diagnostic without fabricating another observation. Contrasts, round trips, noncanonical pilot queries, and the transport-only fresh repeat remain outside study exports. A return date is now part of round-trip normalized trip identity.

Coverage separates pending/failed queries from successful searches without usable history. It includes predeclared holiday labels, history bounds, missing calendar days, structural flags, current-flight economy/nonstop checks, and exact-horizon denominators. Current flight checks do not establish historical itinerary or fare conditions. All exports remain local and ignored.

The authorized project lifetime cap is now 200 attempts; collection also stops when account monthly quota reaches the protected reserve of 40. These protections share one checkout ledger, not external API clients. A run can submit up to 180 attempts, still limited by the lifetime cap and account checks.
