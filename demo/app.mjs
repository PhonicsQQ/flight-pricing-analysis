import {pairs,summarize,leadBucket,leadLabels,laterDate,segments,waitingScenario,displayDate} from './core.mjs';
const $=id=>document.getElementById(id);
const fmt=new Intl.NumberFormat('en-US');
const usd=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(n);
const signed=n=>(n>0?'+':'')+usd(n);
const pct=n=>(100*n).toFixed(1)+'%';
const text=(id,value)=>$(id).textContent=value;
function row(target,values) {const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.append(td);}$(target).append(tr);}
function option(select,value,label){const op=document.createElement('option');op.value=value;op.textContent=label;select.append(op);}
let data;
function traveler(){
  const route=$('traveler-route').value,lead=+$('start-lead').value,h=+$('wait-days').value;
  const trips=data.trips.filter(t=>route==='ALL'||t.route===route),s=waitingScenario(trips,lead,h);
  text('scenario-title',`Buy ${lead} days out, or wait until ${lead-h} days out?`);
  text('scenario-count',s?`${s.trips} of ${trips.length} trips eligible${s.trips<30?' · small sample':''}`:'No eligible trips in the available histories.');
  $('scenario-empty').hidden=!!s;$('scenario-results').hidden=!s;
  if(s){
    $('scenario-cards').replaceChildren();
    for(const [label,value,note] of [
      ['Waiting cost more',pct(s.up),`${s.rises} of ${s.trips} trips`],
      ['Extra cost when it rose',s.medianExtra===null?'—':usd(s.medianExtra),'Median increase'],
      ['Waiting saved money',pct(s.down),`${s.falls} of ${s.trips} trips`],
      ['Savings when it fell',s.medianSaving===null?'—':usd(s.medianSaving),'Median saving']]){
      const card=document.createElement('article'),title=document.createElement('h4'),valueEl=document.createElement('strong'),caption=document.createElement('p');
      title.textContent=label;valueEl.textContent=value;caption.textContent=note;card.append(title,valueEl,caption);$('scenario-cards').append(card);
    }
    $('outcome-bar').replaceChildren();const ns='http://www.w3.org/2000/svg',bar=document.createElementNS(ns,'svg');bar.setAttribute('viewBox','0 0 1000 26');bar.setAttribute('aria-hidden','true');let left=0;
    for(const [fraction,color] of [[s.down,'#50766d'],[s.flat,'#d9dcdf'],[s.up,'#9a6443']]){const rect=document.createElementNS(ns,'rect');for(const [k,v] of Object.entries({x:left,y:0,width:fraction*1000,height:26,fill:color}))rect.setAttribute(k,v);bar.append(rect);left+=fraction*1000;}
    $('outcome-bar').append(bar);$('outcome-bar').setAttribute('aria-label',`${pct(s.down)} cost less, ${pct(s.flat)} unchanged, ${pct(s.up)} cost more`);
    text('outcome-legend',`${pct(s.down)} cost less · ${pct(s.flat)} unchanged · ${pct(s.up)} cost more`);
    text('scenario-bottomline',`Median change: ${signed(s.median)} (${s.medianPercent>0?'+':''}${s.medianPercent.toFixed(1)}%) · Average: ${signed(s.mean)}`);
  }
  text('timing-caption',`What followed a ${h}-day wait, ${route==='ALL'?'across the three sampled BWI routes':'on BWI–'+route}.`);
  $('timing-rows').replaceChildren();
  for(const start of [60,45,30,21,14,7]){const v=waitingScenario(trips,start,h);row('timing-rows',[`${start} → ${start-h} days out`,v?v.trips:0,v?pct(v.up):'—',v?pct(v.down):'—',v?signed(v.mean):'—']);}
  $('mean-audit-rows').replaceChildren();
  for(const a of (data.mean_audit||[]).filter(a=>a.route===route&&a.horizon===h)){
    row('mean-audit-rows',[`${a.lead} days`,a.trips,a.trips?signed(a.mean):'—',a.without_largest==null?'—':signed(a.without_largest),a.without_largest_10pct==null?'—':signed(a.without_largest_10pct),!a.trips?'No data':a.small_sample?'Under 10 trips':a.sign_can_flip?'One trip can flip the sign':'No single-trip sign flip']);
  }
}
function selectedTrip(){return data.trips.find(t=>t.route===$('route').value && t.departure===$('departure').value);}
function dates(){const old=$('departure').value;$('departure').replaceChildren();data.trips.filter(t=>t.route===$('route').value).forEach(t=>option($('departure'),t.departure,displayDate(t.departure)+(t.points.length?'':' · history missing')));$('departure').value=old||'2026-11-06';trip();}
function svg(tag,attrs,textValue){const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);if(textValue!==undefined)node.textContent=textValue;$('chart').append(node);return node;}
function chart(t){
  $('chart').replaceChildren();svg('title',{id:'chart-title'},`BWI to ${t.route}, departure ${displayDate(t.departure)}`);svg('desc',{id:'chart-desc'},`${t.points.length} actual daily prices. The accessible data table follows. Lines break at missing dates.`);
  const prices=t.points.map(p=>p[1]),min=Math.max(0,Math.min(...prices)*.9),max=Math.max(...prices)*1.12;
  const first=t.points[0][2],last=t.points.at(-1)[2];
  const x=p=>60+(first-p[2])/Math.max(1,first-last)*710,y=p=>250-(p[1]-min)/(max-min||1)*220;
  for(let i=0;i<=4;i++){const value=min+(max-min)*i/4,yy=250-i*55;svg('line',{x1:60,x2:770,y1:yy,y2:yy,stroke:'#e5e5e7'});svg('text',{x:48,y:yy+4,'text-anchor':'end'},'$'+Math.round(value));}
  for(let i=0;i<=4;i++){const xx=60+i*177.5;svg('text',{x:xx,y:280,'text-anchor':'middle'},Math.round(first-(first-last)*i/4));}
  for(const group of segments(t.points))svg('polyline',{points:group.map(p=>`${x(p)},${y(p)}`).join(' '),fill:'none',stroke:'#242426','stroke-width':2.5,'stroke-linejoin':'round'});
  for(const p of t.points){const dot=svg('circle',{cx:x(p),cy:y(p),r:3,fill:'#242426'});const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=`${displayDate(p[0])} · ${p[2]} days before departure · ${usd(p[1])}`;dot.append(title);}
}
function inspection(){const t=selectedTrip(),p=t.points.find(p=>p[0]===$('observation').value);text('selected-price',`${displayDate(p[0])} · ${p[2]} days before departure · ${usd(p[1])}`);text('outcome','Outcome hidden.');$('reveal').disabled=false;}
function trip(){
  const t=selectedTrip(),h=+$('horizon').value; text('trip-title',`BWI → ${t.route} · ${displayDate(t.departure)}`);
  const exists=t.points.length>0;$('missing').hidden=exists;$('trip-content').hidden=!exists;
  text('coverage',`Retrieved ${displayDate(t.retrieved)} · ${exists?t.points.length+' observed dates':'history unavailable'}`);
  if(!exists)return;
  const first=t.points[0],last=t.points.at(-1),min=Math.min(...t.points.map(p=>p[1])),ties=t.points.filter(p=>p[1]===min),changes=pairs(t,h);
  text('coverage',`${displayDate(first[0])} to ${displayDate(last[0])} · ${t.points.length} observed dates · stops ${last[2]} days before departure`);
  chart(t);$('trip-metrics').replaceChildren();
  for(const [label,value] of [['Lowest observed',usd(min)],['Days tied at minimum',String(ties.length)],['Exact '+h+'-day pairs',String(changes.length)]]){const el=document.createElement('div');const strong=document.createElement('strong');strong.textContent=value;const span=document.createElement('span');span.textContent=label;el.append(strong,span);$('trip-metrics').append(el);}
  text('minimum-dates',`Minimum dates: ${displayDate(ties[0][0])} to ${displayDate(ties.at(-1)[0])} · ${ties[0][2]}–${ties.at(-1)[2]} days out · nonconsecutive ties possible`);
  const chosen=$('observation').value;$('observation').replaceChildren();t.points.forEach(p=>option($('observation'),p[0],`${displayDate(p[0])} · ${p[2]} days before departure`));$('observation').value=t.points.some(p=>p[0]===chosen)?chosen:t.points[Math.max(0,t.points.length-h-1)][0];inspection();
  $('observations').replaceChildren();const index=new Map(changes.map(p=>[p.date,p]));for(const p of t.points){const c=index.get(p[0]);row('observations',[displayDate(p[0]),p[2],usd(p[1]),displayDate(laterDate(p[0],h)),c?`${signed(c.usd)} (${c.pct>0?'+':''}${c.pct.toFixed(1)}%)`:'No exact observation']);}
}
function summaries(){
  const h=+$('summary-horizon').value,s=summarize(data.trips,h);$('directions').replaceChildren();
  for(const [label,value] of [['Rose',pct(s.up)],['Fell',pct(s.down)],['Unchanged',pct(s.flat)],['Mean dollar change',signed(s.usd)]]){const card=document.createElement('div');const strong=document.createElement('strong');strong.textContent=value;const span=document.createElement('span');span.textContent=label;card.append(strong,span);$('directions').append(card);}
  text('summary-counts',`${s.trips} eligible histories · ${fmt.format(s.pairs)} exact ${h}-day pairs · equal weight per trip · mean percentage change ${s.pct>0?'+':''}${s.pct.toFixed(1)}%`);
  for(const id of ['routes','leads'])$(id).replaceChildren();
  const add=(id,label,r)=>row(id,[label,r?`${r.trips} / ${fmt.format(r.pairs)}`:'0 / 0',r?pct(r.up):'—',r?signed(r.usd):'—']);
  for(const route of ['ATL','MCO','DEN'])add('routes','BWI–'+route,summarize(data.trips.filter(t=>t.route===route),h));
  for(const b of leadLabels)add('leads',b,summarize(data.trips,h,p=>leadBucket(p.lead)===b));
  const a=data.results.overall.find(r=>+r.label===h);
  text('uncertainty',`Rise frequency: 95% trip-bootstrap range ${pct(a.up_trip_ci[0])}–${pct(a.up_trip_ci[1])}. Departure-week block sensitivity: ${pct(a.up_week_ci[0])}–${pct(a.up_week_ci[1])}. 2,000 resamples; only eight departure-week blocks. These ranges do not establish population-wide confidence.`);
}
function otherSections(){
  if(data.sensitivity){const s=data.sensitivity;text('sensitivity',`Same-trip sensitivity (seven days): among the same ${s.trips} trips, rises occurred ${pct(s.near.trip_up)} of the time starting 8–14 days before departure (${s.near.pairs} pairs), versus ${pct(s.far.trip_up)} at 31–60 days (${s.far.pairs} pairs). This exploratory comparison still mixes different observation calendar dates; it is not a causal effect of waiting.`);}
  const weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];const w=data.results.weekdays_7d;
  for(const day of weekdays)row('weekdays',[day,...['departure_weekday','observation_weekday'].map(field=>w[field].standardized.rates[day]===undefined?'Insufficient common cells':pct(w[field].standardized.rates[day]))]);
  text('weekday-note',`At least three trips per weekday/cell. Common route/lead cells: ${w.departure_weekday.standardized.common_cells} for departure weekdays and ${w.observation_weekday.standardized.common_cells} for observation weekdays. Results describe a different eligible population from the unadjusted summaries.`);
  for(const r of data.refreshes){const last=r.added.at(-1);row('refreshes',[`BWI–${r.route} · ${displayDate(r.departure)}`,r.overlap,r.revisions.length,r.original_last&&last?`${usd(r.original_last[1])} → ${usd(last[1])}`:'Unavailable']);}
}
$('route').addEventListener('change',dates);$('departure').addEventListener('change',trip);$('horizon').addEventListener('change',trip);$('observation').addEventListener('change',inspection);$('summary-horizon').addEventListener('change',summaries);
for(const id of ['traveler-route','start-lead','wait-days'])$(id).addEventListener('change',traveler);
document.querySelectorAll('[data-detail-link]').forEach(link=>link.addEventListener('click',()=>{$('deep-dive').open=true;}));
$('reveal').addEventListener('click',()=>{const h=+$('horizon').value,c=pairs(selectedTrip(),h).find(p=>p.date===$('observation').value);text('outcome',c?`${displayDate(c.end)}: ${usd(c.future)}. Change: ${signed(c.usd)} (${c.pct>0?'+':''}${c.pct.toFixed(1)}%).`:`No observation exactly ${h} days later.`);$('reveal').disabled=true;});
try {
  const response=await fetch('./data.json');if(!response.ok)throw new Error('Saved data unavailable');data=await response.json();
  if(!data.trips?.length || !data.results?.overall?.length)throw new Error('Saved dataset is empty or incompatible');
  text('ntrips',fmt.format(data.results.trips));text('nprices',fmt.format(data.results.observations));text('version',displayDate(data.version)+' · v1');
  dates();summaries();otherSections();traveler();$('content').hidden=false;$('loading').hidden=true;
} catch(error){$('loading').hidden=true;$('error').hidden=false;text('error','Unable to load the saved research dataset. Rebuild with python3 -m flights.export_demo and launch python3 -m flights.serve_demo. No sample prices are substituted.');console.error(error);}

for(const link of document.querySelectorAll('nav a'))link.addEventListener('click',()=>{document.querySelectorAll('nav a').forEach(a=>a.removeAttribute('aria-current'));link.setAttribute('aria-current','location');});
