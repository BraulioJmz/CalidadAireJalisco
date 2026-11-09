"use client";
import { useState } from "react";
import type { Coverage, Historical as HistoricalData, Pair, Pollutant, Summary } from "@/lib/academia";
import { fmt, MONTHS } from "@/lib/academia";
import { Categories, LineChart, Loading, MonthOptions, Motion, Panel, Select, Table, useData } from "./Shared";

export function Historical({ summary, pol, initialYear = 0 }: { summary: Summary; pol: Pollutant; initialYear?: number }) {
  const [year, setYear] = useState(initialYear), [mode, setMode] = useState("month"), [all, setAll] = useState(false);
  const result = useData<HistoricalData>(`/datos/sprint-3/historico/${pol.slug}.json`);
  const data = result.data;
  if (!data) return <Loading error={result.error} />;
  const periods = data.periods.filter(r => (year === 0 || r.year === year) && (mode === "year" ? r.month === 0 : r.month > 0));
  const profile = data.profiles.filter(r => r.year === year);
  const categoryYears = data.periods.filter(r => (year === 0 || r.year === year) && r.month === 0);
  return <>
    <Panel id="historico-evolucion" title={`Evolución de ${pol.label}`} question="¿Qué muestran las concentraciones observadas y qué cobertura las sustenta?">
      <div className="am-controls"><Select label="Año del histórico" value={year} change={v => setYear(+v)}><option value={0}>2015–2024</option>{summary.years.map(y => <option key={y}>{y}</option>)}</Select>
        <Select label="Agregación" value={mode} change={setMode}><option value="month">Mensual</option><option value="year">Anual</option></Select>
        <label className="am-check"><input type="checkbox" checked={all} onChange={e => setAll(e.target.checked)} />Mostrar también medias con cobertura insuficiente</label></div>
      <LineChart labels={periods.map(r => mode === "year" ? String(r.year) : `${r.year}-${String(r.month).padStart(2, "0")}`)} unit={pol.unit} title={`Medias ${mode === "year" ? "anuales" : "mensuales"} de concentración horaria observada ${pol.label}`}
        series={[{ name: all ? "Medias observadas · solo descriptivas" : "Medias con criterio de cobertura suficiente", color: "#2c56cf", values: periods.map(r => all || r.sufficient ? r.mean : null), n: periods.map(r => r.n), dash: all }]} />
      <p className="am-note">Media de concentraciones horarias crudas. Mensual: ≥75 % de horas; anual: además ≥75 % en cada trimestre. Son criterios del proyecto. Los huecos de la línea también pueden indicar insuficiencia; la tabla conserva todos los valores observados. No se ajusta una tendencia representativa de toda la década.</p>
      <details><summary>Ver medias, denominadores y suficiencia</summary><Table label="Concentraciones y cobertura"><thead><tr><th>Periodo</th><th>Media ({pol.unit})</th><th>n / esperado</th><th>Cobertura</th><th>Lectura</th></tr></thead><tbody>{periods.map(r => <tr key={`${r.year}-${r.month}`}><th>{r.year}{r.month > 0 && `-${String(r.month).padStart(2, "0")}`}</th><td>{fmt(r.mean, pol.unit === "ppm" ? 4 : 2)}</td><td>{r.n.toLocaleString("es-MX")} / {r.expected.toLocaleString("es-MX")}</td><td>{fmt(r.coverage, 1)} %</td><td>{r.exploratory ? "Exploratorio" : r.sufficient ? "Suficiente según proyecto" : "Solo descriptivo"}</td></tr>)}</tbody></Table></details>
    </Panel>
    <div className="am-grid-2"><Panel id="historico-horas" title="El ritmo de las horas" question="¿Cómo varía la concentración observada dentro del día?">
      <LineChart title={`Perfil horario ${pol.label}`} unit={pol.unit} labels={profile.filter(r => r.kind === "hour").map(r => `${r.bin}:00`)} series={[{ name: `${year || "2015–2024"} · horas observadas`, color: "#2c56cf", values: profile.filter(r => r.kind === "hour").map(r => r.mean), n: profile.filter(r => r.kind === "hour").map(r => r.n) }]} />
      <p className="am-note">Perfil descriptivo. Las observaciones de cada hora pueden proceder de años y temporadas distintos; los n están en los puntos.</p>
    </Panel><Panel title="El ritmo de los meses" question="¿Qué patrón estacional describen las observaciones disponibles?">
      <LineChart title={`Perfil estacional ${pol.label}`} unit={pol.unit} labels={MONTHS.map(m => m.slice(0, 3))} series={[{ name: "Media horaria por mes calendario", color: "#b65327", values: profile.filter(r => r.kind === "season").map(r => r.mean), n: profile.filter(r => r.kind === "season").map(r => r.n) }]} />
      <p className="am-note">No es una comparación pareada. La cobertura desigual y la mezcla de años pueden cambiar el perfil observado.</p>
    </Panel></div>
    <Panel title={`Categorías diarias · ${year || "2015–2024"}`} question="¿Cómo se reparten las categorías y los días sin indicador en cada año?">
      {!pol.categoryApplicable ? <Categories counts={null} expected={0} categories={summary.categories} /> : <>
        <div className="am-category-years">{categoryYears.map(r => <div className="am-year-distribution" data-year={r.year} key={r.year}><h3>{r.year}</h3><div><Categories counts={r.counts} expected={r.days_expected} categories={summary.categories} legend={false} /><p className="am-note">{r.days_valid} / {r.days_expected} días con categoría · {r.days_missing} sin indicador</p></div></div>)}</div>
        <ul className="am-category-legend">{summary.categories.map(c => <li key={c.code}><i style={{background:c.color}} />{c.name}</li>)}<li><i className="am-missing" />Sin indicador</li></ul>
        <details><summary>Ver conteos por año y categoría</summary><Table label="Categorías por año"><thead><tr><th>Año</th>{summary.categories.map(c => <th key={c.code}>{c.name}</th>)}<th>Sin indicador</th><th>Días esperados</th></tr></thead><tbody>{categoryYears.map(r => <tr key={r.year}><th>{r.year}</th>{r.counts?.map((n,i)=><td key={i}>{n}</td>)}<td>{r.days_missing}</td><td>{r.days_expected}</td></tr>)}</tbody></Table></details>
      </>}
      <p className="am-note">{pol.statistic}. Bandas retrospectivas de 2024. Denominador: todos los días de cada año, incluidos los faltantes. Las categorías no se promedian.</p>
    </Panel>
  </>;
}

