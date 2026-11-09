"use client";
import { useEffect, useReducer, useState } from "react";
import type { Day, Events, HourChunk, Pollutant, Summary } from "@/lib/academia";
import { chunkUrls, dateLabel, fmt, hourGrid, mergeHours, MONTHS, pad, shiftHour } from "@/lib/academia";
import { isoDate, monthLength, monthStart, timelineLength, timelineReducer, type TimelineAction, type TimelineState } from "@/lib/calendar";
import { useReducedMotion } from "@/components/sprint2/Motion";
import { LineChart, Loading, MonthOptions, Motion, Panel, Select, Table, useData } from "./Shared";

export function Calendar({ summary, pol, initialYear = 2024 }: { summary: Summary; pol: Pollutant; initialYear?: number }) {
  const first = Math.min(initialYear, 2023);
  const [a, setA] = useState(first), [b, setB] = useState(first + 1), [month, setMonth] = useState(12);
  return <>
    <div className="am-controls"><Select label="Año de referencia" value={a} change={v => { setA(+v); if (+v >= b) setB(+v + 1); }}>{summary.years.filter(y => y < 2024).map(y => <option key={y}>{y}</option>)}</Select><Select label="Año de comparación" value={b} change={v => setB(+v)}>{summary.years.filter(y => y > a).map(y => <option key={y}>{y}</option>)}</Select><Select label="Mes del calendario" value={month} change={v => setMonth(+v)}><MonthOptions /></Select></div>
    <CalendarComparison key={`${a}|${b}|${month}|${pol.key}`} summary={summary} pol={pol} years={[a,b]} month={month} initialFocus={[a,b].includes(initialYear) ? initialYear : b} />
  </>;
}

