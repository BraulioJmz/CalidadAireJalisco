"use client";
import { useLayoutEffect, useRef, useState } from "react";
import type { PlotSeries } from "@/components/sprint2/Charts";
import { useEntrance } from "@/components/sprint2/Motion";
import { fmt } from "@/lib/academia";

export type LineProps = { labels: string[]; series: PlotSeries[]; unit: string; title: string; timestamps?: string[]; maximum?: number; originIndex?: number };

/** Representación local: no altera el componente ni los estilos de las versiones archivadas. */
export function Lines({ labels, series, unit, title, timestamps, maximum, originIndex }: LineProps) {
  const container = useRef<HTMLDivElement>(null), [width, setWidth] = useState(900);
  const reveal = useEntrance<SVGGElement>(JSON.stringify([labels, series, unit, title]), "reveal");
  useLayoutEffect(() => {
    const measure = () => { if (container.current) setWidth(Math.max(280, Math.round(container.current.clientWidth))); };
    measure(); const observer = new ResizeObserver(measure); if (container.current) observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  const temporal = labels.some(label => /[T ]\d{2}:\d{2}/.test(label));
  const h = 320, left = 56, right = 16, top = 32, bottom = temporal ? 65 : 48;
  const values = series.flatMap(s => s.values.filter((v): v is number => v !== null));
  const max = Math.max(maximum ?? Math.max(...values, .001), .001) * 1.12;
  const x = (i: number) => left + i / Math.max(1, labels.length - 1) * (width - left - right);
  const y = (v: number) => h - bottom - v / max * (h - top - bottom);
  const tickCount = Math.min(labels.length, temporal ? 6 : 8, Math.max(2, Math.floor((width - left - right) / (temporal ? 100 : 80)) + 1));
  const ticks = [...new Set(Array.from({ length: tickCount }, (_, i) => Math.round(i * (labels.length - 1) / Math.max(1, tickCount - 1))))];
  return <>
    <div ref={container} className="s2-plot am-line-plot" tabIndex={0} aria-label={title}>
      <svg viewBox={`0 0 ${width} ${h}`} role="img" aria-label={title} data-domain-max={max} data-samples={labels.length}>
        <title>{title}</title><text x={left} y={16} className="s2-axis">{unit}</text>
        {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1={left} x2={width - right} y1={y(max * i / 4)} y2={y(max * i / 4)} className="s2-grid" /><text x={left - 8} y={y(max * i / 4) + 4} textAnchor="end" className="s2-axis">{fmt(max * i / 4, max < 1 ? 3 : 1)}</text></g>)}
        {ticks.map(i => { const parts = temporal ? labels[i].replace("T", " ").split(" ") : [labels[i]]; return <text key={i} data-axis-tick={i} x={x(i)} y={h - (temporal ? 37 : 20)} textAnchor={i === 0 ? "start" : i === labels.length - 1 ? "end" : "middle"} className="s2-axis"><tspan x={x(i)}>{parts[0]}</tspan>{temporal && <tspan x={x(i)} dy={16}>{parts.slice(1).join(" ")}</tspan>}</text>; })}
        {originIndex != null && <g className="am-origin-marker"><line x1={x(originIndex)} x2={x(originIndex)} y1={top} y2={h - bottom} stroke="var(--muted)" strokeDasharray="3 5" /><text x={x(originIndex) - 4} y={top - 7} textAnchor="end" className="s2-axis">Origen</text></g>}
        <g ref={reveal} className="s2-line-reveal">{series.map(s => <g key={s.name} data-series={s.name}>
          {s.values.map((v, i) => v !== null && i > 0 && s.values[i - 1] !== null && <line key={`l${i}`} x1={x(i - 1)} x2={x(i)} y1={y(s.values[i - 1]!)} y2={y(v)} stroke={s.color} strokeWidth={2.4} strokeDasharray={s.dash ? "7 5" : undefined} />)}
          {s.values.map((v, i) => v !== null && <circle key={i} cx={x(i)} cy={y(v)} r={labels.length > 40 ? 2.2 : 4} fill={s.color} data-time={timestamps?.[i]} data-value={v}><title>{`${s.name} · ${timestamps?.[i] ?? labels[i]}: ${fmt(v, 6)} ${unit}${s.n ? ` · n=${s.n[i]}` : ""}`}</title></circle>)}
        </g>)}</g>
      </svg>
    </div>
    <div className="s2-legend">{series.map(s => <span key={s.name}><i style={{ background: s.color }} />{s.name}{s.dash ? " · línea discontinua" : ""}</span>)}<span>Los huecos no se conectan.</span></div>
  </>;
}
