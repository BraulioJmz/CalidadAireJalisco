"use client";
import { useEffect, useReducer, useState } from "react";
import type { DailyS2, PolS2, Sprint2Data } from "@/lib/sprint2-contract";
import { isoDate, monthLength, monthStart, timelineLength, timelineReducer } from "@/lib/calendar";
import { f } from "./Charts";
import { Motion, useReducedMotion } from "./Motion";
const METEO = { ET: { label: "Temperatura externa", unit: "°C" }, RH: { label: "Humedad relativa", unit: "%" }, WS: { label: "Velocidad del viento", unit: "m/s" } };
const SHORT = ["B", "A", "M", "MM", "EM"];

export function ComparativeCalendar({ data, pollutant, year, month }: { data: Sprint2Data; pollutant: PolS2; year: string; month: number }) {
  const [localMonth, setLocalMonth] = useState(12);
  const activeMonth = month || localMonth;
  return <section className="s2-calendar" aria-labelledby="calendario-titulo">
    <h3 id="calendario-titulo" className="display s2-title">Un mes, día a día</h3>
    <p className="s2-detail">¿Cómo se distribuyeron los días favorables, desfavorables y sin información dentro de cada mes, y qué diferencias aparecen entre ambos años?</p>
    {month === 0 && <label className="s2-select s2-calendar-month"><span>Mes del calendario</span><select value={localMonth} onChange={e => setLocalMonth(Number(e.target.value))}>{data.months.map((m, i) => <option value={i + 1} key={m}>{m}</option>)}</select></label>}
    <CalendarMonth key={`${pollutant}-${year}-${month}-${activeMonth}`} data={data} pollutant={pollutant} year={year} month={activeMonth} />
  </section>;
}

