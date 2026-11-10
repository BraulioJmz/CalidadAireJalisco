import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
const get = name => JSON.parse(fs.readFileSync(new URL(name, import.meta.url), 'utf8'));
const source = fs.readFileSync(new URL('../lib/academia.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.ES2022,target:ts.ScriptTarget.ES2022}}).outputText;
const lib = await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const summary = get('../data/academia.json'); lib.validateSummary(summary);
assert.equal(summary.years[0],2015); assert.equal(summary.years.at(-1),2024);
assert.equal(summary.categories[0].code,0); assert.equal(lib.fmt(0),'0.00');
assert.equal(lib.shiftHour('2024-02-28T23:00:00',1),'2024-02-29T00:00:00');
assert.equal(lib.shiftHour('2023-02-28T23:00:00',1),'2023-03-01T00:00:00');
assert.equal(lib.shiftHour('2023-12-31T23:00:00',1),'2024-01-01T00:00:00');
assert.deepEqual(lib.mergeHours([{time:['2024-01-01T00:00:00','2024-01-01T02:00:00'],values:{PM10:[0,12]}}],lib.hourGrid('2024-01-01T00:00:00','2024-01-01T02:00:00'),'PM10'),[0,null,12]);
assert.deepEqual(lib.chunkUrls('2023-12-31T23:00:00','2024-01-01T03:00:00'),['/datos/sprint-3/horas/2023-12.json','/datos/sprint-3/horas/2024-01.json']);
for(const change of [d=>d.schema='bad',d=>d.model.n=0,d=>d.categories[0].code=1,d=>d.model.threshold=60]) { const d=structuredClone(summary); change(d); assert.throws(()=>lib.validateSummary(d)); }
let days=0,origins=0,targets=0;
for(let y=2015;y<=2024;y++) for(let m=1;m<=12;m++) {
  const mm=String(m).padStart(2,'0'); const rows=get(`../public/datos/sprint-3/calendario/${y}-${mm}.json`);
  assert.equal(rows.length,new Date(Date.UTC(y,m,0)).getUTCDate()); days+=rows.length;
  if(y===2023&&m===1) assert(rows.every(r=>r.pollutants.O3.category===null));
  if([2023,2024].includes(y)&&m===12) { assert(rows.every(r=>r.pollutants.CO.category===0));assert.equal(rows.filter(r=>r.pollutants.PM10.category>=2&&r.pollutants.PM10.category!==null).length,y===2023?15:27); }
}
assert.equal(days,3653);
for(let month=1;month<=12;month++) {
  const rows=get(`../public/datos/sprint-3/predicciones/2024-${String(month).padStart(2,'0')}.json`);
  origins+=rows.length;
  for(const row of rows) for(let j=0;j<3;j++) {
    assert.equal(row.target[j],lib.shiftHour(row.origin,j+1));targets++;
    for(const model of ['HGB','persistencia','diaria']) assert(Math.abs((row.models[model].predicted[j]-row.observed[j])-row.models[model].error[j])<1e-10);
  }
}
assert.equal(origins,6225);assert.equal(targets,18675);
assert(summary.downloads.every(d=>d.url.startsWith('/descargas/sprint-3/')));
assert(fs.statSync(new URL('../data/academia.json',import.meta.url)).size<30000);
console.log(JSON.stringify({contrato:summary.schema,dias:days,origenes:origins,horizontes:targets,mutaciones_rechazadas:4,ceros_huecos_fechas_y_metricas:'correctos'}));
