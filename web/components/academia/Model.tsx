"use client";
import { useEffect, useState } from "react";
import type { EvaluationPoint, HourChunk, Metric, Metrics, Prediction, Summary } from "@/lib/academia";
import { chunkUrls, dateLabel, fmt, hourGrid, mergeHours, MONTHS, pad, shiftHour } from "@/lib/academia";
import { LineChart, Loading, MonthOptions, Motion, Panel, PointChart, Select, Table, useData } from "./Shared";

export function ModelScope({ summary }: { summary: Summary }) {
  return <div className="am-model-scope"><b>PM₁₀ · evaluación retrospectiva de 2024</b><p>{summary.model.n.toLocaleString("es-MX")} orígenes evaluados / {summary.model.expected.toLocaleString("es-MX")} horas ({fmt(summary.model.coverage, 1)} %). No es un pronóstico operativo actual. El modelo tiende a subestimar concentraciones altas.</p><details><summary>Qué población se evaluó</summary><p>Hay {summary.model.rawN.toLocaleString("es-MX")} horas con PM10 observado (91.7 %). La comparación exige 24 observaciones previas y los tres objetivos disponibles. 2024 ya fue explorado descriptivamente; no es una prueba ciega. Los huecos condicionan las horas evaluadas.</p></details></div>;

}

export function PredictionView({ summary }: { summary: Summary }) {
  const [month, setMonth] = useState(12), [origin, setOrigin] = useState(""), [hours, setHours] = useState(48);
  const result = useData<Prediction[]>(`/datos/sprint-3/predicciones/2024-${pad(month)}.json`);
  useEffect(() => { if (result.data && !origin) setOrigin(result.data[0]?.origin ?? ""); }, [result.data, origin]);
  const selected = result.data?.find(r => r.origin.slice(0, 16) === origin.slice(0, 16));
  const normalized = origin.length === 16 ? `${origin}:00` : origin;
  const fullGrid = normalized ? hourGrid(shiftHour(normalized, -47), shiftHour(normalized, 3)) : [];
  const context = useData<HourChunk[]>(fullGrid.length ? chunkUrls(fullGrid[0], fullGrid[fullGrid.length - 1]) : null);
  const allObserved = mergeHours(context.data ?? null, fullGrid, "PM10");
  const grid = fullGrid.slice(48 - hours), observed = allObserved.slice(48 - hours);
  const maximum = Math.max(...allObserved.filter((v): v is number => v !== null), ...(selected?.models.HGB.predicted ?? []), .001);
  const at = result.data?.findIndex(r => r.origin === selected?.origin) ?? -1;
  return <>
    <Panel title="Un origen, tres horizontes" question="¿Qué anticipó el modelo desde una hora concreta y qué se observó después?">
      <div className="am-controls am-pred-controls"><Select label="Mes de origen · 2024" value={month} change={v => { setMonth(+v); setOrigin(""); }}><MonthOptions /></Select>
        <label className="am-select am-origin-input"><span>Origen t · hora local de los datos</span><input type="datetime-local" step={3600} value={origin.slice(0, 16)} min={`2024-${pad(month)}-01T00:00`} max={`2024-${pad(month)}-${pad(new Date(Date.UTC(2024, month, 0)).getUTCDate())}T23:00`} onChange={e => setOrigin(e.target.value)} /></label>
        <div className="am-origin-steps"><button type="button" aria-label="Origen disponible anterior" disabled={at <= 0} onClick={() => setOrigin(result.data![at - 1].origin)}>← Anterior</button><button type="button" aria-label="Siguiente origen disponible" disabled={at < 0 || at >= (result.data?.length ?? 0) - 1} onClick={() => setOrigin(result.data![at + 1].origin)}>Siguiente →</button></div></div>
      {!result.data ? <Loading error={result.error} /> : !selected ? <p className="am-status" role="status">Este origen no pertenece a la evaluación completa. No se imputan ni se generan pronósticos para las interrupciones. Elige otro origen disponible.</p> : <Motion signal={selected.origin} preset="detail">
        <p className="am-origin"><span className="eyebrow">Origen de emisión</span><b>{dateLabel(selected.origin)}</b></p>
        <div className="am-forecast-summary" role="list" aria-label="Resumen de los tres horizontes">{[0, 1, 2].map(i => <article role="listitem" className="am-forecast-card" key={i} data-horizon={i + 1} data-target={selected.target[i]}><h3>+{i + 1} hora{i ? "s" : ""}</h3><p className="am-target-label">Fecha objetivo</p><time dateTime={selected.target[i]}><span>{selected.target[i].slice(0,10)}</span><b>{selected.target[i].slice(11,16)}</b></time><dl><div><dt>Concentración observada</dt><dd>{fmt(selected.observed[i])} <small>µg/m³</small></dd></div><div><dt>Predicción del modelo</dt><dd>{fmt(selected.models.HGB.predicted[i])} <small>µg/m³</small></dd></div><div><dt>Diferencia</dt><dd>{selected.models.HGB.error[i] > 0 ? "+" : ""}{fmt(selected.models.HGB.error[i])} <small>µg/m³</small></dd></div></dl></article>)}</div>
        <p className="am-note">Diferencia = predicción − observado. Un valor positivo indica sobreestimación; uno negativo, subestimación. Los observados posteriores al origen solo sirven para contrastar el resultado.</p>
        <details className="am-prediction-detail"><summary>Tabla ampliada y referencias</summary><Table label="Pronósticos de PM10 y observados"><thead><tr><th>Horizonte</th><th>Fecha objetivo</th><th>Observado</th><th>Predicción del modelo</th><th>Diferencia</th><th>Última lectura conocida</th><th>Misma hora del día anterior</th></tr></thead><tbody>{[0, 1, 2].map(i => <tr key={i}><th>+{i + 1} h</th><td>{dateLabel(selected.target[i])}</td><td>{fmt(selected.observed[i])}</td><td>{fmt(selected.models.HGB.predicted[i])}</td><td>{fmt(selected.models.HGB.error[i])}</td><td>{fmt(selected.models.persistencia.predicted[i])}</td><td>{fmt(selected.models.diaria.predicted[i])}</td></tr>)}</tbody></Table><p className="am-note">Concentraciones y diferencias en µg/m³. «Última lectura conocida» repite la concentración del origen en los tres horizontes (persistencia). «Misma hora del día anterior» usa la lectura de 24 horas antes de cada fecha objetivo.</p></details>
      </Motion>}
    </Panel>
    {normalized && <Panel id="prediccion-contexto" title="Contexto observado y continuación predicha" question="¿Cómo se sitúan los tres pronósticos respecto al contexto observado?">
      <div className="am-controls"><Select label="Horas de contexto observado" value={hours} change={v => setHours(+v)}>{[6,12,48].map(h => <option key={h} value={h}>Últimas {h} horas + 3 horizontes</option>)}</Select></div>
      {!context.data ? <Loading error={context.error} /> : <LineChart title={`PM10 observado y predicho desde ${dateLabel(normalized)}`} labels={grid.map(t => t.slice(5, 16).replace("T", " "))} timestamps={grid} maximum={maximum} originIndex={hours - 1} unit="µg/m³" series={[
        { name: "Observado hasta el origen", color: "#26394d", values: grid.map((t, i) => t <= normalized ? observed[i] : null) },
        { name: "Observado posterior · solo evaluación", color: "#637e92", values: grid.map((t, i) => t > normalized ? observed[i] : null) },
        { name: "Predicción del modelo", color: "#b65327", dash: true, values: grid.map(t => { const i = selected?.target.indexOf(t) ?? -1; return i >= 0 ? selected!.models.HGB.predicted[i] : null; }) },
      ]} />}
      <p className="am-note">Desde {dateLabel(grid[0])} hasta {dateLabel(grid[grid.length - 1])}. Las {hours} horas de contexto incluyen el origen. El acercamiento conserva la escala vertical del contexto completo de 48 horas y los tres horizontes.</p>
      <p className="am-callout">Son concentraciones horarias, no categorías del Índice AIRE Y SALUD: clasificar PM10 requiere las ventanas y reglas correspondientes. El umbral diagnóstico de {summary.model.threshold} µg/m³ tampoco es una categoría normativa.</p>
    </Panel>}
  </>;
}