function CalendarComparison({ summary, pol, years, month, initialFocus }: { summary: Summary; pol: Pollutant; years: number[]; month: number; initialFocus: number }) {
  const last = timelineLength(years, month);
  const cells = Math.max(...years.map(year => Math.ceil((monthStart(year, month) + monthLength(year, month)) / 7))) * 7;
  const [state, dispatch] = useReducer((s: TimelineState, action: TimelineAction) => timelineReducer(s, action, last), { day: 1, playing: false });
  const [focusYear, setFocusYear] = useState(initialFocus), [allEpisodes, setAllEpisodes] = useState(false);
  const reduced = useReducedMotion();
  const days = useData<Day[][]>(years.map(year => `/datos/sprint-3/calendario/${year}-${pad(month)}.json`));
  const events = useData<Events>(`/datos/sprint-3/episodios/${pol.slug}.json`);
  const ready = !!days.data;
  useEffect(() => { if (reduced) dispatch({ type: "pause" }); }, [reduced]);
  useEffect(() => {
    if (!state.playing || reduced || !ready) return;
    const timer = window.setTimeout(() => dispatch({ type: "tick" }), 1400);
    return () => window.clearTimeout(timer);
  }, [state.playing, state.day, reduced, ready]);
  useEffect(() => {
    const pauseHidden = () => { if (document.hidden) dispatch({ type: "pause" }); };
    document.addEventListener("visibilitychange", pauseHidden);
    return () => document.removeEventListener("visibilitychange", pauseHidden);
  }, []);
  const date = isoDate(focusYear, month, state.day);
  const start = date ? shiftHour(`${date}T00:00:00`, -24) : null, end = date ? shiftHour(`${date}T23:00:00`, 24) : null;
  const grid = start && end ? hourGrid(start, end) : [];
  const context = useData<HourChunk[]>(start && end ? chunkUrls(start, end) : null);
  return <>
    <Panel id="episodios-calendario" title="Un mes, dos años" question="¿Cómo se distribuyen los días favorables, desfavorables y sin información en ambos años?">
      <p className="am-note">{pol.statistic}. Bandas retrospectivas de 2024; no reconstruyen los avisos oficiales de cada año.</p>
      {pol.key === "NO2" && years.includes(2024) && <p className="am-callout" role="note">NO₂ 2024 es exploratorio: el catálogo MIR no acredita su procedencia ni calibración. No permite sostener una comparación representativa con otros años.</p>}
      {pol.key === "SO2" && years.some(y => y === 2023 || y === 2024) && <p className="am-callout" role="note">SO₂ de 2023 está excluido por falta de calibración documentada; en 2024 no hay mediciones disponibles.</p>}
      {["NO", "NOX"].includes(pol.key) && years.includes(2024) && <p className="am-callout" role="note">{pol.label} de 2024 tiene procedencia instrumental sin acreditar y es exploratorio. Esta variable no tiene categorías normativas en el análisis.</p>}
      <div className="am-calendar-playback">
        <div className="am-calendar-transport" role="group" aria-label="Recorrido temporal comparativo">
          <button type="button" aria-label="Día anterior del calendario" disabled={!ready || state.day === 1} onClick={() => dispatch({ type: "step", offset: -1 })}>← Anterior</button>
          <button type="button" className="am-play-toggle" disabled={!ready || (reduced && state.day !== last)} onClick={() => dispatch(state.day === last ? { type: "restart", autoplay: !reduced } : { type: state.playing ? "pause" : "play" })}>{state.day === last ? "Volver a reproducir" : state.playing ? "Pausar" : "Reproducir"}</button>
          <button type="button" aria-label="Día siguiente del calendario" disabled={!ready || state.day === last} onClick={() => dispatch({ type: "step", offset: 1 })}>Siguiente →</button>
        </div>
        <p className="am-timeline-status" role="status" aria-live={state.playing ? "off" : "polite"}>Día {state.day} de {last} · {state.day === last ? "Fin del mes" : state.playing ? "En reproducción" : "Pausado"}</p>
        <div className="am-calendar-progress" role="progressbar" aria-label="Avance dentro del mes" aria-valuemin={1} aria-valuemax={last} aria-valuenow={state.day} aria-valuetext={`Día ${state.day} de ${last}`}><span style={{ transform: `scaleX(${state.day / last})` }} /></div>
      </div>
      {reduced && <p className="am-note">Movimiento reducido: la reproducción automática está desactivada. Puedes elegir una fecha o usar Anterior y Siguiente; al volver a reproducir se regresa al día 1 sin avance automático.</p>}
      <ul className="am-category-legend">{pol.categoryApplicable && summary.categories.map(c => <li key={c.code}><i style={{ background: c.color }} />{c.name}</li>)}<li><i className="am-missing" />Sin indicador</li><li>— Fecha inexistente</li></ul>
      {!days.data ? <Loading error={days.error} /> : <div className="am-comparison-calendars">{years.map((year,i) => <CalendarYear key={year} summary={summary} pol={pol} year={year} month={month} day={state.day} cells={cells} rows={days.data![i]} select={day => dispatch({ type: "select", day })} />)}</div>}
      <p className="am-note">Selección sincronizada por mes y día. El tramado distingue la ausencia de indicador de Buena. El borde señala la selección sin cambiar la categoría. La suficiencia diaria no acredita calibración instrumental.</p>
    </Panel>
    <Panel title={`Contexto horario · ${focusYear}`} question="¿La fecha seleccionada forma parte de un pico, una interrupción o una secuencia?">
      <div className="am-controls"><Select label="Año del contexto y episodios" value={focusYear} change={v => { dispatch({type:"pause"}); setFocusYear(+v); }}>{years.map(year => <option key={year}>{year}</option>)}</Select></div>
      {!date ? <p className="am-status">No existe una fecha equivalente al día {state.day} de {MONTHS[month-1].toLowerCase()} en {focusYear}. No se inventan observaciones ni un contexto para esa fecha.</p> : !context.data ? <Loading error={context.error} /> : <LineChart labels={grid.map(t => t.slice(5, 16).replace("T", " "))} timestamps={grid} unit={pol.unit} title={`Concentraciones horarias observadas alrededor de ${date}`} series={[{ name: `Observado · ${focusYear}`, color: "#2c56cf", values: mergeHours(context.data, grid, pol.key) }]} />}
      {start && end && <p className="am-note">Desde {dateLabel(start)} hasta {dateLabel(end)}. El contexto conserva los cruces de mes o año. Los huecos interrumpen la línea; esta gráfica no reclasifica las mediciones.</p>}
    </Panel>
    <EventList summary={summary} pol={pol} year={focusYear} month={month} data={events.data} error={events.error} all={allEpisodes} change={value => { dispatch({type:"pause"}); setAllEpisodes(value); }} />
  </>;
}

