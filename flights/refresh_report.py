"""Compare selected refreshes with their recorded originals, entirely offline."""
import json
import sqlite3
from datetime import datetime, timezone
from flights.collect import ROOT, DATA, atomic_json
from flights.freeze import verify
from flights.process import normalize


def compare(old, new):
    before, old_issues = normalize(old)
    after, new_issues = normalize(new)
    a = {r['historical_timestamp']: r for r in before if r['eligible']}
    b = {r['historical_timestamp']: r for r in after if r['eligible']}
    common = sorted(a.keys() & b.keys())
    revised = [dict(timestamp=t, old_price=a[t]['price'], new_price=b[t]['price'])
               for t in common if a[t]['price'] != b[t]['price']]
    added = [b[t] for t in sorted(b.keys() - a.keys())]
    dropped = [a[t] for t in sorted(a.keys() - b.keys())]
    return dict(destination=old['params']['arrival_id'], departure_date=old['params']['outbound_date'],
                original_snapshot_id=old['snapshot_id'], refreshed_snapshot_id=new['snapshot_id'],
                original_retrieved_at=old['retrieved_at'], refreshed_at=new['retrieved_at'],
                exact_parameters_match=old['params'] == new['params'],
                original_observations=len(a), refreshed_observations=len(b),
                overlapping_timestamps=len(common), revisions=revised, added=added, dropped=dropped,
                original_issues=old_issues, refreshed_issues=new_issues,
                original_last=a[max(a)] if a else None, refreshed_last=b[max(b)] if b else None)


def run():
    verify()
    plan = json.loads((DATA/'verification/refresh-plan.json').read_text())
    results = []
    with sqlite3.connect(f'file:{DATA / "ledger.sqlite"}?mode=ro', uri=True) as conn:
        for item in plan:
            latest = conn.execute('SELECT snapshot_id FROM attempts WHERE search_id=? AND outcome=? '
                                  'ORDER BY requested_at DESC LIMIT 1', (item['search_id'], 'success')).fetchone()
            if not latest or latest[0] == item['original_snapshot_id']:
                raise RuntimeError('No successful refresh for '+item['search_id'])
            old = json.loads((DATA/'raw'/f'{item["original_snapshot_id"]}.json').read_text())
            new = json.loads((DATA/'raw'/f'{latest[0]}.json').read_text())
            result = compare(old, new)
            results.append(result)
            item.update(status='completed', refreshed_snapshot_id=new['snapshot_id'], refreshed_at=new['retrieved_at'])
    atomic_json(DATA/'verification/refresh-results.json', results)
    atomic_json(DATA/'verification/refresh-plan.json', plan)
    out = ROOT/'artifacts/refresh-checks'
    out.mkdir(parents=True, exist_ok=True)
    lines = ['# Three-trip refresh check', '',
             'Original retrievals: October 30, 2026. Latest successful refresh timestamps are recorded in the JSON audit. '
             'Comparisons use exact historical timestamps and identical query parameters. The original analysis freeze remains unchanged.', '',
             '| Route / departure | Original / refreshed observations | Overlap | Revised prices | Added / dropped timestamps | Latest observed price: old → refreshed |',
             '| --- | ---: | ---: | ---: | ---: | --- |']
    for r in results:
        last, newlast = r['original_last'], r['refreshed_last']
        prices = (f"${last['price']} ({last['observation_date']}) → ${newlast['price']} ({newlast['observation_date']})"
                  if last and newlast else 'History unavailable')
        lines.append(f"| BWI–{r['destination']} / {r['departure_date']} | {r['original_observations']} / {r['refreshed_observations']} | "
                     f"{r['overlapping_timestamps']} | {len(r['revisions'])} | {len(r['added'])} / {len(r['dropped'])} | {prices} |")
    lines += ['', '## Revisions at overlapping timestamps', '']
    for r in results:
        for revision in r['revisions']:
            stamp = datetime.fromtimestamp(revision['timestamp'], timezone.utc).isoformat()
            lines.append(f"- BWI–{r['destination']}: {stamp}, ${revision['old_price']} → ${revision['new_price']}.")
    lines += ['', 'Revisions mean the refreshed history cannot simply be treated as what was known at each earlier prediction time. '
              'Preserve retrieval versions for any future backtest. The reason for these revisions is not established.', '',
              'Added timestamps and removed timestamps are listed separately from revisions. A rolling window can drop older observations; '
              'a missing history is not evidence of no flights. The latest-price comparison is between the dates shown, not necessarily an exact seven-day change.', '',
              'This small check can detect revisions but cannot prove general stability, historical filter semantics, or point-in-time availability. '
              'These three selected trips do not form a sufficient independent model evaluation sample. Keep raw snapshots and analyze the frozen report separately.', '',
              'Reproduce offline: `python3 -m flights.refresh_report`. Detailed local audit: `data/verification/refresh-results.json`.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    run()
