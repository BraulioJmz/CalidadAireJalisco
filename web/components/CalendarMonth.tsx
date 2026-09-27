"use client";
import { useRouter } from "next/navigation";
import { catVar, dec, fmt, onVar, parseT, PL } from "@/lib/aire";
import type { DayRec } from "@/lib/types";

type Props = {
  diario: DayRec[];
  horas: string[][]; // categoría global de cada hora, por día
  unidades: Record<string, string>;
  /** Si se indica, al tocar un día se navega a esa ruta (?dia=N). Si no, se avisa a la simulación de la misma página. */
  hrefBase?: string;
  compact?: boolean;
};

const DOWS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];

export function CalendarMonth({ diario, horas, unidades, hrefBase, compact }: Props) {
  const router = useRouter();
  const p0 = parseT(diario[0].FECHA + " 00:00");
  const lead = (new Date(p0.y, p0.m - 1, 1).getDay() + 6) % 7;
  const go = (dia: number) => {
    if (hrefBase) { router.push(`${hrefBase}?dia=${dia}#simulacion`); return; }
    window.dispatchEvent(new CustomEvent("sim:dia", { detail: dia }));
    document.getElementById("simulacion")?.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  };
  return (
    <div className="scroll-thin overflow-x-auto pb-1">
      <div className={`grid min-w-[760px] grid-cols-7 gap-1.5 ${compact ? "" : "lg:gap-2"}`}>
        {DOWS.map((d) => <div key={d} className="num px-1 pb-1 text-[0.68rem] uppercase tracking-[0.12em] text-muted">{d}</div>)}
        {Array.from({ length: lead }, (_, i) => <div key={`e${i}`} />)}
        {diario.map((d, i) => {
          const c = d.Cat_global; const sin = c === "Sin datos";
          const resp = d.Responsable;
          const ind = sin ? "" : `${PL[resp]} · ${fmt(d[`${resp}_indicador`], dec(resp))} ${unidades[resp]}`;
          return (
            <button key={d.FECHA} type="button" onClick={() => go(i + 1)}
              aria-label={`${i + 1}: ${c}${sin ? "" : ", " + ind}. Ver en la simulación`}
              className={`group flex flex-col gap-1 rounded-xl p-2.5 text-left transition hover:-translate-y-0.5 hover:shadow-lg focus-visible:-translate-y-0.5 ${compact ? "min-h-[92px]" : "min-h-[116px]"} ${sin ? "border border-dashed border-rule bg-surface text-ink-2" : ""}`}
              style={sin ? undefined : { background: catVar(c), color: onVar(c) }}>
              <span className="flex items-center justify-between">
                <span className="num text-xs font-semibold">{i + 1}</span>
                {d.evento_sigla && <span title={d.evento ?? ""} className="num rounded bg-black/15 px-1 py-px text-[0.6rem] tracking-wider">{d.evento_sigla}</span>}
              </span>
              <span className="display text-[1.02rem] font-semibold leading-tight">{c}</span>
              {!compact && <span className="text-[0.72rem] leading-snug opacity-90">{sin ? "Sin suficiencia" : ind}</span>}
              <span className="mt-auto grid grid-cols-24 gap-px rounded bg-[var(--surface)] p-[2px]" style={{ gridTemplateColumns: "repeat(24, minmax(0, 1fr))" }}>
                {(horas[i] ?? []).map((hc, h) => <i key={h} title={`${String(h).padStart(2, "0")}:00 · ${hc}`} className="block h-2 rounded-[1px]" style={{ background: catVar(hc) }} />)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
