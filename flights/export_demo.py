"""Export only allowlisted, saved research fields to an ignored local demo."""
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import shutil
from flights.freeze import ROOT, FROZEN, verify, sha

OUT = ROOT / 'artifacts/demo'


def export_payload():
    manifest = verify()
    daily = json.loads((FROZEN/'study-daily.json').read_text())
    coverage = json.loads((FROZEN/'study-coverage.json').read_text())
    results = json.loads((ROOT/'artifacts/analysis-v1/results.json').read_text())
    if results['freeze_version'] != manifest['version']:
        raise ValueError('Analysis version does not match frozen data')
    if results['observations'] != len(daily):
        raise ValueError('Analysis observation count differs')
    groups = defaultdict(list)
    for row in daily:
        groups[row['search_id']].append(row)
    trips = []
    for row in coverage:
        points = sorted(groups[row['search_id']], key=lambda x:x['observation_date'])
        if len({p['observation_date'] for p in points}) != len(points):
            raise ValueError('Ambiguous daily observations')
        trips.append(dict(id=row['search_id'], route=row['destination'], departure=row['departure_date'],
                          retrieved=row['retrieved_at'], holidays=row['holiday_windows'],
                          points=[[p['observation_date'], p['price'], p['days_until_departure']] for p in points]))
    # Ensure chart-derived changes and saved headline rates agree before packaging.
    for summary in results['overall']:
        horizon = int(summary['label'])
        changes = []
        pairs = 0
        for trip in trips:
            prices = {date.fromisoformat(p[0]).toordinal():p[1] for p in trip['points']}
            delta = [prices[t+horizon]-v for t,v in prices.items() if t+horizon in prices]
            if delta:
                changes.append(sum(v>0 for v in delta)/len(delta))
                pairs += len(delta)
        if pairs != summary['pairs'] or abs(sum(changes)/len(changes)-summary['trip_up']) > 1e-10:
            raise ValueError('Saved analysis does not agree with exact-horizon chart data')
    refresh_path = ROOT/'data/verification/refresh-results.json'
    refreshes = []
    if refresh_path.exists():
        for r in json.loads(refresh_path.read_text()):
            refreshes.append(dict(route=r['destination'], departure=r['departure_date'],
                retrieved=r['refreshed_at'], overlap=r['overlapping_timestamps'], revisions=r['revisions'],
                added=[[p['observation_date'],p['price']] for p in r['added']],
                dropped=len(r['dropped']),
                original_last=[r['original_last']['observation_date'],r['original_last']['price']] if r['original_last'] else None))
    sensitivity_path = ROOT/'artifacts/analysis-v1/same-trip-sensitivity.json'
    sensitivity = json.loads(sensitivity_path.read_text()) if sensitivity_path.exists() else None
    return dict(version=manifest['version'], trips=trips, results=results, refreshes=refreshes, sensitivity=sensitivity,
                attribution='Google Flights via SerpApi (third-party extraction)',
                observation_zone='America/New_York (provisional)',
                use='Local research only; public display and redistribution unresolved')


def build():
    payload = export_payload()
    OUT.mkdir(parents=True, exist_ok=True)
    for path in (ROOT/'demo').iterdir():
        if path.suffix in {'.html','.css','.mjs'}:
            shutil.copyfile(path, OUT/path.name)
    (OUT/'data.json').write_text(json.dumps(payload, separators=(',',':'),allow_nan=False)+'\n')
    files = [p for p in OUT.iterdir() if p.is_file() and p.name != 'build.json']
    metrics = dict(version=payload['version'], files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files},
                   total_bytes=sum(p.stat().st_size for p in files),runtime='Static browser; Python standard-library local server only')
    (OUT/'build.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps(dict(output=str(OUT),bytes=metrics['total_bytes'],trips=len(payload['trips']),
                         usable=sum(bool(t['points']) for t in payload['trips'])),indent=2))


if __name__ == '__main__':
    build()
