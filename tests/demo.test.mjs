import test from 'node:test';
import assert from 'node:assert/strict';
import {pairs,summarize,segments,laterDate,waitingScenario} from '../demo/core.mjs';

test('calendar horizon crosses DST and never substitutes the next date',()=>{
  assert.equal(laterDate('2026-10-31',7),'2026-11-07');
  const trip={points:[['2026-10-31',100,10],['2026-11-08',120,2]]};
  assert.deepEqual(pairs(trip,7),[]);
});
test('unequal history lengths receive equal trip weight',()=>{
  const a={points:[['2026-11-01',100,10],['2026-11-02',110,9],['2026-11-03',120,8]]};
  const b={points:[['2026-11-01',100,10],['2026-11-02',90,9]]};
  const r=summarize([a,b],1);
  assert.equal(r.up,.5);assert.equal(r.down,.5);assert.equal(r.usd,0);assert.equal(r.pairs,3);
});
test('missing histories stay missing and gaps break the chart',()=>{
  assert.equal(summarize([{points:[]}],7),null);
  assert.equal(segments([['2026-11-01',100,10],['2026-11-03',100,8]]).length,2);
});
test('duplicate dates rejected; unchanged price is a real outcome',()=>{
  assert.throws(()=>pairs({points:[['2026-11-01',100,10],['2026-11-01',90,10]]},1));
  const r=summarize([{points:[['2026-11-01',100,10],['2026-11-08',100,3]]}],7);
  assert.equal(r.flat,1);assert.equal(r.usd,0);
});
test('waiting scenario uses one exact pair per trip and conditional medians',()=>{
  const trips=[120,80,100,160].map(end=>({points:[['2026-11-01',100,14],['2026-11-02',1000,13],['2026-11-08',end,7]]}));
  const s=waitingScenario(trips,14,7);
  assert.equal(s.trips,4);assert.equal(s.up,.5);assert.equal(s.down,.25);assert.equal(s.flat,.25);
  assert.equal(s.medianExtra,40);assert.equal(s.medianSaving,20);assert.equal(s.median,10);
  assert.equal(waitingScenario(trips,21,7),null);
});
test('waiting with no increases does not invent an extra cost',()=>{
  const s=waitingScenario([{points:[['2026-11-01',100,14],['2026-11-08',90,7]]}],14,7);
  assert.equal(s.medianExtra,null);assert.equal(s.medianSaving,10);
});
