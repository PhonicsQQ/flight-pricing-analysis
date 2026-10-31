"""Frozen, offline descriptive analysis. No fitting or predictive claims."""
import json
import os
from pathlib import Path

from flights.freeze import FROZEN, ROOT, verify

OUT = ROOT / 'artifacts/analysis-v1'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 20261031
B = 2000
BUCKETS = ['1–7', '8–14', '15–30', '31–60', '61–90', '91+']
DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
COLORS = {'ATL':'#287b8e','MCO':'#e19035','DEN':'#7257a4'}


def bucket(values):
    return pd.cut(values, [0,7,14,30,60,90,1000], labels=BUCKETS)


def trip_statistics(group):
    x = group.assign(up=(group.change_usd > 0).astype(float), down=(group.change_usd < 0).astype(float),
                     flat=(group.change_usd == 0).astype(float), abs_change=group.change_usd.abs())
    return x.groupby('search_id').agg(up=('up','mean'), down=('down','mean'), flat=('flat','mean'),
        usd=('change_usd','mean'), pct=('change_percent','mean'), mae=('abs_change','mean'),
        destination=('destination','first'), departure_date=('departure_date','first'))


def intervals(t):
    """Stratified trip bootstrap and departure-week block sensitivity; no row bootstrap."""
    if len(t) < 2:
        return {k:[None,None] for k in ('up_trip_ci','usd_trip_ci','up_week_ci','usd_week_ci')}
    rng = np.random.default_rng(SEED)
    sims = np.zeros((B,2))
    for _, g in t.groupby('destination'):
        v = g[['up','usd']].to_numpy()
        sims += v[rng.integers(0,len(v),(B,len(v)))].sum(axis=1) / len(t)
    weeks = ((pd.to_datetime(t.departure_date)-pd.Timestamp('2026-10-31')).dt.days//7)
    sums = t[['up','usd']].groupby(weeks).sum().to_numpy()
    counts = t.groupby(weeks).size().to_numpy()
    if len(counts)>1:
        ix = rng.integers(0,len(counts),(B,len(counts)))
        block = sums[ix].sum(axis=1)/counts[ix].sum(axis=1)[:,None]
        block_ci = np.quantile(block,[.025,.975],axis=0)
    else:
        block_ci = np.full((2,2),np.nan)
    ci = np.quantile(sims,[.025,.975],axis=0)
    return dict(up_trip_ci=ci[:,0].tolist(), usd_trip_ci=ci[:,1].tolist(),
                up_week_ci=[float(v) if np.isfinite(v) else None for v in block_ci[:,0]],
                usd_week_ci=[float(v) if np.isfinite(v) else None for v in block_ci[:,1]])


def summarize(g, label):
    t = trip_statistics(g)
    result = dict(label=str(label), trips=len(t), pairs=len(g),
        trip_up=float(t.up.mean()), trip_down=float(t.down.mean()),trip_unchanged=float(t.flat.mean()),
        row_up=float((g.change_usd>0).mean()), row_down=float((g.change_usd<0).mean()),
        mean_usd=float(t.usd.mean()),mean_pct=float(t.pct.mean()),
        row_median_usd=float(g.change_usd.median()), row_median_pct=float(g.change_percent.median()),
        row_p10_usd=float(g.change_usd.quantile(.1)),row_p90_usd=float(g.change_usd.quantile(.9)),
        mean_increase_usd=float(g.loc[g.change_usd>0,'change_usd'].mean()) if (g.change_usd>0).any() else None,
        mean_decrease_usd=float(g.loc[g.change_usd<0,'change_usd'].mean()) if (g.change_usd<0).any() else None,
        no_change_baseline_mae=float(t.mae.mean()), **intervals(t))
    return result


def weekday_standardized(g, field):
    """Equal-trip cell means; reweight common route/lead cells, minimum 3 trips/day/cell."""
    t = g.assign(up=(g.change_usd>0).astype(float)).groupby(
        ['destination','lead_bucket',field,'search_id'],observed=True).up.mean().reset_index()
    cells = t.groupby(['destination','lead_bucket',field],observed=True).up.agg(['mean','count']).reset_index()
    means = cells.pivot(index=['destination','lead_bucket'],columns=field,values='mean').reindex(columns=DAYS)
    counts = cells.pivot(index=['destination','lead_bucket'],columns=field,values='count').reindex(columns=DAYS)
    good = (counts.fillna(0)>=3).all(axis=1)
    means,counts = means.loc[good],counts.loc[good]
    weights=counts.sum(axis=1)
    standardized=(means.mul(weights,axis=0).sum(axis=0)/weights.sum()).to_dict() if len(means) else {}
    return dict(common_cells=len(means),rates=standardized,
                note='Common route/lead cells only, >=3 distinct trips per weekday/cell. No calendar adjustment or causal interpretation.')


def savefig(fig, name):
    fig.savefig(OUT / (name+'.png'), dpi=170, bbox_inches='tight',facecolor='#fbfcfe')
    fig.savefig(OUT / (name+'.svg'), bbox_inches='tight',facecolor='#fbfcfe')
    plt.close(fig)


def run():
    provenance=verify()
    d=pd.DataFrame(json.loads((FROZEN/'study-daily.json').read_text()))
    c=pd.DataFrame(json.loads((FROZEN/'study-changes.json').read_text()))
    coverage=pd.DataFrame(json.loads((FROZEN/'study-coverage.json').read_text()))
    assert not d.duplicated(['search_id','observation_date']).any()
    metadata=d[['search_id','observation_date','departure_date','observation_weekday','departure_weekday']]
    c=c.merge(metadata,on=['search_id','observation_date'],validate='many_to_one')
    assert ((pd.to_datetime(c.label_date)-pd.to_datetime(c.observation_date)).dt.days==c.horizon_days).all()
    d['lead_bucket']=bucket(d.days_until_departure)
    c['lead_bucket']=bucket(c.days_until_departure)
    holidays=coverage[['search_id','holiday_windows']].copy()
    holidays['holiday_window']=holidays.holiday_windows.map(lambda v:'Holiday window' if v else 'Outside marked windows')
    c=c.merge(holidays[['search_id','holiday_window']],on='search_id',validate='many_to_one')
    overall=[summarize(g,int(h)) for h,g in c.groupby('horizon_days')]
    seven=c[c.horizon_days==7]
    routes=[summarize(g,r) for r,g in seven.groupby('destination')]
    leads=[summarize(g,str(b)) for b,g in seven.groupby('lead_bucket',observed=True)]
    calendar=[summarize(g,r) for r,g in seven.groupby('holiday_window')]
    weekday={field:dict(raw=[summarize(g,w) for w,g in seven.groupby(field)],
                        standardized=weekday_standardized(seven,field))
             for field in ('departure_weekday','observation_weekday')}
    minima=[]
    for sid,g in d.groupby('search_id'):
        g=g.sort_values('observation_date'); ties=g[g.price==g.price.min()]
        minima.append(dict(search_id=sid,destination=g.iloc[0].destination,departure_date=g.iloc[0].departure_date,
            minimum_price=float(g.price.min()),earliest_tied_lead=int(ties.days_until_departure.max()),
            latest_tied_lead=int(ties.days_until_departure.min()),tied_days=len(ties),
            includes_first=bool(g.iloc[0].price==g.price.min()),includes_last=bool(g.iloc[-1].price==g.price.min()),
            final_lead=int(g.days_until_departure.min())))
    minima=pd.DataFrame(minima)
    # Flag extreme changes without automatically deleting them.
    adjacent=c[c.horizon_days==1].copy()
    extreme=adjacent[(adjacent.future_price/adjacent.price>2)|(adjacent.future_price/adjacent.price<.5)]
    no_extreme=seven[~seven.search_id.isin(extreme.search_id)]
    sensitivity=summarize(no_extreme,'Trips without flagged daily jumps') if len(no_extreme) else None
    timezone_differences=int((d.observation_date!=d.observation_date_utc).sum())
    results=dict(freeze_version=provenance['version'],seed=SEED,bootstrap_draws=B,
        trips=int(d.search_id.nunique()),observations=len(d),overall=overall,routes_7d=routes,lead_7d=leads,
        holiday_7d=calendar,weekdays_7d=weekday,
        timezone_date_differences=timezone_differences,
        extrema=dict(flagged_daily_jumps=len(extreme),affected_trips=int(extreme.search_id.nunique()),
                     exclusion_sensitivity_not_primary=sensitivity),
        minimum_summary=dict(trips=len(minima),includes_first=int(minima.includes_first.sum()),
            includes_last=int(minima.includes_last.sum()),multiple_tied_days=int((minima.tied_days>1).sum()),
            median_earliest_tied_lead=float(minima.earliest_tied_lead.median()),
            median_latest_tied_lead=float(minima.latest_tied_lead.median())),
        uncertainty_note='Trip bootstrap stratified by route. Departure-week block intervals are sensitivity checks with only 8 blocks. Neither captures all shared observation-date shocks nor supports population inference.')
    (OUT/'results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    minima.to_csv(OUT/'observed-minima.csv',index=False)
    extreme.sort_values('change_usd',key=lambda s:s.abs(),ascending=False).to_csv(OUT/'flagged-jumps.csv',index=False)
    for name,rows in [('overall',overall),('routes-7d',routes),('lead-7d',leads),('holidays-7d',calendar)]:
        pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.titleweight':'bold','axes.facecolor':'#fbfcfe'})
    fig,axs=plt.subplots(3,1,figsize=(11,9),layout='constrained',sharex=True)
    for ax,(route,color) in zip(axs,COLORS.items()):
        for departure in ('2026-11-06','2026-11-28','2026-12-18'):
            g=d[(d.destination==route)&(d.departure_date==departure)].sort_values('days_until_departure')
            ax.plot(g.days_until_departure,g.price,label=f'{departure} · {len(g)} days',linewidth=1.8)
        ax.set_title(f'BWI → {route} | selected dates fixed before inspecting outcomes',loc='left',fontsize=11)
        ax.set_ylabel('Quoted USD');ax.legend(fontsize=9,ncol=3);ax.grid(alpha=.15)
    axs[-1].set_xlim(115,0);axs[-1].set_xlabel('Days before departure → approaching departure')
    fig.suptitle('Individual histories: prices can move in both directions\nLines stop at the last observation; no interpolation beyond that window',fontsize=14)
    savefig(fig,'01-trajectories')
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for ax,rows,title in [(axs[0],overall,'By exact calendar-day horizon'),(axs[1],routes,'Seven-day changes by route')]:
        y=np.arange(len(rows));left=np.zeros(len(rows))
        for key,color,label in [('trip_down','#287b8e','Fall'),('trip_unchanged','#c9d1dc','Unchanged'),('trip_up','#d97643','Rise')]:
            values=np.array([r[key]*100 for r in rows]);ax.barh(y,values,left=left,color=color,label=label)
            for i,v in enumerate(values):
                if v>8: ax.text(left[i]+v/2,i,f'{v:.1f}%',ha='center',va='center',fontsize=9)
            left+=values
        ax.set_yticks(y,[f"{r['label']} | {r['trips']} trips\n{r['pairs']:,} pairs" for r in rows]);ax.set_xlim(0,100)
        ax.set_xlabel('Equal-trip average frequency (%)');ax.set_title(title,loc='left');ax.invert_yaxis()
    axs[0].legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.18))
    fig.suptitle('Observed fare changes | each trip receives equal weight',fontsize=14)
    savefig(fig,'02-directions')
    fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    x=np.arange(len(leads))
    for ax,key,cikey,title in [(axs[0,0],'trip_up','up_trip_ci','Observed seven-day rise frequency'),(axs[0,1],'mean_usd','usd_trip_ci','Mean seven-day dollar change')]:
        scale=100 if key=='trip_up' else 1
        vals=np.array([r[key]*scale for r in leads]);ci=np.array([r[cikey] for r in leads])*scale
        ax.errorbar(x,vals,yerr=np.array([vals-ci[:,0],ci[:,1]-vals]),fmt='o',capsize=4,color='#287b8e')
        ax.set_xticks(x,[r["label"] for r in leads]);ax.set_title(title,loc='left');ax.grid(axis='y',alpha=.15)
        ax.set_ylabel('%' if key=='trip_up' else 'USD');ax.axhline(0,color='#aaaaaa',linewidth=.6)
    axs[1,0].bar(x,[r['trips'] for r in leads],color='#a6bcc6')
    for i,r in enumerate(leads):axs[1,0].text(i,r['trips']+2,str(r['trips']),ha='center')
    axs[1,0].set_xticks(x,[r["label"] for r in leads]);axs[1,0].set_ylim(0,190);axs[1,0].set_ylabel('Eligible trips');axs[1,0].set_xlabel('Starting days before departure')
    pertrip=d.groupby(['search_id','destination','lead_bucket'],observed=True).price.mean().reset_index()
    for route,color in COLORS.items():
        r=pertrip[pertrip.destination==route].groupby('lead_bucket',observed=True).price.median().reindex(BUCKETS)
        axs[1,1].plot(np.arange(len(BUCKETS)),r.values,marker='o',label=route,color=color)
    axs[1,1].set_xticks(np.arange(len(BUCKETS)),BUCKETS);axs[1,1].set_ylabel('Median of trip mean prices (USD)');axs[1,1].set_xlabel('Days before departure');axs[1,1].legend()
    fig.suptitle('Lead-time associations | changing trip/calendar composition\n95% trip-bootstrap intervals are conditional sample summaries, not causal effects',fontsize=13)
    savefig(fig,'03-lead-time')
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained',sharey=True)
    for ax,field,title in zip(axs,weekday,['Departure weekday','Observation weekday']):
        raw={r['label']:r for r in weekday[field]['raw']};std=weekday[field]['standardized']
        ax.plot(range(7),[100*raw[w]['trip_up'] for w in DAYS],marker='o',label='Unadjusted equal-trip')
        if std['rates']:ax.plot(range(7),[100*std['rates'][w] for w in DAYS],marker='s',label='Common route/lead cells')
        ax.set_xticks(range(7),[w[:3] for w in DAYS]);ax.set_title(f"{title}\n{std['common_cells']} common cells",loc='left')
        ax.grid(alpha=.15);ax.legend(fontsize=8);ax.set_ylabel('Seven-day rise frequency (%)')
    fig.suptitle('Weekday exploration: associations, not advice about when to buy\nRoute/lead reweighting changes the population; holidays and shared calendar shocks remain',fontsize=13)
    savefig(fig,'04-weekdays')
    fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    bins=np.arange(0,121,10)
    axs[0].hist(minima.earliest_tied_lead,bins=bins,alpha=.65,label='Earliest tied minimum',color='#287b8e')
    axs[0].hist(minima.latest_tied_lead,bins=bins,alpha=.55,label='Latest tied minimum',color='#e19035')
    axs[0].set_xlabel('Days before departure');axs[0].set_ylabel('Trip histories');axs[0].legend(fontsize=9)
    axs[1].scatter(minima.final_lead,minima.earliest_tied_lead,s=19,alpha=.5,color='#7257a4')
    axs[1].plot([0,60],[0,60],linestyle='--',color='#999999');axs[1].set_xlabel('Last observed lead time (days)');axs[1].set_ylabel('Earliest tied minimum lead (days)')
    fig.suptitle('Lowest observed within available windows—not an optimal booking time\nTies and different stopping points prevent a single best-day recommendation',fontsize=13)
    savefig(fig,'05-minima')
    write_report(results)
    print(json.dumps(dict(trips=results['trips'],observations=len(d),overall=overall,routes=routes,
                          minima=results['minimum_summary'],extremes=results['extrema']),indent=2))


