import type { Metadata } from "next";
import Link from "next/link";
import { BitacoraTable } from "@/components/BitacoraTable";
import { CalendarMonth } from "@/components/CalendarMonth";
import { DaysVsHoursChart, HourOfDayChart, ResponsibleChart } from "@/components/charts/DistributionCharts";
import { AvailabilityMatrix, VariablesTable } from "@/components/DataQuality";
import { SimulationPlayer } from "@/components/SimulationPlayer";
import { CatPill, Kpi, Legend, Pol, QA, SectionHead } from "@/components/ui";
import { dec, dow, fmt, parseT, pct } from "@/lib/aire";
import { getPeriodo } from "@/lib/data";
import { ACADEMIA, ESTACION } from "@/lib/site";

const PERIODO = "2024-03";

export const metadata: Metadata = {
  title: "Boletín 1 · marzo 2024",
  description: "Sprint 1: del dato horario a la categoría del Índice AIRE Y SALUD en Miravalle, marzo 2024.",
};

const TOC = [
  ["datos", "1", "Preparación de los datos"],
  ["simulacion", "2", "Simulación horaria"],
  ["numeralia", "3", "Análisis diario"],
  ["academia", "4", "Lectura para la academia"],
] as const;

export default function Sprint1() {
  const D = getPeriodo(PERIODO);
  const N = D.numeralia;
  const P = D.perfil;
  const vars = P.variables;
  const conDatos = vars.filter((v) => v.validos > 0).length;
  const rh = vars.find((v) => v.variable === "RH")!;
  const pm25 = vars.find((v) => v.variable === "PM2.5")!;
  const horas = D.diario.map((_, i) => D.horario.slice(i * 24, i * 24 + 24).map((h) => h.Cat_global));
  const dt = N.dias_con_categoria, ht = N.horas_con_categoria;
  const db = N.dias_por_categoria.Buena, hb = N.horas_por_categoria.Buena;
  const pred = Object.entries(N.dias_por_categoria).sort((a, b) => b[1] - a[1])[0];
  const dom = Object.entries(N.dias_por_responsable).sort((a, b) => b[1] - a[1])[0];
  const hv = N.horario_vs_diario;
  const C = D.categorias_por_hora;
  const tot = (h: number) => Object.values(C).reduce((s, arr) => s + arr[h], 0);
  const pm10_8 = D.perfil_diurno.PM10[8] ?? 0;
  const pm10_tarde = Math.max(...D.perfil_diurno.PM10.slice(16, 19).map((v) => v ?? 0));
  const sim = { horario: D.horario, diario: D.diario, periodo_simulacion: D.periodo_simulacion, mensajes: D.mensajes, riesgo: D.riesgo, unidades: D.unidades, bandas: D.bandas, indicador_horario: D.indicador_horario };

  return (
    <article>
      {/* ------- Portada del boletín ------- */}
      <header className="relative overflow-hidden border-b border-rule">
        <div className="grid-paper pointer-events-none absolute inset-0 opacity-60" />
        <div className="relative mx-auto max-w-7xl px-4 pb-12 pt-12 sm:px-6 sm:pt-16 lg:px-8">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <span className="eyebrow">Boletín técnico · Núm. 1 · Sprint 1</span>
            <span className="num rounded-full border border-rule bg-surface px-2.5 py-1 text-[0.68rem] text-ink-2">AM-OCA-BT-{PERIODO}</span>
          </div>
          <h1 className="display mt-5 max-w-4xl text-[2.6rem] font-medium leading-[1.02] text-ink sm:text-6xl lg:text-7xl">
            Marzo 2024: del dato horario a la información
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink-2">
            Qué pasó con la calidad del aire en Miravalle durante marzo y cómo cambia la lectura al pasar de la hora al día.
            Seguimos cada medición desde que llega hasta que se vuelve una recomendación para nuestra comunidad.
          </p>
          <dl className="mt-8 grid max-w-4xl grid-cols-2 gap-x-6 gap-y-4 text-sm sm:grid-cols-4">
            {[["Estación", `${ESTACION.clave} · ${ESTACION.nombre}`], ["Periodo", "1–31 de marzo de 2024"], ["Norma", "NOM-172-SEMARNAT-2023"], ["Elaboró", `${ACADEMIA.equipo} · ${ACADEMIA.unidad}`]].map(([k, v]) => (
              <div key={k}><dt className="eyebrow">{k}</dt><dd className="mt-1 text-ink">{v}</dd></div>
            ))}
          </dl>
          <ol className="mt-10 grid gap-px overflow-hidden rounded-2xl border border-rule bg-[var(--rule)] md:grid-cols-5">
            {[["Dato horario", "Concentración medida por la estación cada hora."], ["Procesamiento", "Control de calidad, ventanas de 12 h y 8 h, suficiencia."], ["Indicador", "NowCast (PM), promedio 8 h (CO), valor horario (O₃)."], ["Categoría", "Índice AIRE Y SALUD, de Buena a Extremadamente Mala."], ["Información", "Aviso y recomendación para la comunidad."]].map(([t, d], i) => (
              <li key={t} className="bg-surface p-4">
                <span className="num text-[0.68rem] text-accent">{String(i + 1).padStart(2, "0")}</span>
                <p className="mt-1.5 font-semibold text-ink">{t}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">{d}</p>
              </li>
            ))}
          </ol>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-10 px-4 sm:px-6 lg:px-8 xl:grid-cols-[200px_minmax(0,1fr)]">
        {/* Índice lateral */}
        <aside className="hidden xl:block">
          <nav aria-label="Contenido del boletín" className="sticky top-24 space-y-1 pt-16 text-sm">
            <p className="eyebrow mb-3">Contenido</p>
            {TOC.map(([id, n, t]) => (
              <a key={id} href={`#${id}`} className="flex gap-2 rounded-lg px-2 py-1.5 text-ink-2 transition hover:bg-surface-2 hover:text-ink">
                <span className="num text-muted">{n}</span>{t}
              </a>
            ))}
            <Link href="/metodologia" className="flex gap-2 rounded-lg px-2 py-1.5 text-ink-2 transition hover:bg-surface-2 hover:text-ink"><span className="num text-muted">↗</span>Metodología</Link>
          </nav>
        </aside>

        <div className="min-w-0 space-y-24 py-16">
          {/* ------- 1. Datos ------- */}
          <section className="space-y-8">
            <SectionHead id="datos" n="1" eyebrow="Preparación de los datos" title="Qué llegó de la estación y en qué estado">
              <p>Extrajimos Miravalle de <span className="num text-ink">BD_2024.xlsx</span> (SEMADET). Las 24 horas del 29 de febrero solo calientan las ventanas del NowCast (12 h) y del promedio de CO (8 h). No eliminamos valores altos o bajos: primero los clasificamos como posible error o evento real.</p>
            </SectionHead>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi value={P.registros} unit={`/ ${P.registros_esperados}`} label="registros horarios; sin horas faltantes ni duplicadas" />
              <Kpi value={conDatos} unit={`/ ${vars.length}`} label="variables con al menos un dato en marzo" />
              <Kpi value={fmt(rh.disponibilidad)} unit="%" tone="alert" label="humedad relativa: sin datos en toda la red SEMADET" />
              <Kpi value={fmt(pm25.disponibilidad, 1)} unit="%" label={<>disponibilidad de <Pol p="PM2.5" />, la más baja entre los contaminantes</>} />
            </div>
            <div className="space-y-6">
              <div className="space-y-3">
                <h3 className="font-semibold text-ink">Variables, unidades y disponibilidad</h3>
                <VariablesTable vars={vars} />
                <p className="text-xs text-muted">Todas las variables son numéricas tras la conversión. Miravalle no mide NO₂ ni SO₂; la categoría global usa O₃, CO, PM₁₀ y PM₂.₅.</p>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="card p-5">
                  <h3 className="mb-3 font-semibold text-ink">Problemas de formato</h3>
                  <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-ink-2">{P.formato.map((f) => <li key={f}>{f}</li>)}</ul>
                </div>
                <div className="card p-5">
                  <h3 className="mb-3 font-semibold text-ink">Criterios de limpieza y transformación</h3>
                  <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-ink-2 marker:font-mono marker:text-muted">
                    <li><b className="text-ink">Rejilla horaria completa.</b> 744 horas esperadas (0–23 h).</li>
                    <li><b className="text-ink">Rango físico.</b> Solo se anula lo imposible (negativos, RH &gt; 100 %, WD &gt; 360°). Sin casos en marzo.</li>
                    <li><b className="text-ink">Consistencia.</b> PM₂.₅ no puede superar a PM₁₀ en la misma hora. Sin casos.</li>
                    <li><b className="text-ink">Atípicos por hora del día.</b> z robusto contra la mediana de esa hora (|z| &gt; 3.5). Es <em>evento real probable</em> si se sostiene en horas vecinas u otro contaminante sube a la vez; si no, queda en <em>revisar</em>.</li>
                    <li><b className="text-ink">Resolución del sensor.</b> El anemómetro solo reporta de 0.4 a 1.2 m/s; 0.4 m/s se lee como calma.</li>
                    <li><b className="text-ink">Sin imputación.</b> La NOM decide si hay datos suficientes para cada indicador.</li>
                  </ol>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <h3 className="font-semibold text-ink">Horas con dato por día</h3>
              <p className="text-sm text-muted">El 17 de marzo la estación no reportó nada y el 18 solo en parte. PM₂.₅ se pierde el 13 y del 29 al 31.</p>
              <AvailabilityMatrix faltantes={P.faltantes_por_dia} dias={D.diario.length} />
            </div>
            <div className="space-y-3">
              <h3 className="font-semibold text-ink">Bitácora de control de calidad</h3>
              <p className="text-sm text-muted">Cada valor marcado, la regla que lo detectó y la decisión. Ninguno se eliminó.</p>
              <BitacoraTable rows={D.bitacora} />
            </div>
          </section>

          {/* ------- 2. Simulación ------- */}
          <section className="space-y-8">
            <SectionHead id="simulacion" n="2" eyebrow="Simulación de datos horarios" title="Como si los datos llegaran en tiempo real">
              <p>Reproducimos el mes hora por hora. En cada momento solo usamos lo que ya había llegado: el dato de esa hora y los anteriores. Así se ve qué sabía la academia, cuándo cambió la categoría y qué aviso correspondía.</p>
            </SectionHead>
            <SimulationPlayer data={sim} />
            <div className="space-y-6">
              <h3 className="display text-2xl font-medium text-ink">Lectura del periodo 26–28 de marzo</h3>
              <div className="grid gap-8 md:grid-cols-2">
                <QA q="¿Qué información estaba disponible en cada momento?"><p>Solo la hora en curso y las previas. El NowCast de partículas necesita 2 de las 3 horas más recientes y pondera las últimas 12; el CO necesita 6 de las últimas 8. La categoría <em>diaria</em> no existe hasta cerrar el día a las 23:00. El 28 de marzo desde las 19:00 se pierde PM₂.₅ y la categoría global se estima con los otros tres contaminantes.</p></QA>
                <QA q="¿Cuándo se presentaron los cambios más importantes?"><p>Hubo 22 cambios en 72 horas. El más fuerte fue el 27 de marzo a las 08:00: PM₁₀ horario de 297 µg/m³, NowCast de 141 µg/m³ y categoría <b>Muy Mala</b> durante 08:00–09:00. A las 13:00 el responsable pasa de PM₁₀ a O₃ y a las 14:00 el ozono llega a 0.091 ppm, la única hora del mes con O₃ en <b>Mala</b>. A las 18:00 vuelve a Buena. El patrón se repite el 26 y el 28.</p></QA>
                <QA q="¿Qué variables pudieron relacionarse?"><p>Los máximos de PM₁₀ coinciden con las temperaturas más bajas de la madrugada y la mañana (9–16 °C) y con viento débil del NE–ENE (0.4–0.5 m/s). Los de O₃ coinciden con las temperaturas máximas (33–34 °C) y viento del SSO por la tarde. Son coincidencias en el tiempo, no causas demostradas; sin humedad ni radiación solar no podemos ir más lejos.</p></QA>
                <QA q="¿Qué debería comunicar la academia?"><p>El 27 a las 08:00, un aviso de <b>Muy Mala</b>: suspender la actividad física al aire libre y mantener a los grupos sensibles en interiores. Por la tarde el aviso cambia de contaminante (de partículas a ozono) y la precaución sigue hasta las 18:00. El NowCast baja más lento que el dato horario (a las 12:00 el PM₁₀ ya era 42 µg/m³, pero el indicador seguía en Mala): conviene avisar que la mejora se reflejará con retraso.</p></QA>
              </div>
            </div>
          </section>

          {/* ------- 3. Numeralia ------- */}
          <section className="space-y-8">
            <SectionHead id="numeralia" n="3" eyebrow="Análisis diario y numeralia" title="Marzo en números">
              <p>El indicador diario sigue la NOM: promedio de 24 h para partículas, máximo horario para O₃ y máximo del promedio de 8 h para CO. Cada contaminante necesita al menos 18 de 24 horas válidas; la categoría del día es la peor entre los que cumplen.</p>
            </SectionHead>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
              <Kpi value={N.dias_mes} label={<>días en marzo; <b className="text-ink">{dt}</b> con categoría diaria</>} />
              <Kpi value={N.dias_sin_datos.length} label={`días sin categoría (${N.dias_sin_datos.map((d) => +d.slice(8)).join(" y ")} de marzo)`} />
              <Kpi value={pred[1]} unit="días" label={<>en <b className="text-ink">{pred[0]}</b>, la categoría predominante</>} />
              <Kpi value={dom[1]} unit="días" label={<>con <b className="text-ink"><Pol p={dom[0]} /></b> como contaminante dominante</>} />
              <Kpi value={N.horas_por_categoria["Muy Mala"]} unit="horas" label="en Muy Mala; ningún día llegó a esa categoría" />
            </div>
            <div className="space-y-3">
              <Legend />
              <CalendarMonth diario={D.diario} horas={horas} unidades={D.unidades} />
              <p className="text-xs text-muted">Cada tarjeta muestra la categoría del día, el contaminante que la definió y su indicador; la tira inferior son sus 24 categorías horarias. SS = Semana Santa. Toca un día para verlo en la simulación.</p>
            </div>

            <div className="card grid gap-6 p-6 md:grid-cols-[1fr_1fr_1.4fr] md:items-center">
              <div><p className="num text-5xl font-semibold tracking-tight text-ink">{pct(db, dt)}%</p><p className="mt-1 text-sm text-ink-2">de los <b className="text-ink">días</b> tuvo categoría Buena ({db} de {dt})</p></div>
              <div><p className="num text-5xl font-semibold tracking-tight text-ink">{pct(hb, ht)}%</p><p className="mt-1 text-sm text-ink-2">de las <b className="text-ink">horas</b> tuvo categoría Buena ({hb} de {ht})</p></div>
              <p className="text-sm leading-relaxed text-ink-2">La misma estación, dos lecturas. El promedio de 24 h de PM₁₀ arrastra el pico de la mañana a todo el día: a las 08:00 el PM₁₀ horario promedió {fmt(pm10_8)} µg/m³ en el mes, y de 16:00 a 18:00 no pasó de {fmt(pm10_tarde)} µg/m³.</p>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="card p-5"><h3 className="mb-2 font-semibold text-ink">Días y horas por categoría</h3><DaysVsHoursChart n={N} /><p className="text-xs text-muted">Porcentaje sobre los días y las horas con categoría.</p></div>
              <div className="card p-5"><h3 className="mb-2 font-semibold text-ink">Contaminante responsable</h3><ResponsibleChart n={N} /><p className="text-xs text-muted">Porcentaje de días y de horas en que cada contaminante definió la categoría.</p></div>
            </div>
            <div className="card p-5">
              <h3 className="mb-2 font-semibold text-ink">Categoría horaria según la hora del día</h3>
              <HourOfDayChart porHora={C} />
              <p className="text-xs text-muted">Número de días de marzo en que cada hora tuvo cada categoría.</p>
            </div>

            <div className="space-y-3">
              <h3 className="font-semibold text-ink">Días con las condiciones más desfavorables</h3>
              <div className="card scroll-thin overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-surface-2 text-left"><tr className="num text-[0.68rem] uppercase tracking-[0.1em] text-muted">
                    <th className="px-4 py-2.5 font-medium">Fecha</th><th className="px-4 py-2.5 font-medium">Categoría diaria</th><th className="px-4 py-2.5 font-medium">Responsable</th><th className="px-4 py-2.5 text-right font-medium">Indicador</th><th className="px-4 py-2.5 text-right font-medium">Horas en Mala o peor</th></tr></thead>
                  <tbody>{N.dias_mas_desfavorables.map((d) => { const p = parseT(d.fecha); return (
                    <tr key={d.fecha} className="border-t border-rule"><td className="num px-4 py-2.5">{dow(d.fecha)} {p.d} mar</td><td className="px-4 py-2.5"><CatPill c={d.categoria} /></td><td className="px-4 py-2.5"><Pol p={d.responsable} /></td><td className="num px-4 py-2.5 text-right">{fmt(d.indicador, dec(d.responsable))} {d.unidad}</td><td className="num px-4 py-2.5 text-right">{d.horas_mala_o_peor}</td></tr>); })}</tbody>
                </table>
              </div>
              <p className="text-xs text-muted">Orden: primero la peor categoría del día y después qué tan cerca está su indicador del límite superior de esa categoría.</p>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
              <QA q="¿Qué categoría predominó?"><p><b>Mala</b>, con {N.dias_por_categoria.Mala} de {dt} días ({pct(N.dias_por_categoria.Mala, dt)}%). Le siguen Aceptable con {N.dias_por_categoria.Aceptable} días y Buena con {db}. No hubo días en Muy Mala ni Extremadamente Mala. El único día Buena (7 de marzo) se calificó solo con O₃ y CO, porque PM₁₀ y PM₂.₅ no alcanzaron las 18 horas.</p></QA>
              <QA q="¿Qué contaminante fue dominante con mayor frecuencia?"><p><b>PM₁₀</b> definió la categoría en {N.dias_por_responsable.PM10} de {dt} días y O₃ en {N.dias_por_responsable.O3 ?? 0} (6, 7, 24 y 25 de marzo). Por hora el reparto cambia: PM₁₀ define {N.horas_por_responsable.PM10} horas, O₃ {N.horas_por_responsable.O3}, PM₂.₅ {N.horas_por_responsable["PM2.5"]} y CO {N.horas_por_responsable.CO ?? 0}. El ozono domina casi todas las tardes (14–19 h).</p></QA>
              <QA q="¿Qué diferencias hay entre la lectura horaria y la diaria?"><p>Por hora, {pct(hb, ht)}% del tiempo fue Buena; por día, solo {pct(db, dt)}%. En {hv.dias_con_horas_peores} días hubo horas peores que la categoría del día ({hv.horas_peores_total} horas en total), y las {N.horas_por_categoria["Muy Mala"]} horas en Muy Mala no aparecen en ningún día. Hubo {hv.cambios_categoria_total} cambios de categoría horaria en el mes.</p></QA>
              <QA q="¿Qué información se pierde al resumir el día?"><p>Se pierde <b>cuándo</b> ocurre el problema (mañana contra tarde), <b>cuánto dura</b>, el <b>pico</b> más alto y el <b>cambio de contaminante</b> a lo largo del día. También se pierde lo que pasa en días incompletos: el 6 de marzo quedó en Aceptable aunque tuvo 4 horas en Muy Mala, y el 7 quedó en Buena con 3 horas en Mala, porque sus datos de partículas no alcanzaron la suficiencia.</p></QA>
            </div>
          </section>

          {/* ------- 4. Academia ------- */}
          <section className="space-y-8">
            <SectionHead id="academia" n="4" eyebrow="Interpretación desde la agencia" title="¿Qué le sirve a nuestra academia?">
              <p>{ACADEMIA.nombre} es una institución académica cercana a la estación. Su comunidad ({ACADEMIA.comunidad}) pasa buena parte del día en el campus y en actividades al aire libre. Estas conclusiones se apoyan solo en los datos de marzo de 2024.</p>
            </SectionHead>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="card space-y-2 p-6"><p className="eyebrow">Información útil</p><h3 className="display text-xl font-medium text-ink">El problema tiene horario</h3>
                <p className="text-sm leading-relaxed text-ink-2">A las 08:00 hubo Mala o Muy Mala en {C.Mala[8] + C["Muy Mala"][8]} de {tot(8)} días; a las 16:00 fue Buena en {C.Buena[16]} de {tot(16)}. PM₁₀ explica casi todas las horas en Mala y todas las de Muy Mala. Esto permite planear por franja horaria, no solo por día.</p></div>
              <div className="card space-y-2 p-6"><p className="eyebrow">Decisión que apoya</p><h3 className="display text-xl font-medium text-ink">Actividades al aire libre por la tarde</h3>
                <p className="text-sm leading-relaxed text-ink-2">Programar educación física, entrenamientos, ceremonias y eventos al aire libre de preferencia después de las 14:00. Entre las 07:00 y las 12:00, reducir la actividad física intensa en exteriores, sobre todo para grupos sensibles. En días con O₃ alto (27 y 28 de marzo), revisar también la franja de 13:00 a 17:00.</p></div>
              <div className="card space-y-2 p-6"><p className="eyebrow">Cómo comunicarlo</p><h3 className="display text-xl font-medium text-ink">Aviso por hora, no solo diario</h3>
                <p className="text-sm leading-relaxed text-ink-2">La categoría diaria sola exagera la tarde y suaviza la mañana. Proponemos un aviso por hora cuando cambie la categoría, que diga qué contaminante la define y qué hacer. Si la estación no reporta (17 y 18 de marzo), comunicar “sin información” en lugar de suponer que el aire está bien.</p></div>
            </div>
            <div className="rounded-2xl border border-rule bg-surface-2 p-6">
              <h3 className="mb-3 font-semibold text-ink">Límites de estas conclusiones</h3>
              <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-ink-2">
                <li>Un solo mes y una sola estación: el patrón debe confirmarse con más meses en los siguientes sprints.</li>
                <li>Mostramos coincidencias en el tiempo entre contaminantes, temperatura y viento; no demostramos causas.</li>
                <li>No hay humedad relativa ni radiación solar en marzo, y el anemómetro tiene resolución limitada (0.4–1.2 m/s).</li>
                <li>PM₁₀ no alcanzó las 18 horas el 6, 7, 17 y 18 de marzo, y PM₂.₅ tampoco el 13, 14 y del 29 al 31: esos días tienen una categoría diaria incompleta.</li>
              </ul>
            </div>
            <div className="flex flex-wrap gap-3">
              {[["horario", "Excel horario"], ["diario", "Excel diario"]].map(([f, l]) => (
                <a key={f} href={`/descargas/${PERIODO}/MIR_${PERIODO}_${f}.xlsx`} className="rounded-full border border-rule bg-surface px-4 py-2 text-sm text-ink transition hover:border-ink-2">↓ {l}</a>
              ))}
              <a href={`/descargas/${PERIODO}/bitacora_limpieza.csv`} className="rounded-full border border-rule bg-surface px-4 py-2 text-sm text-ink transition hover:border-ink-2">↓ Bitácora (CSV)</a>
              <Link href="/metodologia" className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-bg transition hover:opacity-90">Ver metodología →</Link>
            </div>
          </section>
        </div>
      </div>
    </article>
  );
}
