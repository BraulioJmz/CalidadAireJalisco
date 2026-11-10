"use client";
import { useEffect, useState, type ReactNode } from "react";
import { Motion, useEntrance } from "@/components/sprint2/Motion";
import { Lines, type LineProps } from "./Lines";
import { fmt, MONTHS } from "@/lib/academia";

const cache = new Map<string, unknown>();
export function useData<T>(urls: string | string[] | null) {
  const key = urls == null ? "" : typeof urls === "string" ? urls : urls.join("|");
  const [state, setState] = useState<{ key: string; data?: T; error?: string }>({ key: "" });
  useEffect(() => {
    if (!key) return;
    const controller = new AbortController();
    const list = key.split("|");
    Promise.all(list.map(async url => {
      if (cache.has(url)) return cache.get(url);
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error(`No se pudo cargar la consulta (${response.status}).`);
      const data = await response.json(); cache.set(url, data); return data;
    })).then(rows => { if (!controller.signal.aborted) setState({ key, data: (Array.isArray(urls) ? rows : rows[0]) as T }); })
      .catch(error => { if (!controller.signal.aborted) setState({ key, error: String(error.message) }); });
    return () => controller.abort();
  }, [key]); // La clave incluye todos los recursos; se cancela cualquier consulta sustituida.
  return { data: state.key === key ? state.data : undefined, error: state.key === key ? state.error : undefined };
}
export function Loading({ error }: { error?: string }) { return <p className="am-status" role="status">{error ?? "Cargando resultados de esta consulta…"}</p>; }
export function Select({ label, value, change, children }: { label: string; value: string | number; change: (v: string) => void; children: ReactNode }) {
  return <label className="am-select"><span>{label}</span><select aria-label={label} value={value} onChange={e => change(e.target.value)}>{children}</select></label>;
}
export function MonthOptions({ all = false }: { all?: boolean }) { return <>{all && <option value={0}>Todo el año</option>}{MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}</>; }
export function Panel({ title, question, children, id }: { title: string; question: string; children: ReactNode; id?: string }) {
  return <section className="am-panel card" id={id}><header><p className="eyebrow">{question}</p><h2 className="display">{title}</h2></header>{children}</section>;
}
export function Table({ label, children }: { label: string; children: ReactNode }) { return <div className="am-table-wrap" role="region" aria-label={label} tabIndex={0}><table className="am-table">{children}</table></div>; }
export function LineChart(props: LineProps) {
  if (!props.series.some(s => s.values.some(v => v !== null))) return <p className="am-status">Sin valores o cobertura suficiente para esta consulta. Los vacíos se conservan; revise los denominadores.</p>;
  return <Lines {...props} />;
}
export function PointChart({ points, title, xLabel, yLabel, identity = false, zero = false }: {
  points: { x: number; y: number; label: string }[]; title: string; xLabel: string; yLabel: string; identity?: boolean; zero?: boolean;
}) {
  const ref = useEntrance<SVGGElement>(JSON.stringify([points, title]), "reveal");
  if (!points.length) return <p className="am-status">Sin pares observados para esta consulta.</p>;
  const xs = points.map(p => p.x), ys = points.map(p => p.y);
  let minX = Math.min(...xs, 0), maxX = Math.max(...xs, .01), minY = Math.min(...ys, 0), maxY = Math.max(...ys, .01);
  if (identity) { minX = minY = Math.min(minX, minY); maxX = maxY = Math.max(maxX, maxY); }
  const dx = maxX - minX || 1, dy = maxY - minY || 1;
  const x = (v: number) => 66 + (v - minX) / dx * 690, y = (v: number) => 275 - (v - minY) / dy * 240;
  return <div className="s2-plot" tabIndex={0} aria-label={title}><svg viewBox="0 0 800 335" role="img" aria-label={title}>
    <title>{title} · n={points.length}. Todos los puntos de la consulta.</title>
    {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1={66} x2={756} y1={y(minY + dy * i / 4)} y2={y(minY + dy * i / 4)} className="s2-grid" /><text className="s2-axis" x={58} y={y(minY + dy * i / 4) + 4} textAnchor="end">{fmt(minY + dy * i / 4, maxY < 1 ? 3 : 1)}</text><text className="s2-axis" x={x(minX + dx * i / 4)} y={300} textAnchor="middle">{fmt(minX + dx * i / 4, maxX < 1 ? 3 : 1)}</text></g>)}
    {identity && <line x1={x(minX)} y1={y(minX)} x2={x(maxX)} y2={y(maxX)} stroke="var(--muted)" strokeDasharray="6 4" />}
    {zero && <line x1={66} x2={756} y1={y(0)} y2={y(0)} stroke="var(--ink)" />}
    <g ref={ref} className="am-point-reveal">{points.map((p, i) => <circle key={i} cx={x(p.x)} cy={y(p.y)} r={points.length > 1000 ? 2.2 : 3.5} fill="var(--accent)" fillOpacity={.48}><title>{p.label} · {fmt(p.x, 6)} / {fmt(p.y, 6)}</title></circle>)}</g>
    <text x={66} y={17} className="s2-axis">{yLabel}</text><text x={410} y={329} textAnchor="middle" className="s2-axis">{xLabel}</text>
  </svg></div>;
}
export function Categories({ counts, expected, categories, legend = true }: { legend?: boolean; counts: number[] | null; expected: number; categories: { code: number; name: string; color: string; ink: string }[] }) {
  const ref = useEntrance<HTMLDivElement>(JSON.stringify([counts, expected]), "reveal");
  if (!counts) return <p className="am-status">Esta variable no tiene categorías normativas en este análisis.</p>;
  const missing = expected - counts.reduce((a, b) => a + b, 0);
  return <><div ref={ref} className="am-category-bar" aria-label="Distribución sobre todos los días esperados">{counts.map((n, i) => n > 0 && <div key={i} style={{ width: `${100 * n / expected}%`, background: categories[i].color, color: categories[i].ink }} title={`${categories[i].name}: ${n}/${expected}`} />)}{missing > 0 && <div className="am-missing" style={{ width: `${100 * missing / expected}%` }} title={`Sin indicador: ${missing}/${expected}`} />}</div>
    {legend && <ul className="am-category-legend">{categories.map((c, i) => <li key={c.code}><i style={{ background: c.color }} />{c.name}: <b>{counts[i]}</b></li>)}<li><i className="am-missing" />Sin indicador: <b>{missing}</b></li></ul>}</>;
}
export function Sections({ labels, active, change, label }: { labels: string[]; active: number; change: (i: number) => void; label: string }) {
  return <nav className="am-sections" aria-label={label}>{labels.map((text, i) => <button type="button" key={text} aria-current={active === i ? "page" : undefined} onClick={() => change(i)}>{text}</button>)}</nav>;
}
export { Motion };
