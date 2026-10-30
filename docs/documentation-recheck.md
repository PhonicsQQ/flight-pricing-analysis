# Documentation recheck — October 30, 2026

No additional authenticated searches were made during this documentation review. Subsequently, the user authorized three more diagnostics; the minimal request succeeded. See the latest feasibility report.

## Findings

- The [dedicated insights documentation](https://serpapi.com/google-flights-price-insights) uses the same `search?engine=google_flights` endpoint as general flight searches. It describes `price_insights.price_history` as an output field, not a separate history endpoint or an opt-in request parameter.
- The [main API parameter reference](https://serpapi.com/google-flights-api) supports our one-way search structure: `type=2` with an outbound date, without a return date. No one-way exclusion for historical insights was found. This is absence of a documented restriction, not proof of reliable one-way coverage.
- Our passenger, cabin, nonstop, currency, and US/English settings follow the documented parameters. Both documented sort choices and both deep-search modes were tested for ATL; no history appeared. There is no documented need to select a flight or request booking options to retrieve the search-level history.
- We did not send `json_restrictor`, which could suppress output fields, or use asynchronous retrieval. All ten saved responses have `search_metadata.status=Success`. A recursive scan of the complete saved response objects found no history/insight keys anywhere; normalization did not discard the data.
- SerpApi's [official example repository](https://github.com/serpapi/google-flights-scraper) qualifies history availability. Its blog's broad description of responses should not be read as a guarantee for every query. Neither source identifies an extra history activation switch.
- `no_cache=true` requests fresh results, but is not documented as a history-enabling option. We did not test it, nor a minimal request with optional defaults omitted, nor a round-trip control. These remain possible diagnostic designs, not established fixes. A round-trip control would remain separate from the one-way study. No such requests were executed beyond the pilot cap.
- The [release notes](https://serpapi.com/google-flights-api/release-notes) and targeted public issue searches reviewed did not identify a specific missing-history explanation. This does not establish that no relevant issue exists.

## Separate cheapest-fare caveat

SerpApi's [Cheapest-tab issue](https://github.com/serpapi/public-roadmap/issues/3733) describes that tab as unsupported at the time of the report and points to [issue 2485](https://github.com/serpapi/public-roadmap/issues/2485), which is still open/queued when reviewed. Thus `sort_by=2` must not be equated with selecting the separate Cheapest tab. This is relevant to the search universe and minimum-fare claim, but does not explain absent history from the Best-tab search observed in our pilot.

## Conclusion

No documented mandatory parameter was found that our collector omitted. We have a reproducible omission for the tested searches, not proof that SerpApi history never works or that every request variant has been ruled out. Ask support about the stored search IDs and browser/API discrepancy before expanding collection. Maintain the unresolved historical semantics and publication-rights gates.
