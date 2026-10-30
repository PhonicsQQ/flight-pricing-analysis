# Evidence collection checklist

## Visible Google Flights history charts

After authenticated responses exist, inspect at least three baseline trips spanning destinations and the near/far dates, plus the filter-contrast trip where accessible. Use the returned Google Flights URL when available; otherwise manually reproduce exact parameters. Keep BWI as an airport, one-way, one adult, economy, nonstop, USD, US/English, with matching basic-economy choice.

Record a local evidence file for each comparison under ignored `data/verification/`:

```json
{
  "search_id": "fill_from_audit",
  "snapshot_id": "fill_from_audit",
  "checked_at_utc": null,
  "browser_url": null,
  "filters_visually_confirmed": [],
  "chart_type": "fixed_trip_price_history",
  "chart_available": null,
  "visible_date_price_pairs": [],
  "api_matching_pairs": [],
  "date_offset_or_rounding_notes": null,
  "agreement_or_discrepancy": "not_checked",
  "local_screenshot_path": null
}
```

Check several tooltip dates, including early/late and a price change. Record chart granularity, date shifts, currency, retrieval lag, and mismatches; do not infer exact points from a coarse curve. A date grid or travel-date price graph is not historical evidence. If no chart is accessible, say so; do not mark verification passed. Chart agreement strengthens extraction evidence but does not establish all historical fare conditions. Preserve screenshots locally only pending publication rights.

## Provider clarification draft — not sent

We are preparing a noncommercial portfolio research project on fixed BWI-to-US-airport, one-way, one-adult economy trip histories, including basic fares, initially nonstop, in USD. Could you clarify:

1. Does `price_history` represent the minimum across qualifying search results at each timestamp? Which current filters apply to historical values (stops, cabin, passenger count, basic exclusion, bags, currency, airports)?
2. Are mandatory taxes/fees included consistently? Can fare conditions or the historical search universe change within a series?
3. What is the epoch unit and timezone/date convention? Does each point denote a daily minimum, snapshot quote, or another statistic? Can timestamps or earlier prices be revised or removed?
4. Are local storage and reproducible research permitted? May we publicly display individual historical curves, small processed datasets, aggregate statistics, and screenshots? May raw responses be redistributed? What attribution, retention, or other restrictions apply, including upstream rights?

Record any answer with date and scope. Do not contact the provider without explicit authorization to send a message. Until clarified, keep public data exports disabled. If permissions or history availability prevent the planned project, discuss a licensed dataset or smaller prospective quote study with the user before changing scope.