const modelLabel: Record<string, string> = { HGB: "Modelo", persistencia: "Última lectura conocida", diaria: "Misma hora del día anterior" };

function MetricTable({ rows }: { rows: Metric[] }) {
  return <Table label="Métricas congeladas del modelo y referencias"><thead><tr><th>Modelo</th><th>Horizonte</th><th>n</th><th>MAE</th><th>RMSE</th><th>R²</th><th>Sesgo</th></tr></thead><tbody>{[1, 2, 3].flatMap(h => ["HGB", "persistencia", "diaria"].map(model => { const r = rows.find(r => r.horizon === h && r.model === model); return r ? <tr key={`${h}-${model}`}><th>{modelLabel[model]}</th><td>+{h} h</td><td>{r.n.toLocaleString("es-MX")}</td><td>{fmt(r.mae)}</td><td>{fmt(r.rmse)}</td><td title={r.r2_reason ?? ""}>{r.r2 == null ? `No calculable (${r.r2_reason})` : fmt(r.r2, 3)}</td><td>{fmt(r.bias)}</td></tr> : null; }))}</tbody></Table>;
}

export function Evaluation({ summary }: { summary: Summary }) {
  const [month, setMonth] = useState(0), [horizon, setHorizon] = useState(1);
  const metrics = useData<Metrics>("/datos/sprint-3/metricas.json");
  const points = useData<EvaluationPoint[]>(`/datos/sprint-3/evaluacion/h${horizon}-m${month}.json`);
  const rows = metrics.data ? (month === 0 ? metrics.data.globales : metrics.data.mensuales).filter(r => r.partition === "test" && (month === 0 || r.month === month)) : [];
  const high = metrics.data?.altas.filter(r => r.partition === "test" && r.month === month) ?? [];
  const lineMetrics = metrics.data?.mensuales.filter(r => r.partition === "test" && r.horizon === horizon) ?? [];
  return <>
    <Panel id="evaluacion-error" title="Evaluar frente a dos referencias" question="¿Cuánto error tiene cada horizonte sobre las mismas fechas evaluadas?">
      <div className="am-controls"><Select label="Mes de fecha objetivo · 2024" value={month} change={v => setMonth(+v)}><MonthOptions all /></Select><Select label="Horizonte de las gráficas" value={horizon} change={v => setHorizon(+v)}>{[1, 2, 3].map(h => <option key={h} value={h}>+{h} horas</option>)}</Select></div>
      {!metrics.data ? <Loading error={metrics.error} /> : <><MetricTable rows={rows} /><p className="am-note">Las referencias usan la última lectura del origen (persistencia) o la misma hora objetivo del día anterior. No necesitan observaciones futuras.</p><p className="am-note">MAE, RMSE y sesgo en µg/m³; R² adimensional y conservado aunque sea negativo. El filtro mensual usa la fecha objetivo; no el mes del origen. El conjunto global es idéntico entre horizontes y modelos. Los n mensuales pueden variar al cruzar un mes entre horizontes.</p>
      <LineChart title={`MAE mensual 2024 a +${horizon} h`} unit="MAE · µg/m³" labels={MONTHS.map(m => m.slice(0, 3))} series={["HGB", "persistencia", "diaria"].map((model, i) => ({ name: modelLabel[model], color: ["#b65327", "#2c56cf", "#657790"][i], values: MONTHS.map((_, j) => lineMetrics.find(r => r.model === model && r.month === j + 1)?.mae ?? null), n: MONTHS.map((_, j) => lineMetrics.find(r => r.model === model && r.month === j + 1)?.n ?? 0) }))} />
      <details><summary>Concentraciones altas: observado ≥114 µg/m³</summary><p className="am-note">Percentil 90 de las horas utilizables de entrenamiento 2015–2022, no una banda normativa. El modelo tiende a subestimar estas concentraciones; los R² de ese estrato pueden ser negativos.</p><MetricTable rows={high} /></details></>}
    </Panel>
    <div className="am-grid-2"><Panel title="Observado frente a predicho" question="¿Dónde se apartan los pronósticos de las concentraciones observadas?">
      {!points.data ? <Loading error={points.error} /> : <><PointChart title={`Dispersión del modelo 2024 +${horizon} h`} xLabel="Observado (µg/m³)" yLabel="Predicho (µg/m³)" identity points={points.data.map(p => ({ x: p.observed, y: p.predicted, label: `Origen ${p.origin}; objetivo ${p.target_time}` }))} /><p className="am-note">n={points.data.length.toLocaleString("es-MX")} puntos, todos los de la consulta. La diagonal indica coincidencia; se conservan los extremos.</p></>}
    </Panel><Panel title="Error firmado" question="¿Cuándo sobreestima y cuándo subestima el modelo?">
      {!points.data ? <Loading error={points.error} /> : <><PointChart title={`Error firmado del modelo 2024 +${horizon} h`} xLabel="Observado (µg/m³)" yLabel="Predicho − observado (µg/m³)" zero points={points.data.map(p => ({ x: p.observed, y: p.signed_error, label: `Origen ${p.origin}; objetivo ${p.target_time}` }))} /><p className="am-note">Positivo: sobreestimación. Negativo: subestimación. El sesgo global pequeño puede ocultar subestimación de los picos.</p></>}
    </Panel></div>
    <details className="am-experiment"><summary>Protocolo y límites de interpretación</summary><Panel title="Alcance de la evaluación" question="¿Hasta dónde llega la evidencia predictiva y qué sigue sin demostrar?">
      <p>Entrenamiento 2015–2022, selección con 2023 y reajuste 2015–2023 antes de evaluar 2024. La configuración se eligió antes de evaluar 2024 y permanece congelada.</p>
      <p>El MAE global mejora frente a la referencia de la última lectura conocida, pero no en todos los meses: julio de 2024 a +1 h es ligeramente peor. En concentraciones altas hay subestimación, con R² negativos a +2 y +3 h. No se ajustaron decisiones usando estos errores.</p>
      <p>Los huecos condicionan la población del 70.9 %; las ventanas se solapan y no son observaciones independientes. No demuestra disponibilidad en tiempo real, ausencia de retrasos, calibración instrumental, causalidad ni desempeño en las horas omitidas.</p>
    </Panel></details>
  </>;
}
