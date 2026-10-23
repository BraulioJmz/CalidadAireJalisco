import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
const source=fs.readFileSync(new URL('../lib/sprint2-contract.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText;
const {assertSprint2}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const data=JSON.parse(fs.readFileSync(new URL('../data/sprint2.json',import.meta.url),'utf8'));
assertSprint2(data);
for(const change of [
  d=>{d.pollutants[0].unit='ppm'},
  d=>{d.periods[0].counts[0]+=1},
  d=>{d.profiles.pop()},
  d=>{d.periods.find(r=>r.valid===0).mean=0},
  d=>{d.daily.pop()},
  d=>{d.daily[0].date='2023-02-29'},
  d=>{d.daily[0].pollutants.O3.category=0},
  d=>{d.daily[0].pollutants.CO.readings=25},
  d=>{d.daily[0].weather.RH={value:0,readings:0}},
  d=>{d.dailyStatistics.CO.unit='µg/m³'},
  d=>{d.daily.find(r=>r.date==='2023-12-01').pollutants.CO.category=1},
]) {
  const wrong=structuredClone(data);change(wrong);assert.throws(()=>assertSprint2(wrong));
}
console.log(JSON.stringify({contrato:'mir-s2-v2',dimensiones:'correctas',mutaciones_rechazadas:11}));
await import('./validar-calendario.mjs');
