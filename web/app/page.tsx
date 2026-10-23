import Link from "next/link";
import { MapaJalisco } from "@/components/MapaJalisco";
import { Observatorio } from "@/components/observatorio/Observatorio";
import { getDescargas, getIndice, getMapa, getPeriodo } from "@/lib/data";
import { construirResumen } from "@/lib/resumen";
import { ACADEMIA, ESTACION, SPRINTS } from "@/lib/site";

export default function Inicio() {
  // Todos los periodos del índice; el tablero abre en el último y permite cambiar entre ellos.
  const periodos = getIndice().map(({ periodo }) => {
    const s = SPRINTS.find((x) => x.periodo === periodo && x.estado !== "próximo");
    return construirResumen(getPeriodo(periodo), s ? { slug: s.slug, numero: s.numero } : null, getDescargas(periodo));
  });

  const mapa = getMapa();
  return (
    <>
      <section className="mx-auto max-w-7xl px-4 pt-8 sm:px-6 lg:px-8" aria-labelledby="comparacion-anual">
        <div className="card flex flex-wrap items-center justify-between gap-5 border-accent/30 p-6 sm:p-8">
          <div><p className="eyebrow">Sprint 2 · análisis retrospectivo</p><h1 id="comparacion-anual" className="display mt-2 text-3xl font-medium">¿Qué cambió en Miravalle entre 2023 y 2024?</h1><p className="mt-2 max-w-2xl text-sm text-ink-2">Concentraciones, categorías y meteorología con una referencia común de 2024. Explora los periodos evaluados y la cobertura que sustenta cada comparación.</p></div>
          <Link href="/sprint-2" className="rounded-full bg-ink px-5 py-3 text-sm font-medium text-bg">Explorar 2024 vs. 2023 →</Link>
        </div>
      </section>
      <Observatorio periodos={periodos} />

      <div className="mx-auto max-w-7xl space-y-10 px-4 pb-16 sm:px-6 lg:px-8">
        {/* Boletines */}
        <section aria-labelledby="boletines-t" className="space-y-6 border-t border-rule pt-14">
          <div className="space-y-2">
            <p className="eyebrow">Boletines del observatorio</p>
            <h2 id="boletines-t" className="display text-[1.9rem] font-medium text-ink sm:text-[2.3rem]">Análisis por periodo y alcance</h2>
            <p className="max-w-2xl leading-relaxed text-ink-2">
              {ACADEMIA.nombre} reúne el análisis mensual de marzo de 2024 y la comparación retrospectiva de 2023–2024. Cada vista explica sus indicadores y límites de cobertura.
            </p>
          </div>
          <ol className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {SPRINTS.map((s) => {
              const activo = s.estado !== "próximo";
              const body = (
                <>
                  <div className="flex items-center justify-between">
                    <span className="num text-xs text-muted">Núm. {s.numero} · Sprint {s.numero}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${activo ? "bg-accent/15 text-accent" : "bg-surface-2 text-muted"}`}>{s.etiquetaPublica ?? s.estado}</span>
                  </div>
                  <p className="display mt-4 text-2xl font-medium leading-tight text-ink">{s.titulo}</p>
                  <p className="mt-2 text-sm leading-relaxed text-ink-2">{s.resumen}</p>
                  {activo && <p className="mt-5 text-sm font-medium text-accent">Abrir boletín →</p>}
                </>
              );
              return (
                <li key={s.slug}>
                  {activo ? <Link href={`/${s.slug}`} className="card block h-full p-6 transition hover:-translate-y-0.5 hover:border-ink-2">{body}</Link>
                    : <div className="h-full rounded-2xl border border-dashed border-rule p-6">{body}</div>}
                </li>
              );
            })}
          </ol>
        </section>

        {/* Estación */}
        <section aria-labelledby="estacion-t" className="space-y-5">
          <div className="space-y-2">
            <p className="eyebrow">Estación de monitoreo · Jalisco</p>
            <h2 id="estacion-t" className="display text-[1.9rem] font-medium text-ink sm:text-[2.3rem]">{ESTACION.nombre} en la red de SEMADET</h2>
          </div>
          <div className="card grid gap-6 p-6 md:grid-cols-4">
            {[["Estación", `${ESTACION.nombre} (${ESTACION.clave})`], ["Ubicación", `${ESTACION.coords} · ${ESTACION.altitud}`], ["Red", ESTACION.red], ["Mide", "O₃ · CO · PM₁₀ · PM₂.₅ · temperatura · viento"]].map(([k, v]) => (
              <div key={k}><p className="eyebrow">{k}</p><p className="mt-1.5 text-sm text-ink">{v}</p></div>
            ))}
          </div>
          {mapa && (
            <figure className="space-y-2">
              <div className="card p-4 sm:p-5"><MapaJalisco mapa={mapa} clave={ESTACION.clave} /></div>
              <figcaption className="text-xs leading-relaxed text-muted">Jalisco, el Área Metropolitana de Guadalajara y las {mapa.zona.estaciones.length} estaciones de SEMADET. {mapa.fuente}</figcaption>
            </figure>
          )}
        </section>
      </div>
    </>
  );
}

export const dynamic = "force-static";
