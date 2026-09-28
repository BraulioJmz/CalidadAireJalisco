import { CatPill } from "@/components/ui";
import { dow, fmt, MES, parseT } from "@/lib/aire";
import type { Maximo } from "@/lib/types";

/** Cómo se presenta cada extremo del periodo: etiqueta, unidad, decimales y si es indicador NOM. */
const MAX_INFO: Record<string, { label: string; unidad: string; d: number; indicador?: boolean }> = {
  "PM10:max": { label: "PM₁₀ horario (concentración)", unidad: "µg/m³", d: 0 },
  "PM10_NowCast:max": { label: "PM₁₀ NowCast (indicador)", unidad: "µg/m³", d: 0, indicador: true },
  "PM2.5:max": { label: "PM₂.₅ horario (concentración)", unidad: "µg/m³", d: 0 },
  "PM2.5_NowCast:max": { label: "PM₂.₅ NowCast (indicador)", unidad: "µg/m³", d: 0, indicador: true },
  "O3:max": { label: "O₃ horario (indicador)", unidad: "ppm", d: 3, indicador: true },
  "CO_8h:max": { label: "CO promedio 8 h (indicador)", unidad: "ppm", d: 2, indicador: true },
  "ET:max": { label: "Temperatura máxima", unidad: "°C", d: 0 },
  "ET:min": { label: "Temperatura mínima", unidad: "°C", d: 0 },
  "WS:max": { label: "Viento más fuerte", unidad: "m/s", d: 1 },
};

export const fechaHora = (t: string) => {
  const p = parseT(t);
  return `${dow(t)} ${p.d} ${MES[p.m - 1]} ${String(p.h).padStart(2, "0")}:00`;
};

/** Tabla "¿cuándo hubo máximos?": valor, fecha y hora, categoría del indicador y categoría global de esa hora. */
export function Maximos({ maximos }: { maximos: Maximo[] }) {
  return (
    <div className="card scroll-thin overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <caption className="sr-only">Máximos y mínimos del periodo</caption>
        <thead className="bg-surface-2 text-left">
          <tr className="num text-[0.68rem] uppercase tracking-[0.1em] text-muted">
            <th className="px-4 py-2.5 font-medium">Variable</th>
            <th className="px-4 py-2.5 text-right font-medium">Valor</th>
            <th className="px-4 py-2.5 font-medium">Cuándo</th>
            <th className="px-4 py-2.5 font-medium">Categoría del indicador</th>
            <th className="px-4 py-2.5 font-medium">Categoría global de esa hora</th>
          </tr>
        </thead>
        <tbody>
          {maximos.map((m) => {
            const info = MAX_INFO[`${m.variable}:${m.tipo}`] ?? { label: m.variable, unidad: "", d: 2 };
            return (
              <tr key={`${m.variable}${m.tipo}`} className="border-t border-rule align-top">
                <td className="px-4 py-2.5 text-ink">{info.label}</td>
                <td className="num px-4 py-2.5 text-right text-ink">{fmt(m.valor, info.d)} <span className="text-muted">{info.unidad}</span></td>
                <td className="num px-4 py-2.5 text-ink-2">
                  {fechaHora(m.fecha_hora)}
                  {m.otras_horas.length > 0 && <span className="block text-xs text-muted">también: {m.otras_horas.map(fechaHora).join(", ")}</span>}
                </td>
                <td className="px-4 py-2.5">{info.indicador && m.categoria ? <CatPill c={m.categoria} /> : <span className="text-xs text-muted">no aplica</span>}</td>
                <td className="px-4 py-2.5"><CatPill c={m.cat_global} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export type DescargaDoc = { nombre: string; href: string; titulo: string; descripcion: string };

/** Descargas documentadas: qué contiene cada archivo, en el orden del flujo. */
export function Descargas({ items }: { items: DescargaDoc[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {items.map((d) => (
        <li key={d.href}>
          <a href={d.href} download className="card flex h-full flex-col gap-1.5 p-4 transition hover:border-ink-2">
            <span className="flex items-baseline justify-between gap-3">
              <span className="font-semibold text-ink">↓ {d.titulo}</span>
              <span className="num shrink-0 text-[0.68rem] text-muted">{d.nombre.split(".").pop()?.toUpperCase()}</span>
            </span>
            <span className="num truncate text-xs text-accent">{d.nombre}</span>
            {d.descripcion && <span className="text-sm leading-relaxed text-ink-2">{d.descripcion}</span>}
          </a>
        </li>
      ))}
    </ul>
  );
}

/** Pasos del pipeline y comandos para reproducir el análisis desde la raíz del repositorio. */
export function Reproducir({ periodo }: { periodo: string }) {
  const pasos = [
    ["etl.py", "Lee BD_2024.xlsx sin modificarla, filtra MIR, corrige tipos, revisa duplicados, huecos y atípicos (IQR) y guarda el año limpio y el recorte del periodo.", `python pipeline/etl.py --periodo ${periodo}`],
    ["calculos.py", "Control de calidad con bitácora y cálculo NOM-172: NowCast, CO 8 h, suficiencia, indicadores, categorías y responsable. Genera Archivo 1 y Archivo 2.", `python pipeline/calculos.py --periodo ${periodo}`],
    ["procesar.py", "Corre los dos pasos anteriores y, a partir de Archivo 1 y Archivo 2, arma los Excel y el JSON que publica este sitio.", `python pipeline/procesar.py --periodo ${periodo}`],
    ["tests/", "Verifica el NowCast con los 24 casos de la profesora, las bandas y que marzo 2024 no cambie (regresión).", "python -m pytest tests"],
  ];
  return (
    <ol className="grid gap-px overflow-hidden rounded-2xl border border-rule bg-[var(--rule)] md:grid-cols-2">
      {pasos.map(([archivo, que, cmd], i) => (
        <li key={archivo} className="space-y-2 bg-surface p-5">
          <p className="flex items-baseline gap-2"><span className="num text-xs text-accent">{String(i + 1).padStart(2, "0")}</span><span className="num font-semibold text-ink">{archivo}</span></p>
          <p className="text-sm leading-relaxed text-ink-2">{que}</p>
          <code className="num block overflow-x-auto whitespace-nowrap rounded-lg bg-surface-2 px-3 py-2 text-xs text-ink">{cmd}</code>
        </li>
      ))}
    </ol>
  );
}
