"""Offline study coverage report. No credentials or network calls."""
from collections import Counter, defaultdict
from datetime import date
import json
import sqlite3

from flights.collect import DATA, ROOT, atomic_json, query_id
from flights.process import normalize, daily_series, exact_changes


def report():
    manifest = json.loads((ROOT / 'config/study.json').read_text())
    snapshots = [json.loads(p.read_text()) for p in (DATA / 'raw').glob('*.json')]
    by_query = defaultdict(list)
    for s in snapshots:
        by_query[s['search_id']].append(s)
    coverage, all_daily, all_pairs = [], [], []
    for q in manifest['queries']:
        p = q['params']
        attempts = by_query[query_id(p)]
        successes = [s for s in attempts if s['outcome']=='success']
        s = max(successes,key=lambda s:s['retrieved_at']) if successes else None
        rows,issues = normalize(s) if s else ([],['not_successfully_collected'])
        daily = daily_series(rows)
        all_daily.extend(daily)
        pairs = [v for h in (1,3,7) for v in exact_changes(daily,h)]
        all_pairs.extend(pairs)
        flags = Counter(f for r in rows for f in r['quality_flags'])
        flights = (s['response'].get('best_flights',[])+s['response'].get('other_flights',[])) if s else []
        invalid_current = sum(len(f.get('flights',[])) != 1 or
            any(leg.get('travel_class') != 'Economy' for leg in f.get('flights',[])) for f in flights)
        option_prices = [f['price'] for f in flights if type(f.get('price')) in (int,float) and f['price'] > 0]
        current_min = min(option_prices,default=None)
        insight_min = s['response'].get('price_insights',{}).get('lowest_price') if s else None
        days = [date.fromisoformat(r['observation_date']) for r in daily]
        gaps = sum((b-a).days-1 for a,b in zip(days,days[1:]))
        coverage.append(dict(search_id=query_id(p),destination=p['arrival_id'],departure_date=p['outbound_date'],
            departure_weekday=date.fromisoformat(p['outbound_date']).strftime('%A'),
            holiday_windows=[name for name,(start,end) in manifest['holiday_windows'].items() if start<=p['outbound_date']<=end],
            outcome=s['outcome'] if s else 'missing_or_failed', snapshot_id=s['snapshot_id'] if s else None,
            retrieved_at=s['retrieved_at'] if s else None, history_rows=len(rows),usable_dates=len(daily),
            first_observed=daily[0]['observation_date'] if daily else None,
            last_observed=daily[-1]['observation_date'] if daily else None,
            final_lead_days=daily[-1]['days_until_departure'] if daily else None,
            missing_calendar_days=gaps,issues=issues,quality_flags=dict(flags),
            current_option_count=len(flights),current_options_failing_nonstop_economy_check=invalid_current,
            current_min_returned_option=current_min,current_insights_lowest_price=insight_min,
            current_minimum_discrepancy=(current_min != insight_min) if current_min is not None and insight_min is not None else None,
            last_history_vs_current_discrepancy=(daily[-1]['price'] != insight_min) if daily and insight_min is not None else None,
            exact_pairs={str(h):sum(v['horizon_days']==h for v in pairs) for h in (1,3,7)}))
    route_summaries = {}
    for route in ('ATL','MCO','DEN'):
        group = [r for r in coverage if r['destination']==route]
        usable = [r for r in group if r['usable_dates']]
        route_summaries[route] = dict(planned_trips=len(group),collected=sum(r['outcome']=='success' for r in group),
            trips_with_usable_history=len(usable),daily_observations=sum(r['usable_dates'] for r in group),
            min_history_days=min((r['usable_dates'] for r in usable),default=None),
            max_history_days=max((r['usable_dates'] for r in usable),default=None))
    with sqlite3.connect(DATA / 'ledger.sqlite') as c:
        attempts=c.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]
    summary=dict(planned_trip_count=len(coverage),successful_study_queries=sum(r['outcome']=='success' for r in coverage),
        independent_trips_with_usable_history=sum(bool(r['usable_dates']) for r in coverage),
        usable_daily_observations=len(all_daily),exact_horizon_pairs={str(h):sum(v['horizon_days']==h for v in all_pairs) for h in (1,3,7)},
        project_attempts=attempts,routes=route_summaries,
        no_history_trips=[r['search_id'] for r in coverage if r['outcome']=='success' and not r['usable_dates']],
        pending_or_failed_trips=[r['search_id'] for r in coverage if r['outcome']!='success'],
        current_options_failing_nonstop_economy_check=sum(r['current_options_failing_nonstop_economy_check'] for r in coverage),
        current_minimum_discrepancy_count=sum(r['current_minimum_discrepancy'] is True for r in coverage),
        last_history_vs_current_discrepancy_count=sum(r['last_history_vs_current_discrepancy'] is True for r in coverage),
        caveat='Provisional provider-reported histories under intended filters. Correlated observations, incomplete histories, selected BWI routes. No historical fare-universe or redistribution guarantee.')
    atomic_json(DATA / 'processed/study-coverage.json',coverage)
    atomic_json(DATA / 'processed/study-summary.json',summary)
    atomic_json(DATA / 'processed/study-daily.json',all_daily)
    atomic_json(DATA / 'processed/study-changes.json',all_pairs)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('no_history_trips','pending_or_failed_trips')},indent=2))
    return summary


if __name__ == '__main__':
    report()
