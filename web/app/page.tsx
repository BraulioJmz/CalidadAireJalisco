import Link from "next/link";
import { CalendarMonth } from "@/components/CalendarMonth";
import { HourOfDayChart } from "@/components/charts/DistributionCharts";
import { Seal } from "@/components/Seal";
import { CatPill, Kpi, Legend, Pol } from "@/components/ui";
import { CATS, catVar, pct } from "@/lib/aire";
import { getIndice, getPeriodo } from "@/lib/data";
import { ACADEMIA, ESTACION, SPRINTS } from "@/lib/site";

export default function Observatorio() {
  const indice = getIndice();
  const ultimo = indice[indice.length - 1];
  const D = getPeriodo(ultimo.periodo);
  const N = D.numeralia;
  const C = D.categorias_por_hora;
  const horas = D.diario.map((_, i) => D.horario.slice(i * 24, i * 24 + 24).map((h) => h.Cat_global));
  const tot = (h: number) => CATS.reduce((s, c) => s + (C[c]?.[h] ?? 0), 0);
  const malas = (h: number) => (C.Mala?.[h] ?? 0) + (C["Muy Mala"]?.[h] ?? 0) + (C["Extremadamente Mala"]?.[h] ?? 0);
  // franja crítica = horas donde la mitad o más de los días estuvieron en Mala o peor
  const criticas = Array.from({ length: 24 }, (_, h) => h).filter((h) => tot(h) && malas(h) / tot(h) >= 0.5);
  const buenas = Array.from({ length: 24 }, (_, h) => h).filter((h) => tot(h) && (C.Buena?.[h] ?? 0) / tot(h) >= 0.8);
  // tramo continuo más largo dentro de una lista de horas
  const tramo = (hs: number[]) => {
    let best: number[] = [], cur: number[] = [];
    hs.forEach((h, i) => { cur = i && h === hs[i - 1] + 1 ? [...cur, h] : [h]; if (cur.length > best.length) best = cur; });
    return best;
  };
  const rango = (hs: number[]) => { const t = tramo(hs); return t.length ? `${String(t[0]).padStart(2, "0")}:00–${String(t[t.length - 1]).padStart(2, "0")}:59` : "—"; };
  const horasMuyMala = Array.from({ length: 24 }, (_, h) => h).filter((h) => (C["Muy Mala"]?.[h] ?? 0) > 0);
  const pred = ultimo.categoria_predominante;
  const dom = Object.entries(N.dias_por_responsable).sort((a, b) => b[1] - a[1])[0];
  const peorDia = N.dias_mas_desfavorables[0];
  const dt = N.dias_con_categoria;

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-rule">
        <div className="grid-paper pointer-events-none absolute inset-0 opacity-70" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 sm:py-20 lg:grid-cols-[1.25fr_1fr] lg:items-end lg:px-8">
          <div>
            <div className="flex items-center gap-3"><Seal size={44} /><p className="eyebrow">{ACADEMIA.unidad}</p></div>
            <h1 className="display mt-6 text-[2.7rem] font-medium leading-[1.02] text-ink sm:text-6xl lg:text-[4.6rem]">
              ¿Cómo está el aire que respira nuestra comunidad?
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-2">{ACADEMIA.descripcion}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/sprint-1" className="rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-bg transition hover:opacity-90">Leer el boletín de {ultimo.nombre}</Link>
              <Link href="/metodologia" className="rounded-full border border-rule bg-surface px-5 py-2.5 text-sm font-medium text-ink transition hover:border-ink-2">Cómo lo calculamos</Link>
            </div>
          </div>

          <div className="card relative overflow-hidden p-6 shadow-[0_24px_60px_-30px_rgba(15,27,45,0.35)]">
            <div className="absolute inset-x-0 top-0 h-1" style={{ background: catVar(pred) }} />
            <div className="flex items-center justify-between gap-3">
              <p className="eyebrow">Último periodo analizado</p>
              <span className="num text-xs text-muted">{ESTACION.clave} · {ESTACION.nombre}</span>
            </div>
            <p className="display mt-3 text-3xl font-medium capitalize text-ink">{ultimo.nombre}</p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <span className="text-sm text-ink-2">Categoría predominante</span><CatPill c={pred} size="md" />
            </div>
            <div className="mt-6">
              <div className="flex h-3 overflow-hidden rounded-full bg-surface-2">
                {CATS.map((c) => N.dias_por_categoria[c] ? <span key={c} title={`${c}: ${N.dias_por_categoria[c]} días`} style={{ width: `${(100 * N.dias_por_categoria[c]) / dt}%`, background: catVar(c) }} className="border-r-2 border-[var(--surface)] last:border-r-0" /> : null)}
              </div>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
                {CATS.filter((c) => N.dias_por_categoria[c]).map((c) => <span key={c}><b className="num text-ink">{N.dias_por_categoria[c]}</b> {c}</span>)}
                {N.dias_sin_datos.length > 0 && <span><b className="num text-ink">{N.dias_sin_datos.length}</b> sin datos</span>}
              </div>
            </div>
            <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-rule pt-5 text-sm">
              <div><dt className="text-muted">Franja crítica</dt><dd className="num mt-0.5 font-semibold text-ink">{rango(criticas)}</dd></div>
              <div><dt className="text-muted">Mejor franja</dt><dd className="num mt-0.5 font-semibold text-ink">{rango(buenas)}</dd></div>
            </dl>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-20 px-4 py-16 sm:px-6 lg:px-8">
        {/* KPIs */}
        <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi value={pct(N.horas_por_categoria.Buena, N.horas_con_categoria)} unit="%" label={`de las horas tuvo aire Bueno, aunque solo ${N.dias_por_categoria.Buena} de ${dt} días lo fue`} />
          <Kpi value={dom[1]} unit={`de ${dt} días`} label={<>el contaminante que define la categoría es <b className="text-ink"><Pol p={dom[0]} /></b></>} />
          <Kpi value={N.horas_por_categoria["Muy Mala"]} unit="horas" label={`en Muy Mala, todas entre ${rango(horasMuyMala)}`} tone="alert" />
          <Kpi value={peorDia ? +peorDia.fecha.slice(8) : "—"} unit="de marzo" label={<>día más desfavorable: <b className="text-ink">{peorDia?.categoria}</b> con <Pol p={peorDia?.responsable ?? ""} /> en {peorDia?.indicador} {peorDia?.unidad}</>} />
        </section>

        {/* Hora del día */}
        <section className="grid gap-8 lg:grid-cols-[1fr_1.6fr] lg:items-center">
          <div className="space-y-4">
            <p className="eyebrow">Para planear el día</p>
            <h2 className="display text-3xl font-medium leading-tight text-ink sm:text-4xl">La mañana concentra el aire malo; la tarde suele ser buena</h2>
            <p className="leading-relaxed text-ink-2">
              Entre {rango(criticas)} al menos la mitad de los días de {ultimo.nombre} estuvieron en Mala o peor, sobre todo por <Pol p="PM10" />.
              De {rango(buenas)} el aire fue Bueno en 8 de cada 10 días. Por la tarde el ozono puede subir a Aceptable, así que las actividades físicas intensas se planean con el aviso por hora.
            </p>
          </div>
          <div className="card p-5"><HourOfDayChart porHora={C} height={320} /></div>
        </section>

        {/* Calendario */}
        <section className="space-y-5">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div className="space-y-2">
              <p className="eyebrow">Calendario · {ultimo.nombre}</p>
              <h2 className="display text-3xl font-medium text-ink sm:text-4xl">Cada día, su categoría y sus 24 horas</h2>
            </div>
            <Legend />
          </div>
          <CalendarMonth diario={D.diario} horas={horas} unidades={D.unidades} hrefBase="/sprint-1" compact />
          <p className="text-xs text-muted">Toca un día para abrir su simulación hora por hora en el boletín.</p>
        </section>

        {/* Boletines */}
        <section className="space-y-6">
          <div className="space-y-2">
            <p className="eyebrow">Boletines del observatorio</p>
            <h2 className="display text-3xl font-medium text-ink sm:text-4xl">Una entrega por sprint, un dashboard al final</h2>
            <p className="max-w-2xl leading-relaxed text-ink-2">Cada boletín amplía el periodo analizado con el mismo pipeline. Esta página reúne siempre el periodo más reciente.</p>
          </div>
          <ol className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {SPRINTS.map((s) => {
              const activo = s.estado !== "próximo";
              const body = (
                <>
                  <div className="flex items-center justify-between">
                    <span className="num text-xs text-muted">Núm. {s.numero} · Sprint {s.numero}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${activo ? "bg-accent/15 text-accent" : "bg-surface-2 text-muted"}`}>{s.estado}</span>
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
        <section className="card grid gap-6 p-6 md:grid-cols-4">
          {[["Estación", `${ESTACION.nombre} (${ESTACION.clave})`], ["Ubicación", `${ESTACION.coords} · ${ESTACION.altitud}`], ["Red", ESTACION.red], ["Mide", "O₃ · CO · PM₁₀ · PM₂.₅ · temperatura · viento"]].map(([k, v]) => (
            <div key={k}><p className="eyebrow">{k}</p><p className="mt-1.5 text-sm text-ink">{v}</p></div>
          ))}
        </section>
      </div>
    </>
  );
}

export const dynamic = "force-static";
