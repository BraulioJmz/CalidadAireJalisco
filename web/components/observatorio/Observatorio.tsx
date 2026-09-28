"use client";
import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { CalendarMonth } from "@/components/CalendarMonth";
import { Descargas, Maximos } from "@/components/Evidencia";
import { HourOfDayChart, ResponsibleChart } from "@/components/charts/DistributionCharts";
import { MensajesNOM } from "@/components/MensajesNOM";
import { CatPill, Kpi, Legend, Pol } from "@/components/ui";
import { CATS, catBg, catVar, fmt, MES_LARGO, onVar, pct } from "@/lib/aire";
import {
  CATS_ALL, catsDelDia, fmtTramo, fmtTramos, franjasDelDia, hh, modaEn, responsableEn, tramos,
  type Franja, type ResumenPeriodo,
} from "@/lib/resumen";
import { ACADEMIA, ESTACION } from "@/lib/site";
import { DiurnalChart, TrendChart } from "./charts";
import { DayHourMatrix } from "./DayHourMatrix";

const SECCIONES = [
  ["resumen", "Resumen"], ["planear", "Planear el día"], ["dia-por-dia", "Día por día"],
  ["contaminantes", "Contaminantes"], ["maximos", "Máximos"], ["evolucion", "Evolución"], ["datos", "Datos y limitaciones"],
] as const;

const FRANJA: Record<Franja, { titulo: string; criterio: string }> = {
  buena: { titulo: "Recomendada", criterio: "80 % o más de los días en Buena" },
  precaucion: { titulo: "Con precaución", criterio: "sin mayoría clara de horas Buenas ni Malas" },
  critica: { titulo: "Evitar actividad intensa", criterio: "50 % o más de los días en Mala o peor" },
};

const DIURNO: { serie: string; nombre: string; pol?: string; variable?: string }[] = [
  { serie: "PM10_NowCast", nombre: "PM₁₀ · NowCast", pol: "PM10" },
  { serie: "PM2.5_NowCast", nombre: "PM₂.₅ · NowCast", pol: "PM2.5" },
  { serie: "O3", nombre: "O₃ · horario", pol: "O3" },
];

