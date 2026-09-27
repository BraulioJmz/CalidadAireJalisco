import type { ReactNode } from "react";
import { catVar, onVar } from "@/lib/aire";

/** Contaminante con subíndice real. */
export function Pol({ p }: { p: string }) {
  if (p === "PM10") return <>PM<sub>10</sub></>;
  if (p === "PM2.5") return <>PM<sub>2.5</sub></>;
  if (p === "O3") return <>O<sub>3</sub></>;
  if (p === "NO2") return <>NO<sub>2</sub></>;
  if (p === "SO2") return <>SO<sub>2</sub></>;
  return <>{p || "—"}</>;
}

export function CatPill({ c, size = "sm" }: { c: string; size?: "sm" | "md" | "lg" }) {
  const cls = size === "lg" ? "px-4 py-2 text-lg" : size === "md" ? "px-3 py-1.5 text-sm" : "px-2.5 py-1 text-xs";
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full font-semibold ${cls}`} style={{ background: catVar(c), color: onVar(c) }}>
      {c}
    </span>
  );
}

export function Kpi({ value, unit, label, tone }: { value: ReactNode; unit?: string; label: ReactNode; tone?: "alert" }) {
  return (
    <div className="card flex flex-col gap-1.5 p-5">
      <div className={`display text-4xl font-semibold leading-none ${tone === "alert" ? "text-[var(--c-muymala)]" : "text-ink"}`}>
        <span className="num font-sans text-[2.1rem] font-semibold tracking-tight">{value}</span>
        {unit && <span className="ml-1.5 font-sans text-sm font-medium text-muted">{unit}</span>}
      </div>
      <p className="text-sm leading-snug text-ink-2">{label}</p>
    </div>
  );
}

export function SectionHead({ id, n, eyebrow, title, children }: { id?: string; n?: string; eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <div id={id} className="scroll-mt-24 space-y-3">
      <p className="eyebrow">{n ? `${n} · ` : ""}{eyebrow}</p>
      <h2 className="display text-3xl font-medium leading-[1.1] text-ink sm:text-[2.6rem]">{title}</h2>
      {children && <div className="prose-aire space-y-3">{children}</div>}
    </div>
  );
}

export function Legend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-ink-2">
      {["Buena", "Aceptable", "Mala", "Muy Mala", "Extremadamente Mala", "Sin datos"].map((c) => (
        <span key={c} className="inline-flex items-center gap-1.5">
          <i className="inline-block size-3 rounded-[3px]" style={{ background: catVar(c) }} />{c}
        </span>
      ))}
    </div>
  );
}

export function QA({ q, children }: { q: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-base font-semibold text-ink">{q}</h3>
      <div className="prose-aire">{children}</div>
    </div>
  );
}
