"""Exploratory same-trip sensitivity; not a causal estimate or test-set evaluation."""
import json
from flights.analyze import pd, OUT, summarize, trip_statistics, intervals
from flights.freeze import FROZEN, verify


def run():
    verify()
    changes=pd.DataFrame(json.loads((FROZEN/'study-changes.json').read_text()))
    coverage=pd.DataFrame(json.loads((FROZEN/'study-coverage.json').read_text()))
    changes=changes.merge(coverage[['search_id','departure_date']],on='search_id',validate='many_to_one')
    seven=changes[changes.horizon_days==7]
    near=seven[seven.days_until_departure.between(8,14)]
    far=seven[seven.days_until_departure.between(31,60)]
    ids=set(near.search_id)&set(far.search_id)
    near=near[near.search_id.isin(ids)];far=far[far.search_id.isin(ids)]
    a,b=trip_statistics(near),trip_statistics(far)
    diff=a.copy()
    diff['up']=a.up-b.up
    diff['usd']=a.usd-b.usd
    result=dict(label='Same trips: 8–14 versus 31–60 starting lead days',trips=len(ids),
                near=summarize(near,'8–14'),far=summarize(far,'31–60'),
                mean_within_trip_difference_rise=float(diff.up.mean()),mean_within_trip_difference_usd=float(diff.usd.mean()),
                difference_intervals=intervals(diff),
                note='Exploratory sensitivity selected after first results. Same trips reduce route/departure composition differences, but observation calendar dates differ and near-bin coverage varies. Not causal or representative.')
    (OUT/'same-trip-sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Same-trip lead-time sensitivity','',result['note'],'',
           f"Eligible trips: {len(ids)}. Require at least one exact seven-day pair in both bins; all original extreme prices retained.",'',
           '| Starting lead | Trips | Pairs | Equal-trip rise frequency | Mean seven-day change |',
           '| --- | ---: | ---: | ---: | ---: |']
    for row in [result['near'],result['far']]:
        lines.append(f"| {row['label']} | {row['trips']} | {row['pairs']} | {100*row['trip_up']:.1f}% | ${row['mean_usd']:.2f} |")
    ci=result['difference_intervals']['usd_trip_ci']
    lines+=['',f"Mean within-trip difference (near minus far): ${result['mean_within_trip_difference_usd']:.2f}; trip-bootstrap range ${ci[0]:.2f}–${ci[1]:.2f}.",'',
            'This checks whether the observed pattern disappears when comparing the same trips. It does not isolate an effect of waiting: market dates and lead times still move together, and the small near-departure group is selected.']
    (OUT/'same-trip-sensitivity.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    run()
