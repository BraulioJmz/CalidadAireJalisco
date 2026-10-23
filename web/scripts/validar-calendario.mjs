import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
const source=fs.readFileSync(new URL('../lib/calendar.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText;
const {monthLength,monthStart,isoDate,timelineLength,timelineReducer}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
assert.equal(monthLength(2023,2),28);assert.equal(monthLength(2024,2),29);
assert.equal(isoDate(2023,2,29),null);assert.equal(isoDate(2024,2,29),'2024-02-29');
assert.equal(monthStart(2023,2),2);assert.equal(monthStart(2024,2),3);
assert.equal(timelineLength([2023],2),28);assert.equal(timelineLength([2023,2024],2),29);
for(const last of [28,29,30,31]) {
  let state={day:1,playing:false};
  assert.deepEqual(timelineReducer(state,{type:'tick'},last),state);
  state=timelineReducer(state,{type:'play'},last);
  const visited=[state.day];
  while(state.playing) {state=timelineReducer(state,{type:'tick'},last);visited.push(state.day);}
  assert.deepEqual(visited,Array.from({length:last},(_,i)=>i+1));
  assert.deepEqual(state,{day:last,playing:false});
  assert.equal(timelineReducer(state,{type:'play'},last).playing,false);
  assert.deepEqual(timelineReducer(state,{type:'restart',autoplay:true},last),{day:1,playing:true});
  assert.deepEqual(timelineReducer(state,{type:'restart',autoplay:false},last),{day:1,playing:false});
  state=timelineReducer(state,{type:'step',offset:-1},last);
  assert.deepEqual(state,{day:last-1,playing:false});
  state=timelineReducer(state,{type:'play'},last);
  assert.equal(timelineReducer(state,{type:'pause'},last).playing,false);
  assert.deepEqual(timelineReducer(state,{type:'select',day:1},last),{day:1,playing:false});
  assert.deepEqual(timelineReducer({day:1,playing:false},{type:'step',offset:-1},last),{day:1,playing:false});
}
console.log(JSON.stringify({calendario:'APROBADO',casos:'fechas reales, febrero, pausa, selección, pasos y final de meses de 28/29/30/31 días'}));