def write_report(r):
    def pct(x):return f'{100*x:.1f}%'
    def ci(x,scale=1):return f'{scale*x[0]:.1f} to {scale*x[1]:.1f}' if None not in x else 'not estimated'
    lines=['# How sampled BWI fares changed as departure approached',
        '', 'First descriptive report · frozen October 30, 2026 dataset · prepared October 31, 2026', '',
        '**Scope:** 167 usable route/departure histories from 168 planned queries; 10,282 daily prices. '
        'Three BWI routes, departures October 31–December 25. One MCO history (December 21) is missing. '
        'All findings concern this selected provider dataset and its available windows. No live booking advice.', '',
        '## Exact-horizon changes', '',
        'Each trip receives equal weight within a summary. Percent change uses the starting price. '
        'Pairs require an actual observation exactly 1, 3, or 7 calendar dates later; none were interpolated.', '',
        '| Horizon | Trips / pairs | Rise | Fall | Unchanged | Mean $ change | Mean % change |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for x in r['overall']:
        lines.append(f"| {x['label']} days | {x['trips']} / {x['pairs']:,} | {pct(x['trip_up'])} | {pct(x['trip_down'])} | {pct(x['trip_unchanged'])} | {x['mean_usd']:+.2f} | {x['mean_pct']:+.1f}% |")
    lines+=['','![Observed change directions](02-directions.png)','','## Route differences over seven days','',
        '| Route | Trips / pairs | Rise | Fall | Mean $ change | 95% trip-bootstrap range for mean $ |',
        '| --- | ---: | ---: | ---: | ---: | --- |']
    for x in r['routes_7d']:
        lines.append(f"| BWI–{x['label']} | {x['trips']} / {x['pairs']:,} | {pct(x['trip_up'])} | {pct(x['trip_down'])} | {x['mean_usd']:+.2f} | {ci(x['usd_trip_ci'])} |")
    lines+=['','These are descriptive route differences with balanced planned departure dates. They are not causal route effects. '
        'Price levels, holiday demand and shared calendar shocks can differ.','',
        '## Individual trajectories and lead time','','![Selected trajectories](01-trajectories.png)','',
        'Examples use November 6, November 28 and December 18 for each route, fixed before viewing their outcomes. '
        'Lines connect genuine daily observations; they stop at retrieval. No future values are shown.','',
        '![Lead-time patterns and counts](03-lead-time.png)','',
        '| Starting lead days | Eligible trips / seven-day pairs | Rise | Mean $ change | Mean % change |',
        '| --- | ---: | ---: | ---: | ---: |']
    for x in r['lead_7d']:
        lines.append(f"| {x['label']} | {x['trips']} / {x['pairs']:,} | {pct(x['trip_up'])} | {x['mean_usd']:+.2f} | {x['mean_pct']:+.1f}% |")
    lines+=['','The near-departure bins contain far fewer trips. Lead time and observation/departure calendar dates are linked. '
        'Raw prices across lead bins therefore do not trace one comparable cohort moving toward departure.','',
        '## Magnitudes and uncertainty','','| Horizon | Median observed $ change | 10th–90th percentile $ | Mean increase when up | Mean decrease when down |',
        '| --- | ---: | --- | ---: | ---: |']
    for x in r['overall']:
        lines.append(f"| {x['label']} days | {x['row_median_usd']:+.2f} | {x['row_p10_usd']:+.0f} to {x['row_p90_usd']:+.0f} | {x['mean_increase_usd']:+.2f} | {x['mean_decrease_usd']:+.2f} |")
    lines+=['','This magnitude table is observation-weighted and describes the pooled pair distribution. '
        'Conditional means are only among rises/falls. It is not a prediction interval.','',
        '| Horizon | Rise: trip bootstrap 95% | Rise: departure-week block sensitivity 95% | Raw-row rise frequency |',
        '| --- | --- | --- | ---: |']
    for x in r['overall']:
        lines.append(f"| {x['label']} days | {ci(x['up_trip_ci'],100)}% | {ci(x['up_week_ci'],100)}% | {pct(x['row_up'])} |")
    lines+=['','Bootstrap seed 20261031; 2,000 draws. Whole trips are resampled within route, keeping their observations together. '
        'Sensitivity resamples whole departure-week blocks across routes (only eight blocks). Neither fully handles common observation-date market shocks. '
        'These are conditional resampling ranges, not confidence that findings generalize to all air travel. No row-wise independent-binomial intervals or significance claims are used.','',
        '## Weekdays and holidays','','![Weekday associations](04-weekdays.png)','',
        'Departure weekday and observation weekday are analyzed separately. The second line reweights common route/lead-time cells '
        'with at least three distinct trips for every weekday; its population differs from the unadjusted line. '
        'This is partial descriptive adjustment, not a causal model or complete calendar control. '
        'The current snapshot is too narrow to recommend buying on a particular weekday.','',
        '| Predeclared departure windows | Trips / pairs | Seven-day rise | Mean $ change |',
        '| --- | ---: | ---: | ---: |']
    for x in r['holiday_7d']:
        lines.append(f"| {x['label']} | {x['trips']} / {x['pairs']:,} | {pct(x['trip_up'])} | {x['mean_usd']:+.2f} |")
    lines+=['','Holiday labels: Veterans Day ±3 days, Thanksgiving ±7, Christmas ±7. The available departures stop at Christmas. '
        'This comparison is not route/lead/calendar adjusted and cannot isolate a holiday effect.','',
        '## Lowest observed fares and quality','','![Observed minima and ties](05-minima.png)','',
        f"Of {r['trips']} trips, {r['minimum_summary']['multiple_tied_days']} have their lowest fare tied across multiple dates. "
        f"The minimum includes the first observed date for {r['minimum_summary']['includes_first']} trips and the last for {r['minimum_summary']['includes_last']}. "
        'The histogram shows both ends of each minimum’s tie range. These are retrospective minima within available windows, not optimal booking times.','',
        f"There are {r['extrema']['flagged_daily_jumps']} daily jumps exceeding a twofold increase or falling below half the prior price, "
        f"across {r['extrema']['affected_trips']} trips. All are retained; `flagged-jumps.csv` lists them for review. "
        'Dropping entire affected trips is available only as a sensitivity result in `results.json`, not a cleaning rule.','',
        f"UTC and Baltimore observation dates differ for {r['timezone_date_differences']} of 10,282 rows, so those two conventions yield the same weekday labels in this sample. "
        'That does not establish the provider’s timezone semantics elsewhere. Structurally usable histories have no internal missing days; '
        'the one unavailable trip remains missing. Historical filter semantics and taxes/fare comparability remain provisional.','',
        '## Modeling decision and pending refresh','','**Defer predictive modeling for now.** This report is exploratory and does not claim an untouched test set. '
        'Historical revision stability and point-in-time availability remain unresolved, and the sample covers one shared observation season. '
        'Reserve a future evaluation period before model selection. Compare zero-change and training-only majority/route-lead baselines before fitting a modest model. '
        'The no-change baseline errors in the JSON are in-sample descriptive benchmarks, not validated forecasts. No strategy is evaluated against future-known minima.','',
        'Three refreshes are prepared in `config/refresh-three.json` for ATL November 6, MCO November 20 and DEN December 4. '
        'They were not due at report generation; all become eligible by 12:48 PM Eastern on October 31. '
        'No refresh was executed or scheduled automatically. Freeze v1 will remain unchanged when refreshed snapshots arrive.','',
        '## Reproduce and reuse','','Run `.venv/bin/python -m flights.analyze` from the project root after installing `requirements-analysis.lock.txt`. '
        'Inputs are verified against SHA-256 checksums in `data/frozen/2026-10-30-v1/manifest.json`, including referenced raw responses. '
        'Figures, numerical summaries and minima/jump tables are saved alongside this report. '
        'All artifacts remain local and ignored pending clarification of public display/redistribution permissions. No API calls occur during analysis.','']
    (OUT/'report.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    run()