function Seccion({ id, eyebrow, titulo, children, aside }: { id: string; eyebrow: string; titulo: ReactNode; children: ReactNode; aside?: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-t`} className="scroll-mt-28 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-3xl space-y-2">
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={`${id}-t`} className="display text-[1.9rem] font-medium leading-[1.1] text-ink sm:text-[2.3rem]">{titulo}</h2>
        </div>
        {aside}
      </div>
      {children}
    </section>
  );
}

function Meter({ label, value, sub }: { label: ReactNode; value: number; sub?: string }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3 text-sm">
        <span className="truncate text-ink">{label}</span>
        <span className="num shrink-0 text-ink-2">{fmt(value, value % 1 ? 1 : 0)} %{sub && <span className="text-muted"> · {sub}</span>}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

export function Observatorio({ periodos }: { periodos: ResumenPeriodo[] }) {
  const [clave, setClave] = useState(periodos[periodos.length - 1].clave);
  const [vista, setVista] = useState<"matriz" | "calendario">("matriz");

  // ?periodo=AAAA-MM permite compartir un periodo concreto; sin él se muestra el más reciente
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get("periodo");
    if (p && periodos.some((x) => x.clave === p)) setClave(p);
  }, [periodos]);
  const cambiar = (c: string) => {
    setClave(c);
    const u = new URL(window.location.href);
    u.searchParams.set("periodo", c);
    window.history.replaceState(null, "", u);
  };

  const R = periodos.find((p) => p.clave === clave) ?? periodos[periodos.length - 1];
  const N = R.numeralia;
  const C = R.categorias_por_hora;
  const dt = N.dias_con_categoria;
  const mes = MES_LARGO[R.mes - 1];
  const href = R.sprint ? `/${R.sprint.slug}` : undefined;

  const v = useMemo(() => {
    // empate → la más desfavorable
    const pred = [...CATS].reverse().reduce<string>((a, c) => ((N.dias_por_categoria[c] ?? 0) > (N.dias_por_categoria[a] ?? 0) ? c : a), "Extremadamente Mala");
    const dom = Object.entries(N.dias_por_responsable).sort((a, b) => b[1] - a[1])[0] ?? ["", 0];
    const F = franjasDelDia(C);
    const horasMM = Array.from({ length: 24 }, (_, h) => h).filter((h) => (C["Muy Mala"]?.[h] ?? 0) + (C["Extremadamente Mala"]?.[h] ?? 0) > 0);
    const hMM = N.horas_por_categoria["Muy Mala"] + N.horas_por_categoria["Extremadamente Mala"];
    // tramos del día en orden, con su franja y la categoría más frecuente
    const linea = (["buena", "precaucion", "critica"] as Franja[])
      .flatMap((f) => tramos(F[f]).map((t) => ({ f, t, moda: modaEn(C, Array.from({ length: t[1] - t[0] + 1 }, (_, i) => t[0] + i)) })))
      .sort((a, b) => a.t[0] - b.t[0]);
    const tarjetas = (["buena", "precaucion", "critica"] as Franja[]).map((f) => ({
      f, horas: F[f], moda: modaEn(C, F[f]), resp: responsableEn(R.responsable_por_hora, F[f]),
    }));
    const pBuenaEnBuena = F.buena.length ? pct(F.buena.reduce((s, h) => s + F.horas[h].buena, 0), F.buena.reduce((s, h) => s + F.horas[h].tot, 0)) : 0;
    const perdidos = [...R.dias].filter((d) => d.horas_peores > 0).sort((a, b) => b.horas_peores - a.horas_peores).slice(0, 3);
    const extremo = (s: string, fn: "max" | "min") => {
      const xs = R.perfil_diurno[s]; if (!xs) return null;
      const vals = xs.filter((x): x is number => x !== null); if (!vals.length) return null;
      return xs.indexOf(fn === "max" ? Math.max(...vals) : Math.min(...vals));
    };
    return { pred, dom, F, horasMM, hMM, linea, tarjetas, pBuenaEnBuena, perdidos, extremo };
  }, [N, C, R]);

  const unidadDe = (s: (typeof DIURNO)[number]) => (s.pol ? R.unidades[s.pol] : R.disponibilidad.find((x) => x.variable === s.variable)?.unidad ?? "");
  const peorDia = N.dias_mas_desfavorables[0];
  const ex = { pm: v.extremo("PM10_NowCast", "max"), o3: v.extremo("O3", "max"), tmin: v.extremo("ET", "min"), tmax: v.extremo("ET", "max") };

  return (
    <>
      {/* Encabezado del tablero */}
      <section id="resumen" className="relative scroll-mt-28 border-b border-rule">
        <div className="grid-paper pointer-events-none absolute inset-0 opacity-60" />
        <div className="relative mx-auto max-w-7xl px-4 pb-10 pt-10 sm:px-6 sm:pt-14 lg:px-8">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-3xl">
              <p className="eyebrow">Observatorio · Estación {ESTACION.nombre} ({ESTACION.clave}) · NOM-172-SEMARNAT-2023</p>
              <h1 className="display mt-3 text-[2.4rem] font-medium leading-[1.04] text-ink sm:text-5xl lg:text-[3.6rem]">
                ¿Cómo está el aire que respira nuestra comunidad?
              </h1>
              <p className="mt-4 max-w-2xl leading-relaxed text-ink-2">{ACADEMIA.descripcion}</p>
            </div>
            <div className="flex flex-col gap-1.5">
              {periodos.length > 1 ? <label htmlFor="periodo" className="eyebrow">Periodo analizado</label> : <p className="eyebrow">Periodo analizado</p>}
              {periodos.length > 1 ? (
                <select id="periodo" value={R.clave} onChange={(e) => cambiar(e.target.value)}
                  className="num rounded-full border border-rule bg-surface px-4 py-2 text-sm capitalize text-ink hover:border-ink-2">
                  {periodos.map((p) => <option key={p.clave} value={p.clave}>{p.nombre}</option>)}
                </select>
              ) : (
                <span className="display rounded-full border border-rule bg-surface px-4 py-1.5 text-lg capitalize text-ink">{R.nombre}</span>
              )}
            </div>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-[1.05fr_1.4fr]">
            {/* Estado del periodo */}
            <div className="card relative overflow-hidden p-6">
              <div className="absolute inset-x-0 top-0 h-1" style={{ background: catVar(v.pred) }} />
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="eyebrow">Categoría predominante · días</p>
                <span className="text-xs text-muted">Riesgo <b className="text-ink">{R.riesgo[v.pred] ?? "—"}</b></span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <CatPill c={v.pred} size="lg" />
                <span className="text-sm text-ink-2"><b className="text-ink">{N.dias_por_categoria[v.pred]}</b> de {dt} días con categoría</span>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-ink-2">
                <b className="text-ink">Riesgo para la población en general:</b> {R.descripcion_riesgo[v.pred]?.general}
                {R.descripcion_riesgo[v.pred]?.sensible && <> <b className="text-ink">Para la población sensible:</b> {R.descripcion_riesgo[v.pred].sensible}</>}
                <span className="mt-1 block text-xs text-muted">NOM-172-SEMARNAT-2023, tabla 10.</span>
              </p>
              <div className="mt-5">
                <div className="flex h-3 gap-[2px] overflow-hidden rounded-full">
                  {CATS_ALL.map((c) => {
                    const n = c === "Sin datos" ? N.dias_sin_datos.length : N.dias_por_categoria[c] ?? 0;
                    return n ? <span key={c} title={`${c}: ${n} días`} style={{ width: `${(100 * n) / N.dias_mes}%`, ...catBg(c) }} /> : null;
                  })}
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
                  {CATS.filter((c) => N.dias_por_categoria[c]).map((c) => (
                    <span key={c} className="inline-flex items-center gap-1.5"><i className="size-2.5 rounded-[2px]" style={catBg(c)} /><b className="num text-ink">{N.dias_por_categoria[c]}</b> {c}</span>
                  ))}
                  {N.dias_sin_datos.length > 0 && <span className="inline-flex items-center gap-1.5"><i className="size-2.5 rounded-[2px]" style={catBg("Sin datos")} /><b className="num text-ink">{N.dias_sin_datos.length}</b> sin datos</span>}
                </div>
              </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 gap-3">
              <Kpi value={pct(N.horas_por_categoria.Buena, N.horas_con_categoria)} unit="% de las horas"
                label={`con calidad del aire Buena. Por día, solo ${N.dias_por_categoria.Buena} de ${dt} (${pct(N.dias_por_categoria.Buena, dt)} %) se clasificó como Buena: la categoría diaria refleja el peor contaminante del día.`} />
              <Kpi value={v.dom[1]} unit={`de ${dt} días`} label={<>el contaminante responsable de la categoría diaria fue <b className="text-ink"><Pol p={String(v.dom[0])} /></b></>} />
              <Kpi value={v.hMM} unit="horas" tone={v.hMM ? "alert" : undefined}
                label={v.hMM ? `en Muy Mala o peor, entre las ${hh(v.horasMM[0])}:00 y las ${hh(v.horasMM[v.horasMM.length - 1])}:59` : "sin horas en Muy Mala o peor"} />
              <Kpi value={peorDia ? +peorDia.fecha.slice(8) : "—"} unit={`de ${mes}`}
                label={peorDia ? <>día más desfavorable: <b className="text-ink">{peorDia.categoria}</b> por <Pol p={peorDia.responsable} /> ({fmt(peorDia.indicador)} {peorDia.unidad}, {peorDia.horas_mala_o_peor} h en Mala o peor)</> : "sin días con categoría"} />
            </div>
          </div>

          <nav aria-label="Secciones del tablero" className="scroll-thin mt-8 flex gap-1.5 overflow-x-auto">
            {SECCIONES.slice(1).map(([id, t]) => (
              <a key={id} href={`#${id}`} className="whitespace-nowrap rounded-full border border-rule bg-surface px-3 py-1.5 text-xs text-ink-2 transition hover:border-ink-2 hover:text-ink">{t}</a>
            ))}
          </nav>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-16 px-4 py-14 sm:px-6 lg:px-8">
        {/* Planear el día */}
        <Seccion id="planear" eyebrow={`Para planear actividades · ${R.nombre}`} titulo="¿A qué hora conviene salir?">
          <div className="card p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-semibold text-ink">Un día típico del periodo, por franja</p>
              <p className="text-xs text-muted">Color = categoría más frecuente de la franja</p>
            </div>
            <div className="mt-3 flex h-10 gap-[2px] overflow-hidden rounded-lg">
              {v.linea.map(({ f, t, moda }) => {
                const n = t[1] - t[0] + 1;
                return (
                  <div key={t[0]} title={`${fmtTramo(t)} · ${FRANJA[f].titulo} · más frecuente: ${moda}`}
                    className="flex min-w-0 items-center justify-center overflow-hidden px-1 text-[0.7rem] font-semibold"
                    style={{ width: `${(100 * n) / 24}%`, background: catVar(moda), color: onVar(moda) }}>
                    {n >= 4 && <span className="truncate">{FRANJA[f].titulo}</span>}
                  </div>
                );
              })}
            </div>
            <div className="num mt-1.5 flex justify-between text-[0.65rem] text-muted">{["00:00", "06:00", "12:00", "18:00", "23:59"].map((t) => <span key={t}>{t}</span>)}</div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {v.tarjetas.map(({ f, horas, moda, resp }) => (
              <div key={f} className={`card flex flex-col gap-3 p-5 ${horas.length ? "" : "opacity-60"}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-base font-semibold text-ink">{FRANJA[f].titulo}</p>
                  <span className="num text-xs text-muted">{horas.length} h</span>
                </div>
                <p className="num text-sm text-ink">{fmtTramos(horas)}</p>
                <p className="text-xs text-muted">Criterio: {FRANJA[f].criterio}.</p>
                {horas.length > 0 && (
                  <>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
                      Más frecuente <CatPill c={moda} />
                      {resp && <span>· responsable habitual <b className="text-ink"><Pol p={resp} /></b></span>}
                    </div>
                    <MensajesNOM m={R.mensajes[moda]} className="mt-auto border-t border-rule pt-3" />
                  </>
                )}
              </div>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
            <div className="card p-5">
              <p className="mb-2 text-sm font-semibold text-ink">Días en cada categoría según la hora del día</p>
              <HourOfDayChart porHora={C} height={280} />
            </div>
            <div className="card space-y-3 p-5 text-sm leading-relaxed text-ink-2">
              <p className="eyebrow">Cómo leerlo</p>
              {v.F.critica.length > 0 && (
                <p>De <b className="num text-ink">{fmtTramos(v.F.critica)}</b>, la mitad o más de los días estuvieron en Mala o peor.
                  {v.tarjetas[2].resp && <> El responsable más frecuente en esas horas fue <b className="text-ink"><Pol p={v.tarjetas[2].resp} /></b>.</>}</p>
              )}
              {v.F.buena.length > 0 && (
                <p>De <b className="num text-ink">{fmtTramos(v.F.buena)}</b>, la calidad del aire fue Buena en el <b className="text-ink">{v.pBuenaEnBuena} %</b> de los días.
                  {v.tarjetas[0].resp && <> Ahí el responsable habitual fue <b className="text-ink"><Pol p={v.tarjetas[0].resp} /></b>.</>}</p>
              )}
              <p>Las franjas describen lo que pasó en {R.nombre}; no son un pronóstico. La decisión de cada día se toma con el aviso por hora.</p>
            </div>
          </div>
        </Seccion>

        {/* Día por día */}
        <Seccion id="dia-por-dia" eyebrow={`Día por día · ${R.nombre}`} titulo="Cada día, su categoría diaria y sus 24 horas"
          aside={
            <div role="tablist" aria-label="Vista" className="flex rounded-full border border-rule bg-surface p-0.5 text-xs">
              {(["matriz", "calendario"] as const).map((k) => (
                <button key={k} role="tab" type="button" aria-selected={vista === k} onClick={() => setVista(k)}
                  className={`rounded-full px-3 py-1.5 transition ${vista === k ? "bg-ink text-bg" : "text-ink-2 hover:text-ink"}`}>
                  {k === "matriz" ? "Día × hora" : "Calendario"}
                </button>
              ))}
            </div>
          }>
          <Legend />
          {vista === "matriz" ? (
            <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
              <div className="card p-4 sm:p-5"><DayHourMatrix dias={R.dias} unidades={R.unidades} hrefBase={href} /></div>
              <aside className="card h-fit space-y-4 p-5 text-sm leading-relaxed text-ink-2">
                <p className="eyebrow">Lo que se pierde al resumir el día</p>
                <p className="display text-[1.6rem] font-medium leading-tight text-ink">
                  {N.horario_vs_diario.dias_con_horas_peores} de {dt} días tuvieron horas peores que su categoría diaria
                </p>
                <p>En total, <b className="text-ink">{N.horario_vs_diario.horas_peores_total} horas</b> quedaron por encima de la categoría del día. <span className="hidden sm:inline">La columna <span className="num">+peor</span> las cuenta.</span></p>
                {v.perdidos.length > 0 && (
                  <ul className="space-y-2.5 border-t border-rule pt-3">
                    <li className="eyebrow">Días con más horas peores</li>
                    {v.perdidos.map((d) => (
                      <li key={d.FECHA} className="grid grid-cols-[3.2rem_1fr_auto] items-center gap-2">
                        <b className="num text-ink">{+d.FECHA.slice(8)} {mes.slice(0, 3)}</b>
                        <span className="flex flex-wrap items-center gap-1"><CatPill c={d.Cat_global} /><span aria-label="pero su peor hora fue" className="text-muted">→</span><CatPill c={d.peor_horaria} /></span>
                        <span className="num text-xs text-muted">+{d.horas_peores} h</span>
                      </li>
                    ))}
                  </ul>
                )}
                {href && <p className="text-xs text-muted">Toca un día para abrir su simulación hora por hora en el boletín.</p>}
              </aside>
            </div>
          ) : (
            <>
              <CalendarMonth diario={R.dias} horas={R.dias.map(catsDelDia)} unidades={R.unidades} hrefBase={href} compact />
              {href && <p className="text-xs text-muted">Toca un día para abrir su simulación hora por hora en el boletín.</p>}
            </>
          )}
        </Seccion>

        {/* Contaminantes y meteorología */}
        <Seccion id="contaminantes" eyebrow="Contaminantes y meteorología" titulo="Quién define la categoría y cómo se mueve durante el día">
          <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <div className="card p-5">
              <p className="mb-2 text-sm font-semibold text-ink">Contaminante responsable · % de días y de horas</p>
              <ResponsibleChart n={N} />
            </div>
            <div className="card space-y-4 p-5">
              <p className="text-sm font-semibold text-ink">Días con suficiencia (≥ 18 de 24 h válidas)</p>
              {Object.entries(N.suficiencia).map(([p, n]) => (
                <Meter key={p} label={<Pol p={p} />} value={Math.round((1000 * n) / N.dias_mes) / 10} sub={`${n} de ${N.dias_mes} días`} />
              ))}
              <p className="text-xs leading-relaxed text-muted">Si un contaminante no cumple la suficiencia, ese día no tiene indicador ni categoría para él. {ESTACION.clave} no mide NO₂ ni SO₂.</p>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {DIURNO.filter((s) => R.perfil_diurno[s.serie]).map((s) => (
              <div key={s.serie} className="card p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-sm font-semibold text-ink">{s.nombre}</p>
                  <span className="num text-xs text-muted">{unidadDe(s)}</span>
                </div>
                <DiurnalChart serie={s.serie} nombre={s.nombre} valores={R.perfil_diurno[s.serie]} bandas={R.bandas} unidad={unidadDe(s)} />
              </div>
            ))}
            <div className="card space-y-2 p-4 text-sm leading-relaxed text-ink-2">
              <p className="eyebrow">Promedio por hora del día</p>
              <p>
                {ex.pm !== null && <>El promedio de PM₁₀ (NowCast) es más alto a las <b className="num text-ink">{hh(ex.pm)}:00</b>. </>}
                {ex.o3 !== null && <>El de O₃, a las <b className="num text-ink">{hh(ex.o3)}:00</b>. </>}
                {ex.tmin !== null && ex.tmax !== null && <>La temperatura promedio más baja se registra a las <b className="num text-ink">{hh(ex.tmin)}:00</b> y la más alta a las <b className="num text-ink">{hh(ex.tmax)}:00</b>.</>}
              </p>
              <p className="text-muted">Son coincidencias en el tiempo, no relaciones causales demostradas. Las franjas de color son las bandas NOM del indicador horario.</p>
            </div>
          </div>
        </Seccion>

        {/* Máximos */}
        {(N.maximos?.length ?? 0) > 0 && (
          <Seccion id="maximos" eyebrow={`Máximos · ${R.nombre}`} titulo="¿Cuándo hubo máximos?">
            <Maximos maximos={N.maximos!.filter((m) => !["ET", "WS"].includes(m.variable))} />
            <p className="text-xs text-muted">La concentración horaria y el indicador pueden tener su máximo en horas o días distintos: el NowCast y el promedio de 8 h ponderan las horas previas, así que responden más a un episodio sostenido que a un pico aislado.</p>
          </Seccion>
        )}

        {/* Evolución */}
        <Seccion id="evolucion" eyebrow="Evolución entre periodos" titulo="Días por categoría en cada periodo analizado">
          {periodos.length > 1 ? (
            <div className="card p-5"><TrendChart periodos={periodos} /></div>
          ) : (
            <div className="rounded-2xl border border-dashed border-rule p-6 text-sm leading-relaxed text-ink-2">
              Hoy hay <b className="text-ink">un periodo procesado</b> ({R.nombre}). La comparación entre meses aparece aquí cuando el pipeline procese el siguiente periodo; cada sprint agrega uno.
            </div>
          )}
        </Seccion>

        {/* Datos y limitaciones */}
        <Seccion id="datos" eyebrow="Calidad de los datos" titulo="Qué tan completos están los datos y qué no podemos afirmar">
          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
            <div className="card grid gap-4 p-5 sm:grid-cols-2">
              <p className="text-sm font-semibold text-ink sm:col-span-2">Disponibilidad horaria por variable</p>
              {R.disponibilidad.map((x) => <Meter key={x.variable} label={x.nombre} value={x.disponibilidad} />)}
            </div>
            <div className="card space-y-3 p-5 text-sm leading-relaxed text-ink-2">
              <p className="text-sm font-semibold text-ink">Limitaciones declaradas</p>
              <ul className="list-disc space-y-2 pl-5 marker:text-muted">
                {R.ausentes.length > 0 && <li><b className="text-ink">Sin datos en todo el periodo:</b> {R.ausentes.join(", ")}. No se imputan ni se sustituyen con otra estación.</li>}
                {N.dias_sin_datos.length > 0 && <li><b className="text-ink">Días sin categoría:</b> {N.dias_sin_datos.map((f) => +f.slice(8)).join(", ")} de {mes}.</li>}
                {R.limitaciones.map((l) => <li key={l}>{l}</li>)}
                {periodos.length === 1 && <li>Un solo periodo analizado: los patrones describen {R.nombre} y no se generalizan al año.</li>}
              </ul>
              {href && <Link href={`${href}#datos`} className="inline-block text-sm font-medium text-accent">Ver la bitácora de limpieza completa →</Link>}
            </div>
          </div>
          {R.descargas.length > 0 && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm font-semibold text-ink">Tablas procesadas y evidencia técnica</p>
                {href && <Link href={`${href}#evidencia`} className="text-sm font-medium text-accent">Cómo reproducir el análisis →</Link>}
              </div>
              <Descargas items={R.descargas} />
            </div>
          )}
        </Seccion>
      </div>
    </>
  );
}
