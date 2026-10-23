"use client";
import type { ContextPoint, MeteoS2 } from "@/lib/sprint2-contract";
import { useEntrance } from "./Motion";

export const f = (v: number | null | undefined, decimals = 2) => v == null ? "Sin dato" : v.toLocaleString("es-MX", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
export type PlotSeries = { name: string; color: string; values: (number | null)[]; n?: number[]; dash?: boolean };

export function Lines({ labels, series, unit, title }: { labels: string[]; series: PlotSeries[]; unit: string; title: string }) {
  const reveal = useEntrance<SVGGElement>(JSON.stringify([labels, series, unit, title]), "reveal");
  const w = 900, h = 315, left = 62, right = 22, top = 28, bottom = 53;
  const values = series.flatMap(s => s.values.filter((v): v is number => v !== null));
  if (!values.length) return <p className="s2-empty">Sin indicadores suficientes para este periodo. Los vacíos se conservan.</p>;
  const max = Math.max(...values, 0.001) * 1.12;
  const x = (i: number) => left + i / Math.max(1, labels.length - 1) * (w - left - right);
  const y = (v: number) => h - bottom - v / max * (h - top - bottom);
  return <>
    <div className="s2-plot" tabIndex={0} aria-label="Gráfica desplazable horizontalmente">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={title}>
        <title>{title}</title><text x={left} y={15} className="s2-axis">{unit}</text>
        {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1={left} x2={w - right} y1={y(max * i / 4)} y2={y(max * i / 4)} className="s2-grid" /><text x={left - 9} y={y(max * i / 4) + 4} textAnchor="end" className="s2-axis">{f(max * i / 4, max < 1 ? 3 : 1)}</text></g>)}
        {labels.map((label, i) => (i % Math.max(1, Math.ceil(labels.length / 12)) === 0 || i === labels.length - 1) && <text key={i} x={x(i)} y={h - 26} textAnchor="middle" className="s2-axis">{label}</text>)}
        <g ref={reveal} className="s2-line-reveal">{series.map(s => <g key={s.name}>
          {s.values.map((v, i) => v !== null && i > 0 && s.values[i - 1] !== null && <line key={`l${i}`} x1={x(i - 1)} x2={x(i)} y1={y(s.values[i - 1]!)} y2={y(v)} stroke={s.color} strokeWidth={2.7} strokeDasharray={s.dash ? "7 5" : undefined} />)}
          {s.values.map((v, i) => v !== null && <circle key={i} cx={x(i)} cy={y(v)} r={labels.length > 40 ? 2 : 4.5} fill={s.color}><title>{`${s.name} · ${labels[i]}: ${f(v, 6)} ${unit}${s.n ? ` · n=${s.n[i]}` : ""}`}</title></circle>)}
        </g>)}</g>
      </svg>
    </div>
    <div className="s2-legend">{series.map(s => <span key={s.name}><i style={{ background: s.color }} />{s.name}{s.dash ? " · línea discontinua" : ""}</span>)}<span>Huecos: sin indicador; no se conectan.</span></div>
  </>;
}

export function Context({ points, unit, title, daily = false }: { points: ContextPoint[]; unit: string; title: string; daily?: boolean }) {
  return <Lines labels={points.map(p => daily ? p.t.slice(5, 10) : `${p.t.slice(5, 10)} ${p.t.slice(11, 16)}`)}
    series={[...(daily ? [] : [{ name: "Lectura cruda", color: "#8b95a7", values: points.map(p => p.raw), dash: true }]),
      { name: daily ? "Base diaria antes del redondeo" : "Indicador horario", color: "#2c56cf", values: points.map(p => p.indicator) }]}
    unit={unit} title={title} />;
}

export function Scatter({ row, variableUnit, concentrationUnit, variableLabel }: { row: MeteoS2; variableUnit: string; concentrationUnit: string; variableLabel: string }) {
  if (!row.points.length) return <p className="s2-empty">Sin pares coincidentes en este mes. La ausencia de datos no indica ausencia de contaminación.</p>;
  const w = 800, h = 330, left = 65, top = 22, bottom = 58, right = 22;
  const xs = row.points.map(p => p[1]), ys = row.points.map(p => p[2]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = maxX - minX || 1, spanY = maxY - minY || Math.max(maxY, 0.01);
  const x = (v: number) => left + 14 + (v - minX) / spanX * (w - left - right - 28);
  const y = (v: number) => h - bottom - 12 - (v - minY) / spanY * (h - top - bottom - 24);
  return <div className="s2-plot" tabIndex={0}>
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Dispersión de ${variableLabel} y concentración diaria, ${row.n} pares`}>
      <title>Asociación descriptiva de observaciones coincidentes; no causalidad</title>
      {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1={left} x2={w - right} y1={y(minY + spanY * i / 4)} y2={y(minY + spanY * i / 4)} className="s2-grid" /><text x={left - 8} y={y(minY + spanY * i / 4) + 4} textAnchor="end" className="s2-axis">{f(minY + spanY * i / 4, maxY < 1 ? 3 : 1)}</text><text x={x(minX + spanX * i / 4)} y={h - 36} textAnchor="middle" className="s2-axis">{f(minX + spanX * i / 4, 1)}</text></g>)}
      <text x={left} y={14} className="s2-axis">{concentrationUnit}</text><text x={w / 2} y={h - 8} textAnchor="middle" className="s2-axis">{variableLabel} ({variableUnit})</text>
      <g key={JSON.stringify(row.points)}>{row.points.map((p, i) => <circle key={p[0]} className="s2-scatter-point" style={{ animationDelay: `${Math.min(i, 12) * 12}ms` }} cx={x(p[1])} cy={y(p[2])} r={5} fill="#2c56cf" fillOpacity={0.7} stroke="var(--surface)"><title>{`${p[0]} · ${f(p[1], 6)} ${variableUnit} · ${f(p[2], 6)} ${concentrationUnit}`}</title></circle>)}</g>
    </svg>
  </div>;
}
