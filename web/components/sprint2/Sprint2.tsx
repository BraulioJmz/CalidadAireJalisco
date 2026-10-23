"use client";
import { useState, type ReactNode } from "react";
import Link from "next/link";
import { REPOSITORIO } from "@/lib/site";
import type { Sprint2Data, PolS2, EventS2, EpisodeS2 } from "@/lib/sprint2-contract";
import { Context, f, Lines, Scatter } from "./Charts";
import { ComparativeCalendar } from "./ComparativeCalendar";
import { AnimatedTabs, Motion, useEntrance } from "./Motion";
import "./sprint2.css";

const TABS = ["Comparación mensual", "Categorías", "Cobertura", "Patrón horario", "Episodios", "Meteorología", "NO₂ exploratorio"];
const METEO = { ET: { label: "Temperatura externa", unit: "°C" }, RH: { label: "Humedad relativa", unit: "%" }, WS: { label: "Velocidad del viento", unit: "m/s" } };
const YCOLOR: Record<number, string> = { 2023: "#7a879d", 2024: "#2c56cf" };
function Panel({ title, question, children, note }: { title: string; question: string; children: ReactNode; note: ReactNode }) {
  return <section className="card s2-panel"><p className="eyebrow">{question}</p><h2 className="display s2-title">{title}</h2>{children}<p className="s2-note">Fuente: SEMADET · pipeline anual MIR. {note}</p></section>;
}
function Table({ children, label }: { children: ReactNode; label: string }) { return <div className="s2-scroll" tabIndex={0} role="region" aria-label={label}><table className="s2-table">{children}</table></div>; }
function Select({ label, value, change, children }: { label: string; value: string | number; change: (v: string) => void; children: ReactNode }) { return <label className="s2-select"><span>{label}</span><select value={value} onChange={e => change(e.target.value)}>{children}</select></label>; }
function Status({ children }: { children: ReactNode }) { return <div className="s2-status" role="status">{children}</div>; }

