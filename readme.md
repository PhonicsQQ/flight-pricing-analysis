# Flight prices as departure approaches

How does the lowest available economy fare for a fixed route and departure date change as departure approaches?

This portfolio project starts with data feasibility, then descriptive research, and only then considers forecasting and a small Streamlit demo. It studies a trip's cheapest qualifying option; the airline or flight supplying that price can change. It does not track a physical seat.

**Status: collection complete—168 study trips queried, 167 usable histories, 10,282 daily prices. Three BWI routes, departures October 31–December 25, 2026. Verified free quota remaining: 64. Spending: $0.** See [the collection report](docs/collection-report.md) and [the feasibility report](docs/feasibility.md) for verified facts and unresolved questions.

## Run locally

### Frozen descriptive analysis

The first offline analysis is complete. Open `artifacts/analysis-v1/report.md` locally for five figures, exact-horizon changes, route/lead-time and weekday comparisons, observed minima, and limitations. The report and data remain ignored pending redistribution/public-display clarification. This is descriptive research; no predictive model or buying strategy has been validated.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.lock.txt
python3 -m flights.freeze
.venv/bin/python -m flights.analyze
.venv/bin/python -m unittest discover -s tests -v
```

The freeze requires the collected, processed study files. It preserves version `2026-10-30-v1` and verifies input and raw-response hashes on every analysis run. Later collection cannot silently replace these analysis inputs. Analysis makes no API calls and needs no credentials. The locked environment was tested with Python 3.13.2; the standard-library collection pipeline remains separate from analysis dependencies.

Three revision-check refreshes are prepared in `config/refresh-three.json`; they have not been executed or automatically scheduled. All become eligible after the collector's 24-hour minimum at 12:48 PM Eastern on October 31, 2026. See `docs/analysis-methods.md` for the next steps.

### Collection and processing

Python 3.11+ on macOS/Linux. On macOS builds lacking a default CA file, the collector uses `/etc/ssl/cert.pem` with certificate verification enabled. The pilot uses only the Python standard library; no dependency installation is required. Tested with Python 3.13.2. Run from this repository's root:

```sh
python3 -m unittest discover -s tests -v
python3 -m flights.collect run
python3 -m flights.process
```

`run` defaults to a dry run: no credentials, network, or search quota. Processing is entirely offline and produces an explicit `NO_DATA` audit until responses exist. Tests use synthetic fixtures in temporary directories, not research data.

## Configure collection (historical pilot instructions below)

1. Create/sign into your own [SerpApi account](https://serpapi.com/users/sign_up). Choose Free; do not activate a paid plan, extra credits, or automatic paid renewal. Confirm the settings in the dashboard; signup/verification requirements have not been tested here.
2. Copy `.env.example` to `.env`, then edit `.env` locally to set `SERPAPI_API_KEY`. Never paste the key in chat. Set `SERPAPI_FREE_PLAN_CONFIRMED=true` only after checking the account settings. Environment variables take precedence over the file.
3. Review `config/pilot.json` and [the sampling plan](docs/sampling-plan.md). It is anchored to October 30, 2026. If stale, generate a new, separately named manifest rather than overwriting the original:

```sh
python3 -m flights.collect plan --anchor YYYY-MM-DD --output config/pilot-new.json
python3 -m flights.collect run --plan config/pilot-new.json
```

4. After configuration, the initial authorized collection command is:

```sh
python3 -m flights.collect run --live --limit 8
python3 -m flights.process
```

Use `--plan config/pilot-new.json` on the live command too if you generated a replacement. The cap is **200 attempted searches across all runs and manifests**, including failures, retries, and refreshes (authorized main collection after the initial diagnostics; also preserves at least 40 account searches). The ledger is `data/ledger.sqlite`; never delete it to regain budget. One ledger is shared by this checkout, not by separate copies or other tools using your account. Account quota is checked before every search; paid/unknown plans and exhausted/unknown capacity stop collection. No account settings are changed by code.

Successful queries are cached indefinitely for this pilot; rerunning skips them. Missing history in a successful response is still cached. Failed or crash-interrupted queries require `--retry-failed` after inspection. HTTP 429/selected 5xx responses receive at most one retry with backoff, counted against both caps; transport errors are not automatically retried. A failed search stops the run. A process lock prevents overlapping collectors in this checkout; reservations remain counted after a crash.

For one planned refresh after at least 24 hours, use a search ID printed by dry run:

```sh
python3 -m flights.collect run --live --only SEARCH_ID --refresh --limit 1
python3 -m flights.process
```

## Project layout

| Path | Purpose |
| --- | --- |
| `flights/collect.py` | Manifest generation, safe dry run, quota checks, durable request ledger, cached snapshots |
| `flights/process.py` | Normalization, quality audit, exact 1/3/7-calendar-day matching, revision and filter comparisons |
| `config/pilot.json` | Exact reproducible pilot queries; no secrets |
| `tests/test_pipeline.py` | Offline synthetic tests for core collection and processing risks |
| `docs/feasibility.md` | Evidence, current status, and decision gate |
| `docs/schema.md` | Metadata, observations, exclusions, and deduplication policy |
| `docs/sampling-plan.md` | Pilot budget and conditional expansion |
| `docs/research-plan.md` | Analysis, evaluation, strategy, and demo gates |
| `docs/verification.md` | Browser chart verification protocol and provider clarification draft |
| `data/raw/` | Ignored local sanitized provider responses with provenance |
| `data/normalized/` | Ignored snapshot-level observations, including flagged rows |
| `data/processed/` | Ignored daily observations, horizon changes, and machine-readable audit |

## Methods and limitations

The intended search is one adult, one-way, economy including basic, nonstop, no purchased extras, USD, US/English, fixed BWI/destination airports and departure date. Whether historical series obey these filters, include comparable mandatory taxes and fees, or represent the same minimum-fare definition is **unverified**. Today's price level and typical range remain snapshot metadata, never historical predictors.

Historical epochs are provisionally interpreted as Unix seconds. UTC instants and both UTC/Baltimore dates are retained; lead time currently uses the Baltimore calendar date. This convention requires provider/chart verification. Exact 3/7-day matches mean calendar dates, not a nearest available row or exactly 72/168 elapsed hours over daylight-saving changes. Missing values are never filled with zero or interpolated.

Descriptive selection uses the latest successful snapshot per exact query, while retaining all raw snapshots and reporting revisions. Identical duplicates collapse; conflicting daily prices are excluded from daily calculations and preserved for inspection. Large jumps are flagged, not automatically removed. Structurally usable does not mean semantically validated.

We will report the **lowest observed fare within the available window**, not an optimal booking time. Incomplete histories, correlated observations, route/calendar selection, and provider coverage constrain inference. Missing results do not establish sold-out status. Quotes do not establish completed purchases. BWI-only results will be described as sampled BWI routes, not all air travel.

## Attribution, publication, and deployment

Candidate source: Google Flights results extracted by SerpApi, a third-party service, not an official Google Flights API. Documentation reviewed October 30, 2026: [endpoint](https://serpapi.com/google-flights-api), [history](https://serpapi.com/google-flights-price-insights), [pricing](https://serpapi.com/pricing), [account quota](https://serpapi.com/account-api), and [terms](https://serpapi.com/legal).

Public redistribution permission has not been established. Raw data, derived data, screenshots, and artifacts are ignored until their permitted uses are clarified; attribution alone is not permission. Publish code and reproduction instructions independently of data. Do not assume aggregates or a public chart are automatically exempt. See the provider questions in `docs/verification.md`.

The demo and deployment are deliberately pending the feasibility gate. It will load saved, approved artifacts without credentials or live searches. Once actual storage, dependencies, startup time, and memory use are measured, evaluate a free host and document its then-current limits. No paid plans, overages, AI APIs, or deployment services are authorized. Total spending must stay below $20, with a $0 target.

## Main-study collection and offline coverage

The frozen manifest is `config/study.json`; it reuses six previously successful exact queries. Current collection protects a provider quota reserve of 40 and a project lifetime cap of 200 attempts. Do not delete the ledger or use a second checkout to bypass either limit. Original pilot instructions above describe the historical feasibility stage.

```sh
python3 -m flights.collect run --plan config/study.json
python3 -m flights.collection_report
python3 -m flights.process
```

The first command is a dry run. Offline exports are `data/processed/study-{summary,coverage,daily,changes}.json`. The study report uses only frozen manifest membership, excluding filter experiments and round trips. To inspect current free-account quota without a flight search, use `python3 -m flights.collect account`; it saves only safe quota fields locally.
