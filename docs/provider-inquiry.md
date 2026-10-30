# Provider inquiry draft — not sent

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