export function CoverageView({ summary }: { summary: Summary }) {
  const coverage = useData<Coverage[]>("/datos/sprint-3/cobertura.json");
  return <>
    <Panel id="historico-cobertura" title="La disponibilidad forma parte del resultado" question="¿Dónde hay observaciones y dónde están las discontinuidades?">
      {!coverage.data ? <Loading error={coverage.error} /> : <Table label="Cobertura por año y variable"><thead><tr><th>Contaminante · % de horas utilizables</th>{summary.years.map(y => <th key={y}>{y}</th>)}</tr></thead><tbody>{summary.pollutants.map(p => p.key).map(v => <tr key={v}><th>{v}</th>{summary.years.map(y => { const r = coverage.data!.find(r => r.year === y && r.variable === v)!; return <td key={y} style={{ background: r.usable_basic_hours === 0 ? undefined : `color-mix(in srgb, var(--accent) ${Math.round(r.usable_basic_pct * .28)}%, var(--surface))` }} title={`${r.usable_basic_hours}/${r.expected_hours} horas; mayor hueco ${r.max_missing_or_excluded_hours} h${r.warning ? ` · ${r.warning}` : ""}`}>{fmt(r.usable_basic_pct, 1)}</td>; })}</tr>)}</tbody></Table>}
      <p className="am-note">0 % significa ninguna medición utilizable, no concentración cero. SO₂ 2023 se excluye por calibración; el original conserva sus valores. La disponibilidad básica no acredita validez instrumental.</p>
    </Panel>
  </>;
}

