import type { Metadata } from "next";
import { CatPill } from "@/components/ui";
import { CATS, fmt } from "@/lib/aire";
import { getIndice, getPeriodo } from "@/lib/data";

export const metadata: Metadata = { title: "Metodología", description: "Cómo se calcula el Índice AIRE Y SALUD en el observatorio (NOM-172-SEMARNAT-2023)." };

const PASOS = [
  ["Extracción (etl.py)", "Se toma la estación MIR de BD_2024.xlsx (SEMADET) sin modificar el original: se corrigen tipos, se revisan duplicados y huecos, y se guarda el año limpio y el recorte de cada periodo con sus 24 h de calentamiento."],
  ["Perfil y control de calidad", "Tipos, unidades, faltantes, duplicados, formato y atípicos. Los valores sospechosos se marcan y clasifican; solo se anula lo físicamente imposible."],
  ["Indicadores horarios (calculos.py)", "NowCast 12 h para PM₁₀ y PM₂.₅ (función de referencia sin cambios), promedio móvil 8 h para CO, valor horario para O₃."],
  ["Categorías", "Cada indicador se clasifica con las bandas de la NOM; la categoría global es la más desfavorable y se registra el contaminante responsable."],
  ["Indicadores diarios (calculos.py)", "Suficiencia de 18 de 24 horas por contaminante; promedio 24 h (PM), máximo horario (O₃) y máximo del promedio 8 h (CO). Se guardan en Archivo1 (horario) y Archivo2 (diario)."],
  ["Publicación (procesar.py)", "A partir de Archivo1 y Archivo2 se generan los Excel horario y diario, la bitácora y el JSON que usa este sitio."],
];

export default function Metodologia() {
  const idx = getIndice();
  const D = getPeriodo(idx[idx.length - 1].periodo);
  const u = D.unidades;
  return (
    <div className="mx-auto max-w-5xl space-y-16 px-4 py-16 sm:px-6 lg:px-8">
      <header className="space-y-4">
        <p className="eyebrow">Metodología</p>
        <h1 className="display text-5xl font-medium leading-[1.05] text-ink sm:text-6xl">Cómo lo calculamos</h1>
        <p className="max-w-2xl text-lg leading-relaxed text-ink-2">Todos los boletines salen del mismo pipeline en Python, que aplica la NOM-172-SEMARNAT-2023. Cada sprint procesa un periodo nuevo con una sola instrucción.</p>
        <pre className="card num overflow-x-auto p-4 text-sm text-ink">python pipeline/procesar.py --periodo 2024-03</pre>
      </header>

      <section className="space-y-5">
        <h2 className="display text-3xl font-medium text-ink">Del archivo a la categoría</h2>
        <ol className="grid gap-3 sm:grid-cols-2">
          {PASOS.map(([t, d], i) => (
            <li key={t} className="card flex gap-4 p-5">
              <span className="num grid size-8 shrink-0 place-items-center rounded-full bg-surface-2 text-sm text-ink">{i + 1}</span>
              <div><p className="font-semibold text-ink">{t}</p><p className="mt-1 text-sm leading-relaxed text-ink-2">{d}</p></div>
            </li>
          ))}
        </ol>
      </section>

      <section className="space-y-5">
        <h2 className="display text-3xl font-medium text-ink">Límites de cada categoría</h2>
        <p className="text-ink-2">Límite superior de cada categoría por contaminante (partículas: límites vigentes desde enero de 2024).</p>
        <div className="card scroll-thin overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-left"><tr className="num text-[0.68rem] uppercase tracking-[0.1em] text-muted">
              <th className="px-4 py-3 font-medium">Categoría</th><th className="px-4 py-3 font-medium">Riesgo</th>
              {["O3", "CO", "PM10", "PM2.5"].map((p) => <th key={p} className="px-4 py-3 text-right font-medium">{p} · <span className="normal-case">{u[p]}</span><br /><span className="normal-case tracking-normal">{D.indicador_horario[p]}</span></th>)}
            </tr></thead>
            <tbody>
              {CATS.map((c, i) => (
                <tr key={c} className="border-t border-rule">
                  <td className="px-4 py-2.5"><CatPill c={c} /></td><td className="px-4 py-2.5 text-ink-2">{D.riesgo[c]}</td>
                  {["O3", "CO", "PM10", "PM2.5"].map((p) => { const b = D.bandas[p]; return (
                    <td key={p} className="num px-4 py-2.5 text-right text-ink">{i < 4 ? `≤ ${fmt(b[i], p === "O3" ? 3 : 0)}` : `> ${fmt(b[3], p === "O3" ? 3 : 0)}`}</td>); })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="display text-3xl font-medium text-ink">Criterios aplicados</h2>
        <div className="card divide-y divide-[var(--rule)]">
          {D.metodologia.map((m) => (
            <div key={m.Elemento} className="grid gap-1 p-4 sm:grid-cols-[200px_1fr] sm:gap-6">
              <p className="font-semibold text-ink">{m.Elemento}</p><p className="text-sm leading-relaxed text-ink-2">{m.Criterio}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="display text-3xl font-medium text-ink">Cómo crece el proyecto</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <pre className="card num overflow-x-auto p-5 text-xs leading-relaxed text-ink-2">{`calidad-aire-miravalle/
├─ BD_2024.xlsx   base original (solo lectura)
├─ pipeline/      etl → calculos → procesar (--periodo AAAA-MM)
├─ tests/         NowCast, reglas y regresión de marzo
├─ data/processed/
│  ├─ miravalle_2024_clean.csv   año limpio
│  └─ AAAA-MM/    limpio, Archivo1, Archivo2, Excel
└─ web/           este sitio (Next.js)
   ├─ app/page.tsx          observatorio (dashboard final)
   ├─ app/sprint-1/         boletín 1 (congelado)
   ├─ app/sprint-2/         boletín 2 …
   └─ data/periodos/*.json  salida del pipeline`}</pre>
          <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-ink-2 marker:font-mono marker:text-muted">
            <li>Crear la rama del sprint: <span className="num text-ink">git switch -c sprint-2</span>.</li>
            <li>Procesar el nuevo periodo: <span className="num text-ink">python pipeline/procesar.py --periodo 2024-04</span>.</li>
            <li>Agregar la ruta <span className="num text-ink">app/sprint-2</span> y su fila en <span className="num text-ink">lib/site.ts</span>; reutilizar los componentes.</li>
            <li>Abrir un pull request; Vercel crea un enlace de vista previa para revisarlo en equipo.</li>
            <li>Al entregar: fusionar a <span className="num text-ink">main</span> y marcar <span className="num text-ink">git tag sprint-2</span>.</li>
          </ol>
        </div>
      </section>
    </div>
  );
}