function CalendarMonth({ data, pollutant, year, month }: { data: Sprint2Data; pollutant: PolS2; year: string; month: number }) {
  const years = year === "ambos" ? [2023, 2024] : [Number(year)];
  const last = timelineLength(years, month);
  const [state, dispatch] = useReducer((s: { day: number; playing: boolean }, a: Parameters<typeof timelineReducer>[1]) => timelineReducer(s, a, last), { day: 1, playing: false });
  const reduced = useReducedMotion();
  const statistic = data.dailyStatistics[pollutant];
  const pol = data.pollutants.find(p => p.key === pollutant)!;
  useEffect(() => {
    if (reduced) dispatch({ type: "pause" });
  }, [reduced]);
  useEffect(() => {
    if (!state.playing || reduced) return;
    const timer = window.setTimeout(() => dispatch({ type: "tick" }), 1400);
    return () => window.clearTimeout(timer);
  }, [state.playing, state.day, reduced]);
  useEffect(() => {
    const pauseHidden = () => { if (document.hidden) dispatch({ type: "pause" }); };
    document.addEventListener("visibilitychange", pauseHidden);
    return () => document.removeEventListener("visibilitychange", pauseHidden);
  }, []);
  const byDate = new Map(data.daily.map(r => [r.date, r]));
  return <>
    <div className="s2-calendar-controls" role="group" aria-label="Recorrido temporal del calendario">
      <button type="button" disabled={state.day === 1} onClick={() => dispatch({ type: "step", offset: -1 })}>← Día anterior</button>
      <button type="button" disabled={reduced && state.day !== last} onClick={() => dispatch(state.day === last ? { type: "restart", autoplay: !reduced } : { type: state.playing ? "pause" : "play" })}>{state.day === last ? "Volver a reproducir" : state.playing ? "Pausar" : "Reproducir"}</button>
      <button type="button" disabled={state.day === last} onClick={() => dispatch({ type: "step", offset: 1 })}>Día siguiente →</button>
      <p role="status" aria-live="polite" aria-atomic="true">{state.day} de {data.months[month - 1]} · {state.day === last ? "Fin del mes" : state.playing ? "En reproducción" : "Pausado"}</p>
    </div>
    <div className="s2-calendar-progress" role="progressbar" aria-label="Avance dentro del mes" aria-valuemin={1} aria-valuemax={last} aria-valuenow={state.day} aria-valuetext={`Día ${state.day} de ${last}`}><span style={{ transform: `scaleX(${state.day / last})` }} /></div>
    {reduced && <p className="s2-detail">Movimiento reducido: recorrido automático desactivado. Selecciona una fecha o utiliza los botones de día anterior y siguiente. Al volver a reproducir se regresa al día 1 sin avance automático.</p>}
    {month === 2 && state.day === 29 && <p className="s2-calendar-nonexistent" role="note">El 29 de febrero de 2024 no tiene fecha equivalente en 2023.</p>}
    <p className="s2-detail">{pol.label} · {statistic.label} ({statistic.unit}). Selección sincronizada por mes y día; el recorrido se detiene al final del mes y pausa al cambiar filtros o vista.</p>
    <div className="s2-legend s2-calendar-legend" aria-label="Leyenda del calendario">{data.categories.map((c, i) => <span key={c.name}><i style={{ background: c.color }} />{SHORT[i]} · {c.name}</span>)}<span><i className="s2-missing-swatch" />s/d · Sin indicador suficiente</span><span>— Fecha inexistente</span></div>
    <div className="s2-calendar-years">
      {years.map(y => {
        const days = monthLength(y, month);
        const rows = data.daily.filter(r => r.year === y && r.month === month);
        const categories = rows.map(r => r.pollutants[pollutant].category);
        const date = isoDate(y, month, state.day);
        const row = date === null ? undefined : byDate.get(date)!;
        return <article className="s2-calendar-year" key={y} aria-label={`Calendario ${data.months[month - 1]} ${y}`}>
          <header><h4>{data.months[month - 1]} {y}</h4><p>Buena: {categories.filter(c => c === 0).length}/{days} · Mala o peor: {categories.filter(c => c !== null && c >= 2).length}/{days} · Sin indicador: {categories.filter(c => c === null).length}/{days}</p></header>
          <div className="s2-calendar-grid">
            {["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"].map(d => <span className="s2-weekday" key={d}>{d}</span>)}
            {Array.from({ length: monthStart(y, month) }, (_, i) => <span key={`space${i}`} className="s2-calendar-space" aria-hidden="true" />)}
            {rows.map(r => {
              const category = r.pollutants[pollutant].category;
              const name = category === null ? "Sin indicador suficiente" : data.categories[category].name;
              return <button type="button" key={r.date} data-date={r.date} data-category={category === null ? "missing" : category} className={`s2-calendar-day ${category === null ? "s2-calendar-missing" : ""}`} style={category === null ? undefined : { backgroundColor: data.categories[category].color, color: category === 4 ? "white" : "#101b2c" }} aria-label={`${r.date} · ${name}`} aria-pressed={r.day === state.day} title={`${r.date}: ${name}`} onClick={() => dispatch({ type: "select", day: r.day })}><b>{r.day}</b><span>{category === null ? "s/d" : SHORT[category]}</span></button>;
            })}
          </div>
          {days < last && <p className="s2-calendar-nonexistent">— El {last} de {data.months[month - 1].toLowerCase()} no existe en {y}.</p>}
          <Motion signal={String(state.day)} preset="detail" className="s2-calendar-detail" aria-label={`Detalle diario ${y}`}>
            <h5>{row ? `${state.day} de ${data.months[month - 1].toLowerCase()} de ${y}` : `Sin fecha equivalente en ${y}`}</h5>
            {row ? <DayDetail row={row} pollutant={pollutant} data={data} /> : <p className="s2-calendar-nonexistent"><b>Fecha inexistente.</b> El 29 de febrero de 2024 no tiene fecha equivalente en 2023. No es un día con datos ausentes.</p>}
          </Motion>
        </article>;
      })}
    </div>
    <p className="s2-detail">Fuente: archivos diarios procesados, columnas I, EXACT, C y N del contaminante; M y N de meteorología. I es el indicador redondeado que determina la categoría; EXACT conserva la base antes del redondeo. No se interpolan días sin datos. Las filas vacías al inicio de la semana son espacios de alineación.</p>
    <p className="s2-detail">Comprobar fechas y valores: <a className="s2-link" download href="/descargas/sprint-2/MIR_2023_diario.csv">CSV diario 2023</a> · <a className="s2-link" download href="/descargas/sprint-2/MIR_2024_diario.csv">CSV diario 2024</a>. La suficiencia de un indicador no acredita calibración instrumental ni identifica causas.</p>
  </>;
}

function DayDetail({ row, pollutant, data }: { row: DailyS2; pollutant: PolS2; data: Sprint2Data }) {
  const p = row.pollutants[pollutant], statistic = data.dailyStatistics[pollutant];
  return <>
    <p className="s2-calendar-statistic">{statistic.label}</p>
    <p className="s2-calendar-value">{p.indicator === null ? "Sin indicador suficiente" : `${f(p.indicator, pollutant === "O3" ? 3 : pollutant === "CO" ? 2 : 0)} ${statistic.unit}`}</p>
    <p><b>Categoría:</b> {p.category === null ? "Sin datos suficientes para categorizar" : data.categories[p.category].name}</p>
    {p.exact !== null && <p>Base antes del redondeo: {f(p.exact, 6)} {statistic.unit}</p>}
    <p>Lecturas utilizables: <b>{p.readings}/{row.expected}</b> · Bases horarias suficientes: {p.indicators}/{row.expected}</p>
    <h6>Meteorología diaria disponible</h6>
    <dl>{(Object.keys(METEO) as (keyof typeof METEO)[]).map(key => <div key={key}><dt>{METEO[key].label}</dt><dd>{row.weather[key].value === null ? "Sin promedio suficiente" : `${f(row.weather[key].value, 2)} ${METEO[key].unit}`} <span>· {row.weather[key].readings}/{row.expected} lecturas</span></dd></div>)}</dl>
  </>;
}
