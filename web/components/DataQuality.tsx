import { fmt, PL } from "@/lib/aire";
import type { Variable } from "@/lib/types";

export function VariablesTable({ vars }: { vars: Variable[] }) {
  const d = (v: string) => (["O3", "NO", "NO2", "NOX", "SO2", "CO"].includes(v) ? 3 : v === "WS" ? 1 : 0);
  return (
    <div className="card scroll-thin overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-surface-2 text-left">
          <tr className="num text-[0.68rem] uppercase tracking-[0.1em] text-muted">
            <th className="px-3 py-2.5 font-medium">Variable</th><th className="px-3 py-2.5 font-medium">Unidad</th>
            <th className="px-3 py-2.5 text-right font-medium">Válidos</th><th className="px-3 py-2.5 font-medium">Disponibilidad</th>
            <th className="px-3 py-2.5 text-right font-medium">Mín</th><th className="px-3 py-2.5 text-right font-medium">Mediana</th><th className="px-3 py-2.5 text-right font-medium">Máx</th>
          </tr>
        </thead>
        <tbody>
          {vars.map((v) => {
            const empty = v.validos === 0;
            return (
              <tr key={v.variable} className={`border-t border-rule ${empty ? "text-muted" : "text-ink"}`}>
                <td className="whitespace-nowrap px-3 py-2"><b className="font-semibold">{PL[v.variable] ?? v.variable}</b> <span className="text-muted">{v.nombre}</span></td>
                <td className="px-3 py-2">{v.unidad}</td>
                <td className="num px-3 py-2 text-right">{v.validos}</td>
                <td className="px-3 py-2">
                  <span className="flex items-center gap-2"><span className="h-1.5 w-20 overflow-hidden rounded-full bg-surface-2"><i className="block h-full rounded-full bg-accent" style={{ width: `${v.disponibilidad}%` }} /></span><span className="num text-xs">{fmt(v.disponibilidad, 1)}%</span></span>
                </td>
                <td className="num px-3 py-2 text-right">{empty ? "—" : fmt(v.min, d(v.variable))}</td>
                <td className="num px-3 py-2 text-right">{empty ? "—" : fmt(v.mediana, d(v.variable))}</td>
                <td className="num px-3 py-2 text-right">{empty ? "—" : fmt(v.max, d(v.variable))}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function AvailabilityMatrix({ faltantes, dias }: { faltantes: Record<string, number[]>; dias: number }) {
  const order = ["O3", "CO", "PM10", "PM2.5", "ET", "WS", "WD"];
  const steps = ["--seq-0", "--seq-1", "--seq-2", "--seq-3", "--seq-4"];
  const bucket = (n: number) => (n === 0 ? 0 : n < 12 ? 1 : n < 18 ? 2 : n < 24 ? 3 : 4);
  return (
    <div className="card p-4">
      <div className="scroll-thin overflow-x-auto">
        <div className="grid min-w-[680px] gap-[3px] text-[0.68rem]" style={{ gridTemplateColumns: `64px repeat(${dias}, minmax(14px, 1fr))` }}>
          <div />
          {Array.from({ length: dias }, (_, i) => <div key={i} className="num pb-1 text-center text-muted">{i + 1}</div>)}
          {order.map((v) => (
            <Row key={v} v={v} vals={faltantes[v] ?? []} steps={steps} bucket={bucket} />
          ))}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted">
        {["0 h", "1–11 h", "12–17 h", "18–23 h", "24 h"].map((l, i) => (
          <span key={l} className="inline-flex items-center gap-1.5"><i className="inline-block h-2.5 w-5 rounded-sm" style={{ background: `var(${steps[i]})` }} />{l}</span>
        ))}
        <span>· 18 h = mínimo para el indicador diario</span>
      </div>
    </div>
  );
}

function Row({ v, vals, steps, bucket }: { v: string; vals: number[]; steps: string[]; bucket: (n: number) => number }) {
  return (
    <>
      <div className="num self-center text-ink-2">{PL[v] ?? v}</div>
      {vals.map((f, i) => {
        const n = 24 - f;
        return <div key={i} title={`${PL[v] ?? v} · día ${i + 1}: ${n} de 24 h`} className="h-6 rounded-[4px]" style={{ background: `var(${steps[bucket(n)]})` }} />;
      })}
    </>
  );
}
