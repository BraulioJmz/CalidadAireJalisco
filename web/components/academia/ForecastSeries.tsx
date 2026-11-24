"use client";

import { useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { EvaluationPoint, HourChunk } from "@/lib/academia";
import { chunkUrls, dateLabel, fmt, hourGrid, mergeHours, pad, shiftHour } from "@/lib/academia";
import { useEntrance } from "@/components/sprint2/Motion";
import { Loading, MonthOptions, Panel, Select, useData } from "./Shared";

const HORIZONS = [1, 2, 3];
const START = "2024-01-01T00:00:00";
const END = "2024-12-31T23:00:00";
const EMPTY: (number | null)[] = [];
const COLORS = { observed: "var(--ink)", predicted: "var(--am-forecast)", error: "var(--accent)" };

type Zoom = "week" | "month" | "year";
type Selection = { target: string; horizon: number };
type Trace = { name: keyof typeof COLORS; values: (number | null)[] };

function timeWindow(zoom: Zoom, date: string): [string, string] {
  if (zoom === "year") return [START, END];
  if (zoom === "week") {
    const first = date + "T00:00:00";
    return [first, shiftHour(first, 167) < END ? shiftHour(first, 167) : END];
  }
  const month = +date.slice(5, 7);
  const last = new Date(Date.UTC(2024, month, 0)).getUTCDate();
  return [`2024-${pad(month)}-01T00:00:00`, `2024-${pad(month)}-${last}T23:00:00`];
}

function metric(value: number | null | undefined, missing: string) {
  return value == null ? missing : `${fmt(value)} µg/m³`;
}

function PointDetail({ time, horizon, point, observed, openOrigin }: {
  time: string; horizon: number; point?: EvaluationPoint; observed: number | null;
  openOrigin: (origin: string) => void;
}) {
  return <div className="am-series-reading">
    <dl aria-label={`Lectura seleccionada a +${horizon} h`}>
      <div><dt>Origen</dt><dd>{point ? dateLabel(point.origin) : "Sin emisión evaluada"}</dd></div>
      <div><dt>Fecha objetivo</dt><dd><time dateTime={time}>{dateLabel(time)}</time></dd></div>
      <div><dt>Horizonte</dt><dd>+{horizon} h</dd></div>
      <div><dt>Observado</dt><dd>{metric(observed, "Sin medición")}</dd></div>
      <div><dt>Predicción</dt><dd>{metric(point?.predicted, "Sin predicción")}</dd></div>
      <div><dt>Diferencia</dt><dd>{metric(point?.signed_error, "Sin par evaluado")}</dd></div>
    </dl>
    {point && <button type="button" onClick={() => openOrigin(point.origin)}>Ver los tres horizontes de este origen →</button>}
  </div>;
}

const PLOT = { height: 162, left: 42, top: 12, bottom: 126 };

function TimePlot({ dates, traces, domain, index, select, label, error }: {
  dates: string[]; traces: Trace[]; domain: [number, number];
  index: number; select: (index: number) => void; label: string; error?: boolean;
}) {
  const id = useId();
  const container = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(720);
  const { height, left, top, bottom } = PLOT;
  const right = width - 12;
  useLayoutEffect(() => {
    const element = container.current;
    if (!element) return;
    const measure = () => setWidth(Math.max(240, Math.floor(element.clientWidth)));
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const span = dates.length - 1;
  const [min, max] = domain;
  const reveal = useEntrance<SVGGElement>(`${label}/${dates[0]}/${dates.at(-1)}`, "reveal");
  const x = (i: number) => left + i / span * (right - left);
  const y = (value: number) => bottom - (value - min) / (max - min) * (bottom - top);
  const paths = useMemo(() => traces.map(trace => {
    const segments: string[] = [];
    for (let i = 0; i < trace.values.length; i++) {
      const value = trace.values[i];
      if (value == null) continue;
      const px = left + i / span * (right - left);
      const py = bottom - (value - min) / (max - min) * (bottom - top);
      const startsRun = trace.values[i - 1] == null;
      segments.push(`${startsRun ? "M" : "L"}${px.toFixed(3)} ${py.toFixed(3)}`);
      if (startsRun && trace.values[i + 1] == null) segments.push("h0.01");
    }
    return { name: trace.name, d: segments.join(" ") };
  }), [traces, span, min, max, bottom, left, right, top]);
  const ticks = [0, Math.round(span / 2), span];
  const compactTicks = width < 430;
  const tickDay = (date: string) => date.slice(8, 10) + "/" + date.slice(5, 7);

  return <>
    <div ref={container}><svg className="am-series-plot" viewBox={`0 0 ${width} ${height}`}
      role="img" aria-label={label} data-start={dates[0]} data-end={dates.at(-1)} data-max={max}
      onClick={event => {
        const rect = event.currentTarget.getBoundingClientRect();
        const coordinate = (event.clientX - rect.left) / rect.width * width;
        select(Math.max(0, Math.min(span, Math.round((coordinate - left) / (right - left) * span))));
      }}>
      {[min, (min + max) / 2, max].map(value => <g key={value}>
        <line x1={left} x2={right} y1={y(value)} y2={y(value)} className={error && value === 0 ? "am-series-zero" : "s2-grid"} />
        <text x={left - 7} y={y(value) + 4} className="s2-axis" textAnchor="end">{fmt(value, 0)}</text>
      </g>)}
      <g ref={reveal}>{paths.map(trace => <path key={trace.name} d={trace.d} fill="none" stroke={COLORS[trace.name]}
        strokeWidth={trace.name === "observed" ? 1.25 : 1.55} strokeDasharray={trace.name === "predicted" ? "5 3" : undefined}
        strokeLinecap="round" vectorEffect="non-scaling-stroke" />)}</g>
      <line x1={x(index)} x2={x(index)} y1={top} y2={bottom} className="am-series-cursor" />
      {traces.map(trace => trace.values[index] != null && <ellipse key={trace.name} cx={x(index)} cy={y(trace.values[index]!)}
        rx={3.5} ry={3.5} fill={COLORS[trace.name]} />)}
      {ticks.map(i => <text key={i} x={x(i)} y={compactTicks ? height - 20 : height - 13}
        className="s2-axis" textAnchor={i === 0 ? "start" : i === span ? "end" : "middle"}>
        {tickDay(dates[i])}
        {compactTicks ? <tspan x={x(i)} dy={13}>{dates[i].slice(11, 16)}</tspan> : " " + dates[i].slice(11, 16)}
      </text>)}
    </svg></div>
    <label className="am-series-slider" htmlFor={id}>
      <span>Fecha objetivo</span>
      <input id={id} type="range" min={0} max={span} value={index}
        aria-label={`Fecha objetivo · ${label}`} aria-valuetext={dateLabel(dates[index])}
        onChange={event => select(+event.target.value)} />
      <span className="am-series-date">{dateLabel(dates[index]).slice(0, 18)}</span>
    </label>
  </>;
}

export function ForecastSeries({ openOrigin }: { openOrigin: (origin: string) => void }) {
  const [zoom, setZoom] = useState<Zoom>("week");
  const [date, setDate] = useState("2024-12-01");
  const [selection, setSelection] = useState<Selection>();
  const [start, end] = timeWindow(zoom, date);
  const dates = useMemo(() => hourGrid(start, end), [start, end]);
  const hourUrls = useMemo(() => chunkUrls(start, end), [start, end]);
  const pointUrls = useMemo(() => HORIZONS.flatMap(horizon => zoom === "year"
    ? [`/datos/sprint-3/evaluacion/h${horizon}-m0.json`]
    : hourUrls.map(url => `/datos/sprint-3/evaluacion/h${horizon}-m${+url.slice(-7, -5)}.json`)), [zoom, hourUrls]);
  const samples = useData<HourChunk[]>(hourUrls);
  const forecast = useData<EvaluationPoint[][]>(pointUrls);
  const observed = useMemo(() => samples.data ? mergeHours(samples.data, dates, "PM10") : EMPTY, [samples.data, dates]);
  const horizonData = useMemo(() => HORIZONS.map((horizon, i) => {
    const chunksPerHorizon = zoom === "year" ? 1 : hourUrls.length;
    const chunks = forecast.data?.slice(i * chunksPerHorizon, (i + 1) * chunksPerHorizon) ?? [];
    const byTarget = new Map(chunks.flat().map(point => [point.target_time, point]));
    const points = dates.map(target => byTarget.get(target));
    const traces: Trace[] = [
      { name: "observed", values: observed },
      { name: "predicted", values: points.map(point => point?.predicted ?? null) },
    ];
    return { horizon, points, traces, errors: [{ name: "error", values: points.map(point => point?.signed_error ?? null) }] as Trace[] };
  }), [dates, forecast.data, observed, hourUrls.length, zoom]);
  const peak = useMemo(() => {
    let max = 0;
    for (const { traces } of horizonData) for (const trace of traces) {
      for (const value of trace.values) if (value != null && value > max) max = value;
    }
    return Math.max(10, Math.ceil(max / 20) * 20);
  }, [horizonData]);
  const initialIndex = horizonData[0].points.findIndex(point => point != null);
  const selectedIndex = selection ? dates.indexOf(selection.target) : -1;
  const index = selectedIndex >= 0 ? selectedIndex : Math.max(0, initialIndex);
  const selectedHorizon = selection?.horizon ?? 1;
  const errorData = horizonData[selectedHorizon - 1];
  const errorPeak = useMemo(() => Math.max(10, Math.ceil(Math.max(0, ...errorData.errors[0].values.map(v => Math.abs(v ?? 0))) / 10) * 10), [errorData]);
  const choose = (i: number, horizon: number) => setSelection({ target: dates[i], horizon });

  return <>
    <Panel id="serie-pm10" title="PM₁₀ observado y predicho en 2024" question="¿Cómo cambia el pronóstico conforme aumenta el horizonte?">
      <div className="am-controls am-pred-window">
        <Select label="Intervalo de fechas objetivo" value={zoom} change={value => setZoom(value as Zoom)}>
          <option value="week">Semana</option><option value="month">Mes</option><option value="year">Todo 2024</option>
        </Select>
        {zoom === "month" && <Select label="Mes objetivo" value={+date.slice(5, 7)} change={value => setDate(`2024-${pad(+value)}-01`)}><MonthOptions /></Select>}
        {zoom === "week" && <label className="am-select"><span>Inicio de semana · 7 días</span><input aria-label="Inicio de semana" type="date" min="2024-01-01" max="2024-12-31" value={date}
          onChange={event => { const value = event.target.value; if (value >= "2024-01-01" && value <= "2024-12-31") setDate(value); }} /></label>}
      </div>
      <p className="am-note">{dateLabel(start)} a {dateLabel(end)} · hora local. Las tres gráficas comparten eje temporal y escala en µg/m³.</p>
      <div className="am-series-legend"><span>Observado</span><span>Predicción del modelo</span></div>
      <p className="am-note">Los huecos indican falta de medición o de predicción evaluada. Una concentración de cero se dibuja en la línea base. Toca o haz clic en una gráfica, o usa las flechas del control de fecha.</p>
      {!samples.data || !forecast.data ? <Loading error={samples.error ?? forecast.error} /> : horizonData.map(({ horizon, points, traces }) =>
        <section key={horizon} className="am-series-panel">
          <h3 className="display">+{horizon} {horizon === 1 ? "hora" : "horas"}</h3>
          <TimePlot dates={dates} traces={traces} domain={[0, peak]} index={index} select={i => choose(i, horizon)} label={`Observado y predicho a +${horizon} h`} />
          {selectedHorizon === horizon && <PointDetail time={dates[index]} horizon={horizon} point={points[index]} observed={observed[index]} openOrigin={openOrigin} />}
        </section>)}
    </Panel>
    <Panel id="error-temporal-pm10" title="Diferencia a lo largo del tiempo" question="¿Cuándo sobreestima o subestima el modelo?">
      <div className="am-controls"><Select label="Horizonte del error temporal" value={selectedHorizon} change={value => choose(index, +value)}>
        {HORIZONS.map(h => <option key={h} value={h}>+{h} h</option>)}
      </Select></div>
      <p className="am-note">Predicho − observado, en µg/m³. Por encima de cero hay sobreestimación; por debajo, subestimación. Se muestran pares con predicción evaluada.</p>
      {!samples.data || !forecast.data ? <Loading error={samples.error ?? forecast.error} /> :
        <div className="am-series-panel am-series-error">
          <TimePlot dates={dates} traces={errorData.errors} domain={[-errorPeak, errorPeak]} index={index} select={i => choose(i, selectedHorizon)} label={`Error temporal a +${selectedHorizon} h`} error />
          <PointDetail time={dates[index]} horizon={selectedHorizon} point={errorData.points[index]} observed={observed[index]} openOrigin={openOrigin} />
        </div>}
    </Panel>
  </>;
}
