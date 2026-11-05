# Provider inquiry draft — not sent

## Current draft — November 5, 2026

Subject: Google Flights history semantics, revisions, and noncommercial portfolio display

Hello SerpApi support,

We are developing a noncommercial data-science portfolio project using your Google Flights endpoint. Minimal one-way searches now return histories reliably for our sampled BWI routes. Our local study has 167 usable route/date histories from 168 planned searches.

Search constraints are one adult, one-way, economy, nonstop, USD, US/English locale. We use the search-level `price_insights.price_history`, not a travel-date grid. On November 5, we refreshed three October 30 queries with identical parameters. All returned 62 observations; six dates were added and six oldest dates removed. Two overlapping historical prices changed: BWI–MCO November 20 departure, October 29 historical timestamp, $123 to $94; and BWI–DEN December 4 departure, October 30 timestamp, $168 to $134. We preserve both retrievals and make no live booking or predictive-accuracy claims.

Could you clarify:

1. Do historical prices reflect the cheapest returned option under our passenger/cabin/nonstop filters, including basic economy? Do mandatory taxes and fees use comparable definitions throughout the history?
2. What timezone, aggregation, and within-day convention do the historical timestamps represent? Are the revisions above expected, and what can cause changes to earlier observations?
3. Is local storage for this research permitted, and under what retention conditions?
4. May a free, noncommercial public portfolio demo display individual collected histories and aggregate statistics? May we distribute processed observations, raw responses, or Google Flights verification screenshots? Please distinguish these uses and any upstream restrictions.
5. What attribution or other requirements would apply?

We can provide the relevant provider search IDs privately if helpful. No API key is included. The real-data demo currently stays local, pending clarification.

Thank you.

---

## Earlier diagnostic draft (historical)

**Update:** The original omission report below is historical. A later minimal one-way request and its fresh-fetch repeat returned 62 browser-matched points; a round-trip control also succeeded. Before sending, include this result and ask which optional parameters could suppress insights, alongside the semantic and publication questions.

Subject: Google Flights price_insights absent despite visible browser history

Hello SerpApi support,

On October 30, 2026, our Free-plan pilot made ten successful google_flights searches. All returned current flight options, but none returned price_insights. We are testing a noncommercial portfolio project before expanding collection.

A reproducible example is BWI to ATL departing 2026-11-06, type=2, adults=1, children=0, infants_in_seat=0, infants_on_lap=0, travel_class=1, stops=1, currency=USD, gl=us, hl=en, exclude_basic=false, bags=0. We tested (sort_by=2, deep_search=true), (sort_by=1, deep_search=true), and (sort_by=1, deep_search=false). All omitted price_insights. The corresponding Google Flights browser page displayed an expanded price-history chart. BWI to DEN on 2026-12-01 also displayed a browser history that was absent from the API response.

Is this a known extraction issue or an unsupported combination? Is another documented setting required? We can provide provider search IDs and sanitized responses privately if helpful, but will not share our API key.

Before proceeding, could you also clarify:

1. What does each historical price represent, and which search filters apply historically (stops, economy/basic, passengers, airports, bags and currency)? Are mandatory taxes and fees comparable across observations?
2. What timestamp unit/timezone and daily aggregation convention apply? Can earlier prices or timestamps be revised or removed?
3. Is local research storage permitted? Can a noncommercial portfolio demo display individual curves and aggregate statistics? Can processed or raw histories and verification screenshots be redistributed? What retention, attribution, or upstream rights restrictions apply?

Thank you.
