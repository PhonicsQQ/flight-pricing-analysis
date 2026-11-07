"""Offline sensitivity of exact-lead historical means; never remove primary observations."""
import json
from math import ceil
from statistics import mean
from flights.freeze import ROOT, FROZEN, verify


def audit_changes(values):
    if not values:
        return None
    n=len(values)
    avg=mean(values)
    ordered=sorted(enumerate(values),key=lambda x:(-abs(x[1]),x[0]))
    largest=ordered[0][1]
    loo=[(sum(values)-v)/(n-1) for v in values] if n>1 else []
    removed=ceil(n*.1)
    remaining=[v for _,v in ordered[removed:]]
    return dict(trips=n,mean=avg,largest_absolute_change=largest,
                without_largest=mean([v for _,v in ordered[1:]]) if n>1 else None,
                leave_one_out_min=min(loo) if loo else None,leave_one_out_max=max(loo) if loo else None,
                sign_can_flip=any(avg*v<0 for v in loo),
                removed_for_sensitivity=removed,without_largest_10pct=mean(remaining) if remaining else None,
                small_sample=n<10)


def run():
    verify()
    daily=json.loads((FROZEN/'study-daily.json').read_text())
    groups={}
    for r in daily:
        groups.setdefault((r['destination'],r['search_id']),{})[r['days_until_departure']]=r['price']
    cases=[]
    for route in ['ALL','ATL','MCO','DEN']:
        for lead in [60,45,30,21,14,7]:
            for horizon in [1,3,7]:
                values=[prices[lead-horizon]-prices[lead] for (dest,sid),prices in groups.items()
                        if (route=='ALL' or route==dest) and lead in prices and lead-horizon in prices]
                cases.append(dict(route=route,lead=lead,horizon=horizon,**(audit_changes(values) or dict(trips=0))))
    out=ROOT/'artifacts/analysis-v1'
    (out/'mean-sensitivity.json').write_text(json.dumps(cases,indent=2)+'\n')
    lines=['# Expected-change sensitivity audit','',
           'Primary means retain every observed fare. Each scenario uses one exact pair per eligible trip. '
           'Removing the largest absolute change or top 10% is a diagnostic, not a cleaned estimate. '
           'No resampling interval is presented as population confidence.','',
           '| Start / wait | Trips | Mean | Without largest absolute change | Without largest 10% |',
           '| --- | ---: | ---: | ---: | ---: |']
    money=lambda x:'—' if x is None else f'${x:+.2f}'
    for c in cases:
        if c['route']=='ALL' and c['horizon']==7:
            lines.append(f"| {c['lead']} / 7 days | {c['trips']} | {money(c.get('mean'))} | {money(c.get('without_largest'))} | {money(c.get('without_largest_10pct'))} |")
    usable=[c for c in cases if c['trips']]
    lines+=['',f"Of {len(usable)} nonempty scenarios, {sum(c['small_sample'] for c in usable)} have fewer than 10 trips; "
             f"{sum(c['sign_can_flip'] for c in usable)} change mean sign when a single trip is omitted.", '',
             'The 72 scenarios reuse trips and are not independent experiments. Small samples and shared calendar shocks remain. '
             'Tail removal can alter the research population and suppress real risk. Never replace the primary mean with the most favorable sensitivity.', '',
             'Reproduce: `python3 -m flights.mean_audit`. Detailed results: `mean-sensitivity.json`.']
    (out/'mean-sensitivity.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':
    run()
