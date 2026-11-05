export const dayNumber = value => Math.round(Date.parse(`${value}T00:00:00Z`)/86400000);
// Display only: internal dates remain ISO for sorting and exact horizon matching.
export const displayDate = value => {const [year,month,day]=value.slice(0,10).split('-');return `${month}-${day}-${year}`;};
export const laterDate = (value, horizon) => new Date((dayNumber(value)+horizon)*86400000).toISOString().slice(0,10);
export const leadLabels = ['1–7','8–14','15–30','31–60','61–90','91+'];
export function leadBucket(lead) {return leadLabels[[7,14,30,60,90,Infinity].findIndex(end => lead<=end)];}
export function pairs(trip, horizon) {
  if (![1,3,7].includes(horizon)) throw new Error('Unsupported horizon');
  const index = new Map(trip.points.map(p=>[p[0],p]));
  if (index.size !== trip.points.length) throw new Error('Duplicate observation date');
  return trip.points.flatMap(p=>{
    const end=index.get(laterDate(p[0],horizon));
    if (!end || p[1]<=0 || end[1]<=0) return [];
    return [{date:p[0],end:end[0],lead:p[2],price:p[1],future:end[1],usd:end[1]-p[1],pct:100*(end[1]-p[1])/p[1]}];
  });
}
export function summarize(trips,horizon,predicate=()=>true) {
  const groups=trips.map(t=>pairs(t,horizon).filter(predicate)).filter(p=>p.length);
  if (!groups.length) return null;
  const mean=f=>groups.reduce((a,g)=>a+g.reduce((s,p)=>s+f(p),0)/g.length,0)/groups.length;
  return {trips:groups.length,pairs:groups.reduce((a,g)=>a+g.length,0),up:mean(p=>+(p.usd>0)),
    down:mean(p=>+(p.usd<0)),flat:mean(p=>+(p.usd===0)),usd:mean(p=>p.usd),pct:mean(p=>p.pct)};
}
export function segments(points) {
  const groups=[];
  for (const p of points) {
    const prev=groups.at(-1)?.at(-1);
    if (!prev || dayNumber(p[0])-dayNumber(prev[0])!==1) groups.push([]);
    groups.at(-1).push(p);
  }
  return groups;
}

// One exact starting lead and one exact endpoint per trip: a comparable waiting scenario.
export function waitingScenario(trips, lead, horizon) {
  const observations=trips.flatMap(t=>pairs(t,horizon).filter(p=>p.lead===lead));
  if(!observations.length)return null;
  const changes=observations.map(p=>p.usd).sort((a,b)=>a-b);
  const median=values=>{const v=[...values].sort((a,b)=>a-b),m=Math.floor(v.length/2);return v.length?(v.length%2?v[m]:(v[m-1]+v[m])/2):null;};
  const rises=changes.filter(x=>x>0),falls=changes.filter(x=>x<0);
  return {trips:changes.length,up:rises.length/changes.length,down:falls.length/changes.length,
    flat:changes.filter(x=>x===0).length/changes.length,
    median:median(changes),mean:changes.reduce((a,b)=>a+b,0)/changes.length,
    medianExtra:rises.length?median(rises):null,medianSaving:falls.length?-median(falls):null,
    medianPercent:median(observations.map(p=>p.pct)),rises:rises.length,falls:falls.length};
}