export function Comparison({ summary, pol }: { summary: Summary; pol: Pollutant }) {
  const [a, setA] = useState(2023), [b, setB] = useState(2024), [month, setMonth] = useState(12);
  const { data, error } = useData<Pair[]>(`/datos/sprint-3/comparaciones/${a}-${b}.json`);
  const rows = data?.filter(r => r.pollutant === pol.key) ?? [];
  const row = rows.find(r => r.month === month);
  return <Panel id="comparacion-periodos" title="Comparar las mismas fechas" question="¿Qué cambia al observar días equivalentes y qué comparación permite su cobertura?">
    <div className="am-controls"><Select label="Año de referencia" value={a} change={v => { setA(+v); if (+v >= b) setB(+v + 1); }}>{summary.years.filter(y => y < 2024).map(y => <option key={y}>{y}</option>)}</Select><Select label="Año de comparación" value={b} change={v => setB(+v)}>{summary.years.filter(y => y > a).map(y => <option key={y}>{y}</option>)}</Select><Select label="Periodo comparado" value={month} change={v => setMonth(+v)}><MonthOptions all /></Select></div>
    {!row ? <Loading error={error} /> : <>
      <Motion signal={`${a}|${b}|${month}|${pol.key}`} preset="detail" className="am-kpis"><div className="am-kpi"><span>{a} · media de bases diarias</span><b>{fmt(row.a, pol.unit === "ppm" ? 4 : 2)}</b><small>{pol.unit}</small></div><div className="am-kpi"><span>{b} · media de bases diarias</span><b>{fmt(row.b, pol.unit === "ppm" ? 4 : 2)}</b><small>{pol.unit}</small></div><div className="am-kpi"><span>Pares observados</span><b>{row.n} / {row.expected}</b><small>{row.sufficient ? "Cobertura suficiente según proyecto" : "Solo descriptivo; comparación insuficiente"}</small></div></Motion>
      <p className="am-callout">{row.sufficient ? `Cambio pareado: ${fmt(row.change_pct, 1)} %; diferencia ${fmt(row.delta, pol.unit === "ppm" ? 4 : 2)} ${pol.unit}. Persisten sesgos residuales.` : "Esta población no permite destacar una mejora o deterioro representativo. Los valores se conservan para inspección."}</p>
      <LineChart labels={(month ? [row] : rows.filter(r => r.month > 0)).map(r => MONTHS[r.month - 1].slice(0, 3))} unit={pol.unit} title={`Bases diarias pareadas ${a} y ${b}`} series={[{ name: `${a} · población pareada`, color: "#657790", values: (month ? [row] : rows.filter(r => r.month > 0)).map(r => r.sufficient ? r.a : null), n: (month ? [row] : rows.filter(r => r.month > 0)).map(r => r.n) }, { name: `${b} · población pareada`, color: "#2c56cf", values: (month ? [row] : rows.filter(r => r.month > 0)).map(r => r.sufficient ? r.b : null) }]} />
      <p className="am-note">{pol.statistic}. Se usan bases antes del redondeo final en las mismas fechas mes/día. ≥75 % de pares; para el año, además ≥75 % por trimestre. El 29 de febrero solo tiene par si existe en ambos años. La media de máximos diarios de un gas no es su concentración media horaria.</p>
      <details><summary>Ver población exacta y criterios trimestrales</summary><p className="am-note">Fechas pareadas: {row.dates.join(", ") || "Ninguna"}.</p>{row.month === 0 && <p className="am-note">{row.quarterly.map(q => `T${q.quarter}: ${q.n}/${q.expected}`).join(" · ")}</p>}</details>
    </>}
  </Panel>;
}
