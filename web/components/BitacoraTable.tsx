"use client";
import { useMemo, useState } from "react";
import { dec, fmt, PL } from "@/lib/aire";
import type { Bitacora } from "@/lib/types";

export function BitacoraTable({ rows }: { rows: Bitacora[] }) {
  const [f, setF] = useState("Todas");
  const clases = useMemo(() => ["Todas", ...Array.from(new Set(rows.map((b) => b.clasificacion)))], [rows]);
  const shown = rows.filter((b) => f === "Todas" || b.clasificacion === f);
  return (
    <div className="space-y-3">
      <div role="group" aria-label="Filtrar bitácora" className="flex flex-wrap gap-2">
        {clases.map((c) => {
          const n = c === "Todas" ? rows.length : rows.filter((b) => b.clasificacion === c).length;
          const on = f === c;
          return (
            <button key={c} type="button" aria-pressed={on} onClick={() => setF(c)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${on ? "border-ink bg-ink text-bg" : "border-rule bg-surface text-ink-2 hover:text-ink"}`}>
              {c} <span className="num opacity-70">{n}</span>
            </button>
          );
        })}
      </div>
      <div className="card scroll-thin max-h-[420px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface-2 text-left">
            <tr className="num text-[0.68rem] uppercase tracking-[0.1em] text-muted">
              {["Fecha y hora", "Variable", "Valor", "Clasificación", "Detalle"].map((h) => <th key={h} className="whitespace-nowrap px-3 py-2.5 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {shown.map((b, i) => (
              <tr key={i} className="border-t border-rule align-top">
                <td className="num whitespace-nowrap px-3 py-2 text-xs text-ink-2">{b.fecha_hora}</td>
                <td className="whitespace-nowrap px-3 py-2 font-medium text-ink">{PL[b.variable] ?? b.variable}</td>
                <td className="num whitespace-nowrap px-3 py-2 text-right">{b.valor == null ? "—" : fmt(b.valor, b.variable === "WS" ? 1 : dec(b.variable))}</td>
                <td className="whitespace-nowrap px-3 py-2"><span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs text-ink-2">{b.clasificacion}</span></td>
                <td className="min-w-[280px] px-3 py-2 text-ink-2"><span className="text-muted">{b.regla}. </span>{b.detalle}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
