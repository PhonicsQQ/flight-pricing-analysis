"""Offline comparison of the authorized extension with saved browser evidence."""
from datetime import date, timedelta
import json
import re

from flights.collect import DATA, atomic_json
from flights.process import normalize, daily_series, exact_changes


def verify():
    snapshots = [json.loads(p.read_text()) for p in (DATA / 'raw').glob('*.json')]
    selected = {s['role']: s for s in snapshots
                if s['role'] in {'diagnostic_minimal', 'diagnostic_fresh', 'diagnostic_roundtrip'}}
    evidence = (DATA / 'verification/atl-2026-11-06-ax.txt').read_text()
    # Date when the saved browser evidence was observed, not the date of rerun.
    checked_date = date(2026, 10, 30)
    labels = re.findall(r'button (\d+ days ago|1 day ago|Today) - \$(\d+)', evidence)
    browser = [((checked_date - timedelta(days=0 if label == 'Today' else int(label.split()[0]))).isoformat(), int(price))
               for label, price in labels]
    minimal = selected['diagnostic_minimal']
    rows, issues = normalize(minimal)
    daily = daily_series(rows)
    api = [(r['observation_date'], r['price']) for r in daily]
    fresh = selected['diagnostic_fresh']
    result = dict(
        browser_evidence_date=checked_date.isoformat(),
        browser_evidence_file='data/verification/atl-2026-11-06-ax.txt',
        minimal_snapshot_id=minimal['snapshot_id'], fresh_snapshot_id=fresh['snapshot_id'],
        browser_point_count=len(browser), api_point_count=len(api),
        all_date_price_pairs_match=bool(browser) and browser == api,
        fresh_timestamp_price_pairs_identical=(minimal['response']['price_insights']['price_history'] ==
                                               fresh['response']['price_insights']['price_history']),
        independent_oneway_trips=1, quality_issues=issues,
        diagnostic_exact_horizon_pair_counts={str(h):len(exact_changes(daily,h)) for h in (1,3,7)},
        note='Diagnostic series only; two one-way snapshots are one trip. Same-session agreement does not establish long-term stability, fare-universe semantics, or timezone behavior outside this sample.')
    atomic_json(DATA / 'verification/extension-comparison.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