export function Sprint2({ data }: { data: Sprint2Data }) {
  const [pol, setPol] = useState<PolS2>("PM10");
  const [year, setYear] = useState("ambos");
  const [month, setMonth] = useState(12);
  const [tab, setTab] = useState(0);
  const contentRef = useEntrance<HTMLDivElement>(String(tab));
  const [population, setPopulation] = useState("pares");
  const [scope, setScope] = useState("principal");
  const [meteoVar, setMeteoVar] = useState<keyof typeof METEO>("ET");
  const [meteoYear, setMeteoYear] = useState(2024);
  const [meteoMonth, setMeteoMonth] = useState(12);
  const [eventId, setEventId] = useState("");
  const selected = data.pollutants.find(p => p.key === pol)!;
  const years = year === "ambos" ? [2023, 2024] : [Number(year)];
  const periodName = month ? data.months[month - 1] : "Todo el año";
  const period = (y: number, p = pol as string, m = month) => data.periods.find(r => r.year === y && r.month === m && r.pollutant === p)!;
  const comparison = data.comparisons.find(r => r.pollutant === pol && r.month === month)!;
  const selectedEvents = data.events.filter(r => r.pollutant === pol && years.includes(r.year) && (!month || r.month === month));
  const selectedEpisodes = data.episodes.filter(r => r.pollutant === pol && years.some(y => {
    const from = `${y}-${String(month || 1).padStart(2, "0")}-01`, to = month ? `${y}-${String(month).padStart(2, "0")}-31` : `${y}-12-31`;
    return r.start <= to && r.end >= from;
  }));
  const contextEvent: EventS2 | EpisodeS2 | undefined = [...selectedEvents, ...selectedEpisodes].find(r => r.id === eventId) ?? selectedEvents[0] ?? selectedEpisodes[0];
  const meteo = data.meteorology.find(r => r.year === meteoYear && r.month === meteoMonth && r.pollutant === pol && r.variable === meteoVar)!;
  const catPol = scope === "principal" ? pol : scope;
  const quarterly = data.comparisons.find(r => r.pollutant === pol && r.month === 0)!;
  const rankings = years.map(y => {
    const eligible = population === "pares"
      ? data.comparisons.filter(r => r.pollutant === pol && r.month > 0 && r.comparable).map(r => ({ month: r.month, value: r[y === 2023 ? "a" : "b"], n: r.n }))
      : data.periods.filter(r => r.pollutant === pol && r.year === y && r.month > 0 && r.sufficient).map(r => ({ month: r.month, value: r.mean, n: r.valid }));
    const ordered = eligible.filter((r): r is { month: number; value: number; n: number } => r.value !== null).sort((a, b) => a.value - b.value);
    return { year: y, low: ordered[0], high: ordered.at(-1) };
  });

  return <div className="s2 mx-auto max-w-7xl px-4 pb-20 pt-8 sm:px-6 lg:px-8">
    <header className="s2-heading">
      <div><p className="eyebrow">Academia Miravalle · estación MIR · Sprint 2</p><h1 className="display">2024 frente a 2023</h1><p className="s2-intro">Dos años, una referencia común. Explora qué cambió en las fechas evaluadas y dónde la cobertura limita la comparación.</p></div>
      <div className="s2-edition"><b>Análisis retrospectivo</b><span>Bandas de referencia 2024</span><span>Concentraciones, categorías y cobertura</span></div>
    </header>

    <div className="card s2-filters">
      <Select label="Contaminante principal" value={pol} change={v => { setPol(v as PolS2); setEventId(""); }}>
        {data.pollutants.filter(p => p.key !== "NO2").map(p => <option key={p.key} value={p.key}>{p.label} · {p.unit}</option>)}
      </Select>
      <Select label="Año" value={year} change={setYear}><option value="ambos">Ambos años</option><option value="2023">2023</option><option value="2024">2024</option></Select>
      <Select label="Periodo" value={month} change={v => setMonth(Number(v))}><option value={0}>Todo el año</option>{data.months.map((m, i) => <option value={i + 1} key={m}>{m}</option>)}</Select>
      <div className="s2-filter-caption">{selected.label}<br /><b>{periodName} · {selected.unit}</b></div>
    </div>

    <Motion signal={`${pol}-${year}-${month}`} preset="detail" className="s2-kpis">
      {years.map(y => { const r = period(y); return <section key={y} className="card s2-kpi" aria-label={`Indicadores ${y}`}>
        <div className="s2-kpi-top"><span style={{ color: YCOLOR[y] }}>{y}</span><span>{r.sufficient ? "≥75 % de días evaluables" : "<75 % de días evaluables"}</span></div>
        <p className="s2-kpi-value">{r.valid}<small> / {r.expected} días</small></p><p>Días evaluables de {selected.label}</p>
        <div className="s2-kpi-details"><div><b>{f(r.badPct)}{r.badPct === null ? "" : " %"}</b><span>Mala o peor · {r.bad}/{r.valid} evaluables</span></div><div><b>{f(r.mean, pol === "O3" ? 4 : 2)} {r.mean === null ? "" : selected.unit}</b><span>{selected.daily}</span></div></div>
      </section>; })}
      <section className="card s2-kpi s2-change" aria-label="Cambio en días pareados">
        <div className="s2-kpi-top"><span>Fechas coincidentes</span><span>{comparison.n}/{comparison.expected} pares</span></div>
        {comparison.comparable ? <><p className="s2-kpi-value">{comparison.change_pct === null ? "No calculable" : `${comparison.change_pct > 0 ? "+" : ""}${f(comparison.change_pct)} %`}</p><p>Cambio relativo 2024 vs. 2023</p><p className="s2-detail">Diferencia absoluta: {f(comparison.delta, 6)} {selected.unit}</p></>
          : <><p className="s2-insufficient">Cobertura insuficiente</p><p>{month === 0 ? "Comparación anual con cobertura insuficiente según el criterio del proyecto" : "El mes no alcanza el 75 % de pares del proyecto"}.</p></>}
        <p className="s2-detail">{selected.daily}. No identifica la causa del cambio.</p>
      </section>
    </Motion>
    {month === 0 && <Status>Se exige ≥75 % de pares anuales y ≥75 % en cada trimestre. Cobertura de {selected.label}: {quarterly.quarterly_coverage.map(v => `${f(v, 1)} %`).join(" · ")}. Los descriptivos disponibles se conservan; no se destaca una mejora o deterioro anual.</Status>}
    {pol === "CO" && month === 12 && <Status><b>Un aumento de concentración no equivale a duplicar el riesgo.</b> Media de máximos diarios móviles de 8 h: {f(comparison.a, 6)} → {f(comparison.b, 6)} ppm; {f(comparison.change_pct)} %. CO permaneció en Buena {period(2023).counts[0]}/{period(2023).expected} días en 2023 y {period(2024).counts[0]}/{period(2024).expected} en 2024.</Status>}

    <AnimatedTabs labels={TABS} active={tab} change={setTab} />
    <div ref={contentRef} role="tabpanel" id="s2-content" aria-labelledby={`s2-tab-${tab}`}>
      {tab === 0 && <Panel title={`Trayectoria mensual de ${selected.label}`} question="¿Qué cambió cada mes?" note="Cada punto tiene su n. Los descriptivos incluyen todos los días válidos; el pareamiento usa únicamente fechas coincidentes. Umbral mensual del proyecto: 75 %.">
        <div className="s2-inline"><Select label="Población de la gráfica" value={population} change={setPopulation}><option value="pares">Solo fechas diarias pareadas</option><option value="todos">Todos los días evaluables</option></Select><p>{selected.daily} · {selected.unit}</p></div>
        <Lines labels={data.months.map(m => m.slice(0, 3))} series={years.map(y => ({ name: `${y} · ${population === "pares" ? "fechas pareadas" : "todos los evaluables"}`, color: YCOLOR[y], dash: y === 2023,
          values: data.months.map((_, i) => population === "pares" ? data.comparisons.find(r => r.month === i + 1 && r.pollutant === pol)![y === 2023 ? "a" : "b"] : period(y, pol, i + 1).mean),
          n: data.months.map((_, i) => population === "pares" ? data.comparisons.find(r => r.month === i + 1 && r.pollutant === pol)!.n : period(y, pol, i + 1).valid) }))} unit={selected.unit} title={`${selected.daily}, 2023 y 2024, ${population === "pares" ? "fechas pareadas" : "todos los días evaluables"}`} />
        <Table label="Comparación mensual con denominadores"><thead><tr><th>Mes</th><th>2023</th><th>2024</th><th>Pares</th><th>Δ absoluta ({selected.unit})</th><th>Δ relativa</th><th>Alcance</th></tr></thead><tbody>{data.comparisons.filter(r => r.pollutant === pol && r.month > 0).map(r => <tr key={r.month} className={month === r.month ? "s2-row-selected" : ""}><th>{data.months[r.month - 1]}</th><td>{f(population === "pares" ? r.a : period(2023, pol, r.month).mean, 6)}<small>n={population === "pares" ? r.n : period(2023, pol, r.month).valid}</small></td><td>{f(population === "pares" ? r.b : period(2024, pol, r.month).mean, 6)}<small>n={population === "pares" ? r.n : period(2024, pol, r.month).valid}</small></td><td>{r.n}/{r.expected}</td><td>{f(r.delta, 6)}</td><td>{r.a === 0 ? "No calculable" : r.change_pct === null ? "Sin pares" : `${f(r.change_pct)} %`}</td><td>{r.comparable ? "Comparable en fechas evaluadas" : "Solo descriptivo · insuficiente"}</td></tr>)}</tbody></Table>
        <p className="s2-detail">Las columnas de cambio siempre usan pares, también al mostrar descriptivos. Los meses con cobertura insuficiente no se clasifican como los mejores.</p>
        <div className="s2-rankings">{rankings.map(r => <p key={r.year}><b>{r.year} · menor / mayor media evaluada</b><span>{r.low && r.high ? `${data.months[r.low.month - 1]}: ${f(r.low.value, 3)} (n=${r.low.n}) / ${data.months[r.high.month - 1]}: ${f(r.high.value, 3)} (n=${r.high.n}) ${selected.unit}` : "Sin meses suficientes"}</span></p>)}</div>
        <p className="s2-detail">Se consideran únicamente {population === "pares" ? "meses con ≥75 % de pares, usando esas mismas fechas" : "meses con ≥75 % de días evaluables, usando todos sus días válidos"}. Menor o mayor media describe esta magnitud; no representa por sí sola todas las categorías de riesgo.</p>
      </Panel>}

      {tab === 1 && <Panel title="Categorías sobre todos los días calendario" question="¿Cambió la distribución del riesgo?" note="Denominador de barras: todos los días calendario, incluidos los faltantes en gris. El porcentaje Mala o peor de los indicadores superiores usa únicamente evaluables.">
        <Select label="Conjunto de categorías" value={scope} change={setScope}><option value="principal">Contaminante seleccionado · {selected.label}</option><option value="GLOBAL">Global comparable · cuatro comunes</option><option value="AVAILABLE">Global disponible · composición variable</option></Select>
        <p className="s2-detail">{scope === "GLOBAL" ? "Requiere PM10, PM2.5, O3 y CO suficientes. Resumen del conjunto común, no índice oficial completo." : scope === "AVAILABLE" ? "Peor categoría de los indicadores presentes; cobertura parcial de los seis normativos. NO₂ complementario puede modificar este máximo." : `${selected.label}: categoría del indicador diario calculado en el pipeline.`}</p>
        {years.map(y => { const r = period(y, catPol); return <div className="s2-category-row" key={y}><div><b>{y}</b><span>{r.valid}/{r.expected} evaluables</span></div><Motion signal={JSON.stringify([y, catPol, r])} preset="reveal" className="s2-stack" aria-label={`Distribución ${y}`}>{[...r.counts, r.missing].map((n, i) => n > 0 && <div key={i} style={{ width: `${100 * n / r.expected}%`, background: i < 5 ? data.categories[i].color : "#d2d7df", color: i === 4 ? "white" : "#101b2c" }} title={`${i < 5 ? data.categories[i].name : "Sin datos"}: ${n}/${r.expected}`}><span>{n}</span></div>)}</Motion><p className="s2-detail">{r.counts.map((n, i) => `${data.categories[i].name}: ${n}`).join(" · ")} · Sin datos: {r.missing}</p></div>; })}
        <div className="s2-legend">{data.categories.map(c => <span key={c.name}><i style={{ background: c.color }} />{c.name}</span>)}<span><i style={{ background: "#d2d7df" }} />Sin datos</span></div>
        <h3 className="s2-subtitle">Determinantes del máximo · empates conservados</h3>
        <Table label="Frecuencias de contaminantes determinantes"><thead><tr><th>Conjunto / año</th><th>Días con resumen</th>{data.pollutants.map(p => <th key={p.key}>{p.label}</th>)}</tr></thead><tbody>{["GLOBAL", "AVAILABLE"].flatMap(s => years.map(y => { const r = data.determinants.find(r => r.year === y && r.month === month && r.scope === s)!; return <tr key={`${s}${y}`}><th>{s === "GLOBAL" ? "Cuatro comunes" : "Disponible parcial"} · {y}</th><td>{r.days}</td>{data.pollutants.map(p => <td key={p.key}>{r.counts[p.key]}</td>)}</tr>; }))}</tbody></Table>
        <p className="s2-detail">Las frecuencias pueden sumar más que los días por los empates. Un determinante de categoría no identifica una fuente emisora.</p>
      </Panel>}

      {tab === 2 && <Panel title="La rejilla está completa; las mediciones, no siempre" question="¿Qué tan comparable es cada periodo?" note="Horas utilizables / horas esperadas. Cada celda ofrece conteos de exclusiones, faltantes y filas. Color azul: disponibilidad, no calidad del aire.">
        <Status>No faltan filas en las rejillas de origen: {data.quality.raw_hours["2023"]} horas en 2023 y {data.quality.raw_hours["2024"]} en 2024. Esto no implica que todas tengan mediciones ni validación instrumental.</Status>
        {years.map(y => <div key={y}><h3 className="s2-subtitle">{y} · cobertura por variable</h3><Table label={`Cobertura ${y}`}><thead><tr><th>Mes</th>{["PM10", "PM2.5", "O3", "CO", "NO2", "ET", "RH", "WS"].map(v => <th key={v}>{v}</th>)}</tr></thead><tbody>{data.months.map((m, i) => <tr key={m}><th>{m.slice(0, 3)}</th>{["PM10", "PM2.5", "O3", "CO", "NO2", "ET", "RH", "WS"].map(v => { const r = data.coverage.find(r => r.year === y && r.month === i + 1 && r.variable === v)!; return <td key={v} className="s2-coverage" style={{ background: `rgba(44,86,207,${r.pct / 100 * .25})` }} title={`${r.usable}/${r.expected} horas utilizables; ${r.absent_rows} filas ausentes; ${r.missing_measurements} mediciones faltantes; ${r.excluded} exclusiones`}><b>{f(r.pct, 0)} %</b><small>{r.usable}/{r.expected} h</small></td>; })}</tr>)}</tbody></Table></div>)}
        <p className="s2-detail">Suficiencia normativa: PM horario, 2 de 3 horas recientes; CO, 6 de 8; PM diario, 18 de 24. Para máximos diarios de gases se añaden 18 lecturas crudas como criterio del proyecto. Destacar cambios exige además cobertura pareada mensual y trimestral; son criterios distintos.</p>
      </Panel>}

      {tab === 3 && <Panel title={`Frecuencia desfavorable por mes y hora · ${selected.label}`} question="¿En qué horarios se concentraron categorías Mala o peor?" note={`${selected.hourly}. Cada celda: horas Mala o peor / horas evaluables. El borde discontinuo indica cobertura horaria <75 % (referencia visual del proyecto); no ausencia de contaminación.`}>
        <p className="s2-detail">La matriz muestra el año completo para reconocer patrones. Colores azules más intensos indican mayor proporción desfavorable; no mezclan concentraciones de distintos contaminantes.</p>
        {years.map(y => <div key={y}><h3 className="s2-subtitle">{y} · {selected.hourly}</h3><div className="s2-scroll" tabIndex={0} role="region" aria-label={`Patrón horario ${y}`}><div className="s2-hour-grid"><span>Mes/h</span>{Array.from({ length: 24 }, (_, h) => <span key={h}>{String(h).padStart(2, "0")}</span>)}{data.months.flatMap((m, i) => [<b key={`m${i}`}>{m.slice(0, 3)}</b>, ...Array.from({ length: 24 }, (_, h) => { const r = data.profiles.find(r => r.year === y && r.month === i + 1 && r.hour === h && r.pollutant === pol)!; return <button key={`${i}-${h}`} className={r.valid / r.expected < .75 ? "s2-low-coverage" : ""} style={{ background: r.bad_pct === null ? "#d2d7df" : `rgba(44,86,207,${.07 + r.bad_pct / 100 * .8})`, color: r.bad_pct !== null && r.bad_pct > 55 ? "white" : "var(--ink)" }} title={`${y} · ${m} ${h}:00 · ${selected.hourly} · ${r.bad}/${r.valid} Mala o peor; ${r.valid}/${r.expected} evaluables (${f(100 * r.valid / r.expected, 1)} % de cobertura)`} aria-label={`${m} ${h}:00, ${r.bad} de ${r.valid} horas Mala o peor, ${r.valid} de ${r.expected} evaluables`}>{r.bad_pct === null ? "s/d" : f(r.bad_pct, 0)}</button>; })])}</div></div></div>)}
        <p className="s2-detail">Celdas: porcentaje de horas evaluables. «s/d» = sin indicadores; consulta el tooltip o nombre accesible para numerador, denominador y cobertura.</p>
      </Panel>}

      {tab === 4 && <Panel title="Fechas para revisar con detalle" question="¿Qué episodios, días y horas merecen revisión?" note="Selección reproducible de máximos separados y episodios de dos o más días Mala o peor. Un atípico no demuestra incendio, tráfico, fallo instrumental u otra causa.">
        <ComparativeCalendar data={data} pollutant={pol} year={year} month={month} />
        <p className="s2-detail">Máximos diarios: tres por año/contaminante separados ≥7 días. Horarios: tres separados ≥24 horas. Selección original anual, filtrada aquí por periodo; no se vuelve a elegir un máximo nuevo al filtrar.</p>
        <Table label="Máximos relevantes"><thead><tr><th>Fecha</th><th>Selección</th><th>Indicador ({selected.unit})</th><th>Lectura cruda</th><th>Categoría / n</th><th>Contexto</th></tr></thead><tbody>{selectedEvents.map(r => <tr key={r.id}><th>{r.date}</th><td>{r.kind}</td><td>{f(r.value, 3)}</td><td>{r.raw === null ? "No aplica al máximo diario" : `${f(r.raw, 3)} ${selected.unit}`}</td><td>{data.categories[r.category].name}{r.n !== null && <small>{r.n}/24 lecturas crudas</small>}</td><td><button className="s2-link" onClick={() => setEventId(r.id)}>Ver serie</button></td></tr>)}</tbody></Table>
        {!selectedEvents.length && <p className="s2-empty">No hay máximos de la selección anual en este filtro. Esto no significa que el mes carezca de contaminación.</p>}
        <h3 className="s2-subtitle">Episodios consecutivos</h3><Table label="Episodios"><thead><tr><th>Intervalo real</th><th>Duración completa</th><th>Peor categoría</th><th>Lecturas / esperadas</th><th>Contexto</th></tr></thead><tbody>{selectedEpisodes.map(r => <tr key={r.id}><th>{r.start} → {r.end}{r.crossYear && <small>Cruza de año · intervalo completo sin duplicar</small>}</th><td>{r.days} días</td><td>{data.categories[r.max_category].name}</td><td>{r.n_raw_hours}/{r.expected_hours}</td><td><button className="s2-link" onClick={() => setEventId(r.id)}>Ver episodio</button></td></tr>)}</tbody></Table>
        {!selectedEpisodes.length && <p className="s2-empty">Sin episodios suficientes de la selección en este periodo.</p>}
        {contextEvent && <div className="s2-context"><h3 className="s2-subtitle">Contexto · {"start" in contextEvent ? `${contextEvent.start} → ${contextEvent.end}` : contextEvent.date}</h3><p className="s2-detail">{"start" in contextEvent ? "Base diaria; incluye dos días de contexto a cada lado. El intervalo mantiene sus fechas originales." : `${contextEvent.kind === "Máximo diario" ? "Contexto horario del máximo diario" : "Contexto del máximo horario"}. Se distinguen lectura cruda e indicador horario (${selected.hourly}).`}</p><Context points={contextEvent.context} unit={selected.unit} daily={"start" in contextEvent} title="Serie de contexto del periodo seleccionado" /></div>}
      </Panel>}

      {tab === 5 && <Panel title={`Concentración y meteorología coincidentes · ${selected.label}`} question="¿Cómo coincidieron concentración, temperatura, humedad o viento?" note="Cada punto corresponde a la misma fecha para ambas variables. Spearman mensual descriptivo, sin p-valores y sin atribución causal. WD es circular y queda fuera de esta correlación.">
        <div className="s2-inline"><Select label="Año meteorología" value={meteoYear} change={v => setMeteoYear(Number(v))}><option value={2023}>2023</option><option value={2024}>2024</option></Select><Select label="Mes meteorología" value={meteoMonth} change={v => setMeteoMonth(Number(v))}>{data.months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</Select><Select label="Variable meteorológica" value={meteoVar} change={v => setMeteoVar(v as keyof typeof METEO)}>{Object.entries(METEO).map(([v, info]) => <option value={v} key={v}>{info.label} ({info.unit})</option>)}</Select></div>
        <div className="s2-meteo-summary"><b>ρ de Spearman: {meteo.rho === null ? "No calculable" : f(meteo.rho, 3)}</b><span>n={meteo.n}/{meteo.expected} pares diarios · cobertura {f(meteo.coverage_pct, 1)} %</span></div>
        {meteo.rho === null && <Status>{meteo.n < 15 ? "Menos de 15 pares: no se calcula Spearman." : "Serie constante: Spearman no calculable."} Se conservan los puntos existentes.</Status>}
        <p className="s2-detail">Eje vertical: {selected.daily}, {selected.unit}. Eje horizontal: media diaria de {METEO[meteoVar].label.toLowerCase()} (≥18 lecturas). Los filtros de esta vista identifican explícitamente un solo mes y año.</p>
        <Scatter row={meteo} variableUnit={METEO[meteoVar].unit} concentrationUnit={selected.unit} variableLabel={METEO[meteoVar].label} />
        <p className="s2-detail">ET es temperatura externa. IT no demuestra inversión térmica. La cobertura de RH cambia de temporada entre años; dependencia temporal, estación y variables omitidas limitan cualquier interpretación.</p>
      </Panel>}

      {tab === 6 && <Panel title="NO₂ · complemento exploratorio de 2024" question="¿Qué información adicional existe y qué falta confirmar?" note="Lecturas presentes desde agosto de 2024. El catálogo Param de MIR no enumera NO₂; procedencia y calibración instrumentales pendientes. No se incluye en el resumen comparable de cuatro comunes.">
        <Status>No existe una comparación anual NO₂ 2024 vs. 2023. Se presentan únicamente las observaciones de 2024 y su cobertura.</Status>
        <Table label="NO2 2024 exclusivamente"><thead><tr><th>Mes 2024</th><th>Días evaluables</th><th>Media de máximos horarios (ppm)</th><th>Mala o peor / evaluables</th></tr></thead><tbody>{data.months.map((m, i) => { const r = period(2024, "NO2", i + 1); return <tr key={m}><th>{m}</th><td>{r.valid}/{r.expected}</td><td>{f(r.mean, 6)}</td><td>{r.bad}/{r.valid}{r.valid === 0 ? " · Sin indicador" : ` · ${f(r.badPct)} %`}</td></tr>; })}</tbody></Table>
      </Panel>}
    </div>

    <section className="s2-agency" aria-labelledby="uso-academico"><div><p className="eyebrow">Perspectiva de la agencia</p><h2 id="uso-academico" className="display s2-title">Usar los hallazgos para orientar la revisión</h2></div><div className="s2-agency-grid"><article><b>Observado</b><p>Diciembre tiene comparación suficiente de PM₁₀, PM₂.₅ y CO. Las tablas distinguen magnitudes y categorías; O₃ y el resumen común presentan menos pares.</p></article><article><b>Posible interpretación</b><p>Priorizar la revisión académica de diciembre y de horarios con mayor frecuencia desfavorable, conservando la cautela por cobertura. El patrón orienta inspección; no demuestra una causa.</p></article><article><b>Dato adicional necesario</b><p>Mayor continuidad de mediciones, bitácoras de operación y calibración, y procedencia de NO₂. Ninguna correlación de este tablero atribuye incendios, tráfico o inversión térmica.</p></article></div></section>

    <details className="card s2-method"><summary>Metodología y evidencia del análisis</summary><div><p>Se aplican bandas de referencia 2024 a ambos años; no se reconstruyen avisos oficiales. Suficiencia de ventanas y cobertura de comparación son criterios distintos. No se promedian categorías ordinales. El SO₂ 2023 se excluye por invalidación documentada; extremos y empates se conservan.</p><p><Link href="/metodologia">Cómo se interpreta el análisis</Link> · <a href={REPOSITORIO}>Repositorio y documentación técnica</a> · <Link href="/sprint-1">Consultar Sprint 1</Link></p><h3 className="s2-subtitle">CSV calculados</h3><div className="s2-downloads">{data.downloads.map(d => <a href={d.url} key={d.name} download>{d.name}</a>)}</div><h3 className="s2-subtitle">Figuras del análisis</h3><ul className="s2-figures">{data.figures.map(fig => <li key={fig.id}><span>{fig.question}</span><a href={fig.svg} download>SVG</a><a href={fig.png} download>PNG</a></li>)}</ul><p className="s2-detail">Las descargas reúnen resultados calculados y figuras con sus fuentes y denominadores. Los libros originales completos se conservan en el paquete técnico.</p></div></details>
  </div>;
}