function CalendarYear({ summary, pol, year, month, day, cells, rows, select }: { summary: Summary; pol: Pollutant; year: number; month: number; day: number; cells: number; rows: Day[]; select: (day: number) => void }) {
  const date = isoDate(year, month, day), selected = rows.find(r => r.date === date), value = selected?.pollutants[pol.key];
  const category = value?.category == null ? null : summary.categories[value.category];
  const codes = rows.map(r => r.pollutants[pol.key].category), expected = monthLength(year,month);
  return <article className="am-calendar-year" aria-label={`Calendario ${MONTHS[month-1]} ${year}`} data-year={year}>
    <h3>{MONTHS[month-1]} de {year}</h3>
    <p className="am-note">{pol.categoryApplicable ? `Buena: ${codes.filter(c => c === 0).length}/${expected} · Mala o peor: ${codes.filter(c => c !== null && c >= 2).length}/${expected} · Sin indicador: ${codes.filter(c => c === null).length}/${expected}` : `${rows.filter(r => r.pollutants[pol.key].value !== null).length}/${expected} días con base observada; sin banda normativa`}</p>
    <div className="am-calendar-grid">
      {["L", "M", "Mi", "J", "V", "S", "D"].map((label,i) => <span className="am-weekday" key={i}>{label}</span>)}{Array.from({length:monthStart(year,month)},(_,i)=><span key={`space-${i}`} aria-hidden="true" />)}
      {rows.map(r => { const d = r.pollutants[pol.key], c = d.category == null ? null : summary.categories[d.category], n = +r.date.slice(8); return <button type="button" key={r.date} data-date={r.date} data-category={d.category ?? (d.value == null ? "missing" : "not-applicable")} aria-pressed={day === n} className={`am-day ${c ? "" : d.value == null ? "am-missing" : "am-uncategorized"}`} style={c ? { background:c.color, color:c.ink } : undefined} aria-label={`${r.date}: ${c?.name ?? (d.value == null ? "Sin indicador" : "Sin banda normativa")}`} onClick={()=>select(n)}><b>{n}</b><span aria-hidden="true">{c ? ["Buena", "Acept.", "Mala", "Muy mala", "Extrema"][c.code] : d.value == null ? "Sin ind." : "Sin banda"}</span></button>; })}
      {Array.from({length:cells - monthStart(year,month) - rows.length},(_,i)=><span key={`tail-${i}`} aria-hidden="true" />)}
    </div>
    <Motion className={`am-day-detail${date ? "" : " am-nonexistent"}`} signal={`${date ?? `inexistente-${day}`}|${pol.key}`} preset="detail" role="region" aria-label={`Detalle diario ${year}`}><h4>{date ?? `Sin fecha equivalente en ${year}`}</h4>{!date ? <p>Fecha inexistente. No es un día con mediciones ausentes.</p> : <><b className="am-big-number">{fmt(value?.value,pol.unit === "ppm" ? 3 : 1)} <small>{pol.unit}</small></b><p>{category?.name ?? (pol.categoryApplicable ? "Sin indicador suficiente" : "Sin categoría normativa")}</p><p><b>{value?.n ?? 0} / 24</b> lecturas disponibles · {value?.indN ?? 0} bases horarias suficientes</p></>}</Motion>
  </article>;
}

function EventList({ summary, pol, year, month, data, error, all, change }: { summary: Summary; pol: Pollutant; year: number; month: number; data?: Events; error?: string; all: boolean; change: (all: boolean) => void }) {
  const low = `${year}-${all ? "01" : pad(month)}-01`, high = `${year}-${all ? "12-31" : `${pad(month)}-${pad(monthLength(year,month))}`}`;
  const episodes = data?.episodes.filter(r => r.end >= low && r.start <= high) ?? [];
  const peaks = data?.peaks.filter(r => r.year === year && (all || +r.date.slice(5,7) === month)) ?? [];
  return <Panel id="episodios-secuencia" title={`Episodios y señales para inspección · ${year}`} question="¿Qué secuencias desfavorables y extremos coinciden con el periodo?">
    <label className="am-check"><input type="checkbox" checked={all} onChange={e=>change(e.target.checked)} />Consultar episodios y máximos de todo el año {year}</label>
    {!data ? <Loading error={error} /> : <><p className="am-note">{episodes.length} episodios que se superponen al periodo. Al menos dos días consecutivos Mala o peor; la falta de indicador corta el episodio. Los límites no se recortan al cambiar el mes.</p>
      {episodes.length ? <Table label="Episodios históricos"><thead><tr><th>Inicio real</th><th>Fin real</th><th>Días</th><th>Categoría máxima</th><th>Lecturas</th></tr></thead><tbody>{episodes.map(r => <tr key={r.start}><td>{r.start}</td><td>{r.end}</td><td>{r.days}</td><td>{summary.categories[r.max_category].name}</td><td>{r.n_hours}/{r.expected_hours}</td></tr>)}</tbody></Table> : <p className="am-status">No se identifican episodios con ese criterio. La ausencia de episodios no acredita ausencia de riesgo.</p>}
      <h3>Máximos horarios seleccionados</h3>{peaks.length ? <Table label="Máximos horarios"><thead><tr><th>Fecha real</th><th>Concentración ({pol.unit})</th><th>Alcance</th></tr></thead><tbody>{peaks.map(r => <tr key={r.date}><td>{dateLabel(r.date)}</td><td>{fmt(r.value,pol.unit === "ppm" ? 4 : 1)}</td><td>{r.exploratory ? "Exploratorio" : "Descriptivo"}</td></tr>)}</tbody></Table> : <p className="am-note">Sin máximos seleccionados en el periodo.</p>}
      <p className="am-note">Se seleccionan tres máximos por año separados al menos 24 horas. {data.anomalies.filter(r => r.date >= low && r.date.slice(0,10) <= high).length} señales de atípico robusto en el periodo, conservadas en la descarga. Un extremo o atípico no demuestra error instrumental, incendio o fuente emisora.</p>
    </>}
  </Panel>;
}
