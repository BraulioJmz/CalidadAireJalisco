import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { BitacoraTable } from "@/components/BitacoraTable";
import { CalendarMonth } from "@/components/CalendarMonth";
import { DaysVsHoursChart, HourOfDayChart, ResponsibleChart } from "@/components/charts/DistributionCharts";
import { AvailabilityMatrix, VariablesTable } from "@/components/DataQuality";
import { Descargas, fechaHora, Maximos, Reproducir } from "@/components/Evidencia";
import { MapaJalisco } from "@/components/MapaJalisco";
import { MensajesNOM } from "@/components/MensajesNOM";
import { DiurnalChart } from "@/components/observatorio/charts";
import { SimulationPlayer } from "@/components/SimulationPlayer";
import { CatPill, Legend, Pol } from "@/components/ui";
import { CATS, catBg, dec, dow, fmt, MES_LARGO, ORD, parseT, pct, PL } from "@/lib/aire";
import { getDescargas, getMapa, getPeriodo } from "@/lib/data";
import { momentosClave } from "@/lib/momentos";
import { fmtTramos, franjasDelDia, hh } from "@/lib/resumen";
import { ACADEMIA, ESTACION } from "@/lib/site";

const PERIODO = "2024-03";

export const metadata: Metadata = {
  title: "Reporte técnico 1 · marzo 2024",
  description: "Transformación, análisis y visualización de la calidad del aire en la estación Miravalle (Jalisco) con el Índice AIRE Y SALUD, marzo 2024.",
};

const TOC = [
  ["introduccion", "1", "Introducción"],
  ["datos", "2", "Área de estudio y datos"],
  ["metodo", "3", "Método"],
  ["resultados", "4", "Resultados"],
  ["discusion", "5", "Discusión"],
  ["conclusiones", "6", "Conclusiones y limitaciones"],
  ["evidencia", "7", "Reproducibilidad"],
  ["referencias", "", "Referencias"],
] as const;

/** Por qué elegimos cada visualización (requisito del entregable). */
const VISUALES = [
  ["Mapa de localización", "Sitúa la estación en Jalisco y en la red de SEMADET; la representatividad de los datos depende de ese contexto."],
  ["Matriz de disponibilidad", "Horas con dato por día y variable: muestra los huecos antes de interpretar cualquier resultado."],
  ["Línea de tiempo con reproducción", "Reproduce la llegada de los datos hora por hora. Las bandas de la NOM van de fondo para leer la categoría sin un segundo eje; la meteorología se grafica en paneles aparte, alineados en el tiempo."],
  ["Recorrido guiado", "Fija los momentos clave del periodo y los explica, para leer la simulación como una secuencia de diapositivas."],
  ["Calendario mensual", "Cada día con su categoría, contaminante responsable e indicador; la tira de 24 horas contrasta la lectura horaria con la diaria."],
  ["Barras apiladas de días y horas", "La misma escala porcentual para ambas perspectivas hace visible cuánto cambia la interpretación al resumir el día."],
  ["Barras por hora del día", "Cuentan los días en cada categoría a cada hora y ubican las franjas críticas."],
  ["Múltiplos pequeños del perfil diurno", "Una variable por panel, cada una con su escala, para comparar horarios sin sugerir relaciones mediante un doble eje."],
  ["Tablas", "Para valores exactos con fecha y hora (máximos, días desfavorables, numeralia) una tabla es más precisa que una gráfica."],
] as const;

/* ---------- piezas de maquetación del reporte ---------- */

function Seccion({ id, n, titulo, children }: { id: string; n: string; titulo: string; children: ReactNode }) {
  return (
    <section aria-labelledby={`${id}-t`} className="space-y-6">
      <h2 id={id} className="display scroll-mt-24 border-b border-rule pb-3 text-[1.9rem] font-medium leading-tight text-ink sm:text-[2.2rem]">
        <span id={`${id}-t`}>{n && <span className="mr-3 text-muted">{n}.</span>}{titulo}</span>
      </h2>
      {children}
    </section>
  );
}

function Sub({ n, titulo, children }: { n: string; titulo: string; children: ReactNode }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink"><span className="num mr-2 text-muted">{n}</span>{titulo}</h3>
      {children}
    </div>
  );
}

function P({ children }: { children: ReactNode }) {
  return <p className="max-w-[72ch] text-[1.02rem] leading-[1.75] text-ink-2 [&_b]:font-semibold [&_b]:text-ink">{children}</p>;
}

function Figura({ n, pie, fuente, children }: { n: number; pie: ReactNode; fuente?: string; children: ReactNode }) {
  return (
    <figure className="space-y-3">
      <div className="rounded-xl border border-rule bg-surface p-3 sm:p-5">{children}</div>
      <figcaption className="max-w-[80ch] text-sm leading-relaxed text-ink-2">
        <b className="text-ink">Figura {n}.</b> {pie}{fuente && <span className="text-muted"> Fuente: {fuente}</span>}
      </figcaption>
    </figure>
  );
}

function Tabla({ n, titulo, nota, children }: { n: number; titulo: ReactNode; nota?: ReactNode; children: ReactNode }) {
  return (
    <figure className="space-y-2">
      <figcaption className="text-sm text-ink-2"><b className="text-ink">Tabla {n}.</b> {titulo}</figcaption>
      <div className="scroll-thin overflow-x-auto rounded-xl border border-rule bg-surface">{children}</div>
      {nota && <p className="text-xs leading-relaxed text-muted">{nota}</p>}
    </figure>
  );
}

const th = "px-4 py-2.5 text-left text-[0.72rem] font-medium uppercase tracking-[0.08em] text-muted";
const td = "px-4 py-2.5 align-top";

export default function Reporte1() {
  const D = getPeriodo(PERIODO);
  const mapa = getMapa();
  const N = D.numeralia;
  const P0 = D.perfil;
  const vars = P0.variables;
  const C = D.categorias_por_hora;
  const F = franjasDelDia(C);
  const hv = N.horario_vs_diario;
  const rec = D.periodo_simulacion;
  const mes = MES_LARGO[Number(PERIODO.slice(5)) - 1];

  const dt = N.dias_con_categoria, ht = N.horas_con_categoria;
  const db = N.dias_por_categoria.Buena, hb = N.horas_por_categoria.Buena;
  const pred = Object.entries(N.dias_por_categoria).sort((a, b) => b[1] - a[1])[0];
  const resp = Object.entries(N.dias_por_responsable).sort((a, b) => b[1] - a[1]);
  const conDatos = vars.filter((v) => v.validos > 0);
  const sinDatos = vars.filter((v) => v.validos === 0);
  const rh = vars.find((v) => v.variable === "RH");
  const horas = D.diario.map((_, i) => D.horario.slice(i * 24, i * 24 + 24).map((h) => h.Cat_global));
  const hMM = Array.from({ length: 24 }, (_, h) => h).filter((h) => (C["Muy Mala"]?.[h] ?? 0) > 0);
  const maximos = N.maximos ?? [];
  const mx = (v: string, t = "max") => maximos.find((m) => m.variable === v && m.tipo === t);
  const pmMax = mx("PM10_NowCast"), o3Max = mx("O3");

  // Simulación: momentos clave del periodo recomendado (los mismos del recorrido guiado)
  const i0 = D.horario.findIndex((h) => h.t === rec.inicio);
  const ventana = D.horario.slice(i0, i0 + 72);
  const momentos = momentosClave(ventana, D.diario, D.unidades);
  const peorSim = ventana.reduce((a, r) => ((ORD[r.Cat_global] ?? -1) > (ORD[a] ?? -1) ? r.Cat_global : a), "Buena");

  // Días en que el resumen diario oculta horas peores y las partículas no alcanzaron la compleción
  const ocultos = D.diario.filter((d) => d.Cat_global !== "Sin datos" && Number(d.horas_peores_que_diaria ?? 0) > 0
    && (d.PM10_suficiencia === "No cumple" || d["PM2.5_suficiencia"] === "No cumple"));
  const diasSinSuf = (p: string) => D.diario.filter((d) => d[`${p}_suficiencia`] === "No cumple").map((d) => +d.FECHA.slice(8));

  const bit = D.bitacora.reduce<Record<string, Record<string, number>>>((acc, b) => {
    const r = (acc[b.regla] ??= {});
    r[b.clasificacion] = (r[b.clasificacion] ?? 0) + 1;
    return acc;
  }, {});
  const clasifs = [...new Set(D.bitacora.map((b) => b.clasificacion))];

  const sim = { horario: D.horario, diario: D.diario, periodo_simulacion: rec, mensajes: D.mensajes, descripcion_riesgo: D.descripcion_riesgo, riesgo: D.riesgo, unidades: D.unidades, bandas: D.bandas, indicador_horario: D.indicador_horario };
  const fechaCorta = (t: string) => { const p = parseT(t); return `${p.d} de ${MES_LARGO[p.m - 1]}`; };

  return (
    <article>
      {/* ------- Portada ------- */}
      <header className="border-b border-rule bg-surface">
        <div className="mx-auto max-w-5xl px-4 pb-12 pt-12 sm:px-6 sm:pt-16 lg:px-8">
          <p className="eyebrow">Reporte técnico núm. 1 · Sprint 1 · {ACADEMIA.unidad}</p>
          <h1 className="display mt-5 max-w-4xl text-[2.3rem] font-medium leading-[1.08] text-ink sm:text-5xl">
            Del dato horario a la información: calidad del aire en la estación Miravalle, Jalisco, durante {mes} de 2024
          </h1>
          <p className="mt-5 text-ink-2">{ACADEMIA.equipo} · {ACADEMIA.materia} · {ACADEMIA.universidad}</p>
          <p className="mt-1 text-sm text-muted">
            Estación {ESTACION.nombre} ({ESTACION.clave}), red de monitoreo de SEMADET · Periodo: 1 al 31 de {mes} de 2024 · Norma: NOM-172-SEMARNAT-2023
          </p>

          <div className="mt-10 max-w-[80ch] border-l-2 border-ink pl-5">
            <p className="text-[1.02rem] leading-[1.75] text-ink-2">
              <b className="text-ink">Resumen.</b> Este reporte documenta un proceso reproducible para convertir los registros horarios de la
              estación {ESTACION.nombre} en información del Índice AIRE Y SALUD. Se prepararon {P0.registros} registros horarios de {vars.length} variables,
              se aplicaron los criterios de la NOM-172-SEMARNAT-2023 para obtener indicadores y categorías horarias y diarias, y se simuló la llegada
              progresiva de la información. De {dt} días con categoría, predominó la categoría <b className="text-ink">{pred[0]}</b> ({pred[1]} días) y{" "}
              {PL[resp[0][0]]} fue el contaminante responsable en {resp[0][1]} de ellos. La perspectiva horaria difiere de la diaria:
              el {pct(hb, ht)} % de las horas tuvo calidad Buena, frente al {pct(db, dt)} % de los días. El deterioro se concentró
              de {fmtTramos(F.critica)}, lo que permite a la academia planear sus actividades al aire libre por franja horaria.
            </p>
            <p className="mt-3 text-sm text-muted"><b className="text-ink-2">Palabras clave:</b> calidad del aire; Índice AIRE Y SALUD; NOM-172-SEMARNAT-2023; NowCast; PM₁₀; Área Metropolitana de Guadalajara.</p>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:px-8 xl:grid-cols-[190px_minmax(0,1fr)]">
        <aside className="hidden xl:block">
          <nav aria-label="Contenido del reporte" className="sticky top-24 space-y-0.5 pt-14 text-sm">
            <p className="eyebrow mb-3">Contenido</p>
            {TOC.map(([id, n, t]) => (
              <a key={id} href={`#${id}`} className="flex gap-2 rounded-md px-2 py-1.5 text-ink-2 transition hover:bg-surface-2 hover:text-ink">
                <span className="num w-3 text-muted">{n}</span>{t}
              </a>
            ))}
          </nav>
        </aside>

        <div className="min-w-0 space-y-20 py-14">
          {/* ======================= 1 ======================= */}
          <Seccion id="introduccion" n="1" titulo="Introducción">
            <P>
              La NOM-172-SEMARNAT-2023 establece cómo obtener y comunicar, de forma horaria y diaria, el Índice AIRE Y SALUD: el estado de la
              calidad del aire, los riesgos a la salud y las medidas para reducir la exposición. Entre una medición horaria y un mensaje
              para la población median varios pasos (validación, cálculo de una concentración base, clasificación en bandas y selección del
              mensaje), y cada uno puede cambiar la interpretación.
            </P>
            <P>
              El trabajo se plantea desde la perspectiva de {ACADEMIA.nombre}, una institución académica ficticia cercana a la estación, que usa
              estos datos para decidir cuándo y cómo realizar actividades al aire libre con su comunidad ({ACADEMIA.comunidad}).
            </P>
            <P><b>Objetivo.</b> Desarrollar un proceso reproducible para preparar, transformar, analizar y visualizar datos ambientales, y comprender cómo una medición horaria se convierte en información útil para interpretar la calidad del aire.</P>
            <div className="max-w-[72ch] space-y-2">
              <p className="text-[1.02rem] font-semibold text-ink">Preguntas guía</p>
              <ol className="list-decimal space-y-1.5 pl-6 text-[1.02rem] leading-[1.7] text-ink-2">
                <li>¿Qué ocurrió durante {mes} y cómo cambia la interpretación entre la perspectiva horaria y la diaria?</li>
                <li>¿Cómo se transforma un dato ambiental desde que se genera hasta convertirse en información útil para interpretar la calidad del aire?</li>
              </ol>
            </div>
          </Seccion>

          {/* ======================= 2 ======================= */}
          <Seccion id="datos" n="2" titulo="Área de estudio y datos">
            <Sub n="2.1" titulo="Localización de la estación">
              <P>
                La estación {ESTACION.nombre} ({ESTACION.clave}) forma parte de la red de monitoreo de la calidad del aire de la Secretaría de Medio
                Ambiente y Desarrollo Territorial (SEMADET) del estado de Jalisco. Se ubica en el sur del municipio de Guadalajara
                (20.6145° N, 103.3434° O; {ESTACION.altitud}), en Av. Gobernador Curiel esquina con J. Salomé Piña, dentro de la clínica
                núm. 92 del IMSS. Mide O₃, CO, PM₁₀ y PM₂.₅; no mide NO₂ ni SO₂. Conforme al numeral 5.1.2.5 de la NOM, el índice se calcula y se
                comunica por estación, sin combinarlo con otras.
              </P>
              {mapa && (
                <Figura n={1} fuente={mapa.fuente}
                  pie={<>Localización de la estación {ESTACION.nombre} en Jalisco. (a) Municipios del estado, con el Área Metropolitana de Guadalajara (AMG) resaltada. (b) Acercamiento al AMG con las {mapa.zona.estaciones.length} estaciones de monitoreo de SEMADET registradas en la hoja <i>Param</i>.</>}>
                  <MapaJalisco mapa={mapa} clave={ESTACION.clave} />
                </Figura>
              )}
            </Sub>

            <Sub n="2.2" titulo="Fuente y variables">
              <P>
                Los datos provienen del archivo <span className="num">BD_2024.xlsx</span> de SEMADET (hoja <i>Data</i>, registros horarios de 13 estaciones;
                hoja <i>Param</i>, catálogo de estaciones y unidades). Se extrajeron los {P0.registros} registros de {ESTACION.clave} para {mes} de 2024,
                de {P0.registros_esperados} esperados, sin registros duplicados. {conDatos.length} de {vars.length} variables tienen al menos un dato en el periodo.
                La Tabla 1 resume la unidad, el tipo y la disponibilidad de cada una.
              </P>
              <Tabla n={1} titulo={`Variables de la estación ${ESTACION.clave}: unidad, tipo, disponibilidad y estadísticos en ${mes} de 2024.`}
                nota={`Variables sin ningún dato en el periodo: ${sinDatos.map((v) => v.nombre.toLowerCase()).join(", ")}.`}>
                <VariablesTable vars={vars} />
              </Tabla>
              {rh && rh.validos === 0 && (
                <P>La humedad relativa, variable mínima del análisis, no tiene datos en {mes} de 2024 en ninguna estación de la red. Se declara como limitación y no se sustituye con datos de otra fuente.</P>
              )}
            </Sub>

            <Sub n="2.3" titulo="Calidad de los datos">
              <P>
                Antes de calcular cualquier indicador se revisaron los faltantes, los problemas de formato y los valores atípicos o inconsistentes.
                La Figura 2 muestra las horas con dato de cada variable por día.
              </P>
              <Figura n={2} pie="Horas con dato por día y variable. Los huecos determinan qué indicadores pueden calcularse según los criterios de compleción de la NOM." fuente="elaboración propia con datos de SEMADET.">
                <AvailabilityMatrix faltantes={P0.faltantes_por_dia} dias={D.diario.length} />
              </Figura>
              <div className="max-w-[72ch] space-y-2">
                <p className="text-[1.02rem] font-semibold text-ink">Problemas de formato identificados</p>
                <ul className="list-disc space-y-1.5 pl-6 text-[0.98rem] leading-[1.7] text-ink-2">
                  {P0.formato.map((f) => <li key={f}>{f}</li>)}
                  <li>En la hoja <i>Param</i>, las estaciones instaladas en 2024 (COU, SAN y SMT) tienen el nombre y la abreviatura intercambiados; se corrigen al leer el catálogo.</li>
                </ul>
              </div>
              <Tabla n={2} titulo="Valores marcados por el control de calidad, según regla y clasificación."
                nota="Ningún valor se eliminó: cada uno se clasificó como error, evento real probable o valor a revisar, y la decisión quedó registrada en la bitácora.">
                <table className="w-full min-w-[560px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Regla</th>{clasifs.map((c) => <th key={c} className={`${th} text-right`}>{c}</th>)}<th className={`${th} text-right`}>Total</th></tr></thead>
                  <tbody>
                    {Object.entries(bit).map(([regla, cs]) => (
                      <tr key={regla} className="border-t border-rule">
                        <td className={`${td} text-ink`}>{regla}</td>
                        {clasifs.map((c) => <td key={c} className={`${td} num text-right text-ink-2`}>{cs[c] ?? "—"}</td>)}
                        <td className={`${td} num text-right text-ink`}>{Object.values(cs).reduce((a, b) => a + b, 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Tabla>
              <details className="rounded-xl border border-rule bg-surface p-4">
                <summary className="cursor-pointer text-sm font-medium text-ink">Consultar la bitácora completa ({D.bitacora.length} registros)</summary>
                <div className="mt-4"><BitacoraTable rows={D.bitacora} /></div>
              </details>
            </Sub>
          </Seccion>

          {/* ======================= 3 ======================= */}
          <Seccion id="metodo" n="3" titulo="Método">
            <Sub n="3.1" titulo="Criterios de limpieza y transformación">
              <ol className="max-w-[72ch] list-decimal space-y-2 pl-6 text-[1.02rem] leading-[1.7] text-ink-2 [&_b]:text-ink">
                <li><b>Lectura sin modificar la fuente.</b> El archivo original se abre solo en lectura; las variables se identifican por nombre de columna y el texto se convierte a valor faltante.</li>
                <li><b>Rejilla horaria completa.</b> {P0.registros_esperados} horas esperadas (0 a 23 h), más 24 h previas que solo completan las ventanas móviles.</li>
                <li><b>Rango físico.</b> Solo se anulan valores imposibles (negativos, humedad mayor a 100 %, dirección mayor a 360°).</li>
                <li><b>Consistencia.</b> PM₂.₅ no puede superar a PM₁₀ en la misma hora.</li>
                <li><b>Atípicos.</b> Puntaje z robusto respecto de la mediana de la misma hora del día (|z| &gt; 3.5). Un valor alto se clasifica como evento real probable si se sostiene en las horas vecinas o si otro contaminante también aumenta; en otro caso queda por revisar. No se elimina ningún valor alto o bajo de forma automática.</li>
                <li><b>Sin imputación.</b> Los faltantes se conservan; los criterios de compleción de la NOM deciden si un indicador puede calcularse.</li>
              </ol>
            </Sub>

            <Sub n="3.2" titulo="Aplicación de la NOM-172-SEMARNAT-2023">
              <P>
                Para cada contaminante se calcula una concentración base (tabla 3 de la NOM), se redondea según el numeral 5.2.4 y se clasifica
                en una de cinco bandas (tablas 4 a 9). La categoría global de cada hora y de cada día es la más desfavorable entre los contaminantes
                con indicador válido (numeral 5.4.2); el contaminante que la define es el responsable. Si dos contaminantes empatan en categoría,
                se elige el más cercano al límite superior de su banda (criterio del equipo, porque la NOM no define desempate).
              </P>
              <Tabla n={3} titulo="Concentraciones base, criterios de compleción y redondeo aplicados (NOM-172-SEMARNAT-2023, numerales 5.2.3 a 5.2.5).">
                <table className="w-full min-w-[720px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Contaminante</th><th className={th}>Reporte horario</th><th className={th}>Reporte diario</th><th className={th}>Compleción</th><th className={th}>Redondeo</th></tr></thead>
                  <tbody className="text-ink-2">
                    {[
                      ["PM₁₀ y PM₂.₅", "Promedio móvil ponderado de 12 h (NowCast)", "Promedio de 24 h", "2 de las 3 horas más recientes (horario); 18 de 24 h (diario)", "Entero (µg/m³)"],
                      ["O₃", "Promedio horario", "Máximo de los promedios horarios del día", "18 de 24 h (diario)", "3 decimales (ppm)"],
                      ["CO", "Promedio móvil de 8 h", "Máximo de los promedios móviles de 8 h", "6 de 8 h (horario); 18 de 24 h (diario)", "2 decimales (ppm)"],
                    ].map((r) => <tr key={r[0]} className="border-t border-rule">{r.map((c, i) => <td key={i} className={`${td} ${i === 0 ? "text-ink" : ""}`}>{c}</td>)}</tr>)}
                  </tbody>
                </table>
              </Tabla>
              <P>
                El promedio móvil ponderado de 12 horas (Anexo A de la NOM) da más peso a las horas recientes. Con <i>C</i><sub>i</sub> la concentración de la
                hora <i>i</i> (<i>i</i> = 1 es la más reciente) y <i>W</i> = máx(0.5, 1 − (<i>C</i><sub>máx</sub> − <i>C</i><sub>mín</sub>)/<i>C</i><sub>máx</sub>), redondeado a dos decimales:
              </P>
              <div className="num max-w-[72ch] overflow-x-auto rounded-lg bg-surface-2 px-5 py-4 text-center text-[1.05rem] text-ink">
                NowCast = <i>F</i> · Σ <i>W</i><sup>i−1</sup><i>C</i><sub>i</sub> / Σ <i>W</i><sup>i−1</sup>, &nbsp; <i>F</i> = 0.714 (PM₁₀), 0.694 (PM₂.₅)
              </div>
              <P>
                Las horas faltantes conservan su posición <i>i</i>. El cálculo usa sin cambios la función de referencia proporcionada en el curso, validada
                contra los 24 casos de prueba; en {mes} de 2024 su redondeo coincide en todas las horas con la regla del numeral 5.2.4.
              </P>
              <Tabla n={4} titulo="Bandas del Índice AIRE Y SALUD aplicadas: límite superior de cada categoría (tablas 4 a 10 de la NOM)."
                nota="Para PM₁₀ y PM₂.₅ la NOM define límites graduales; se aplica la columna «a partir de enero de 2024», que corresponde a la fecha de los datos. Colores según la tabla 11 (RGB); el blanco indica estación sin información.">
                <table className="w-full min-w-[640px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Categoría</th><th className={th}>Riesgo</th>
                    {["O3", "CO", "PM10", "PM2.5"].map((p) => <th key={p} className={`${th} text-right`}>{PL[p]} <span className="normal-case">({D.unidades[p]})</span></th>)}</tr></thead>
                  <tbody>
                    {CATS.map((c, i) => (
                      <tr key={c} className="border-t border-rule">
                        <td className={td}><span className="inline-flex items-center gap-2 text-ink"><i className="inline-block size-3 rounded-sm" style={catBg(c)} />{c}</span></td>
                        <td className={`${td} text-ink-2`}>{D.riesgo[c]}</td>
                        {["O3", "CO", "PM10", "PM2.5"].map((p) => { const b = D.bandas[p]; const d = p === "O3" ? 3 : p === "CO" ? 2 : 0; return (
                          <td key={p} className={`${td} num text-right text-ink`}>{i < 4 ? `≤ ${fmt(b[i], d)}` : `> ${fmt(b[3], d)}`}</td>); })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Tabla>
              <P>
                Cada categoría se acompaña de los mensajes de la tabla 12 de la NOM, diferenciados para tres grupos: población en general;
                menores de 12 años y personas gestantes; y personas con enfermedades cardiovasculares o respiratorias y mayores de 60 años.
              </P>
            </Sub>

            <Sub n="3.3" titulo="Simulación de la llegada de datos y agregación diaria">
              <P>
                Para simular la recepción en tiempo real, en cada hora solo se usan el dato de esa hora y los anteriores. El NowCast y el promedio de 8 h
                son causales, de modo que la simulación reproduce lo que era posible saber en cada momento; la categoría diaria solo existe al cerrar el día.
                Criterio de selección del periodo representativo: {rec.criterio.charAt(0).toLowerCase() + rec.criterio.slice(1)}
              </P>
            </Sub>

            <Sub n="3.4" titulo="Propuesta de visualización: agencia, audiencia y objetivo">
              <P>
                <b>Agencia.</b> {ACADEMIA.nombre} es una institución académica. A diferencia de una autoridad ambiental, no opera la red ni emite alertas oficiales:
                usa los datos públicos de SEMADET para tomar decisiones internas y, por su carácter educativo, para explicar cómo se construye la información.
              </P>
              <P>
                <b>Audiencia.</b> Su comunidad ({ACADEMIA.comunidad}), en particular quienes programan actividades al aire libre (educación física, entrenamientos,
                ceremonias) y los grupos sensibles que define la NOM. Es una audiencia con formación académica que valora ver el método, no solo el resultado.
              </P>
              <P>
                <b>Objetivo de comunicación.</b> Doble: (1) apoyar la decisión de cuándo y cómo realizar actividades al aire libre, lo que exige leer la calidad del aire
                por hora del día; y (2) mostrar de forma trazable cómo una medición horaria se convierte en una categoría y un mensaje.
              </P>
              <Tabla n={5} titulo="Referentes consultados, elementos retomados y diferencias de la propuesta."
                nota="Los referentes se consultaron el 27 de septiembre de 2026 como inspiración; no se copió su diseño.">
                <table className="w-full min-w-[760px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Referente</th><th className={th}>Qué presenta</th><th className={th}>Qué retomamos</th><th className={th}>En qué nos diferenciamos y por qué</th></tr></thead>
                  <tbody className="text-ink-2">
                    {[
                      ["SIMAJ, SEMADET (aire.jalisco.gob.mx)", "Mapa de estaciones con el Índice AIRE Y SALUD, la estación con mayor nivel destacada, recomendaciones por grupo de población, reporte diario y descarga de datos.",
                        "El índice por estación, los colores oficiales, los mensajes por grupo y la ubicación en el AMG (Figura 1).",
                        "SIMAJ informa el estado actual a toda la población de Jalisco. Nosotros analizamos un mes pasado de una sola estación para una comunidad académica, por lo que añadimos la simulación, la comparación horaria y diaria y la trazabilidad del cálculo."],
                      ["SINAICA, INECC (sinaica.inecc.gob.mx)", "Mapa nacional con estaciones coloreadas por categoría, leyenda que asocia calidad del aire y riesgo a la salud, índice diario y leyenda de mantenimiento o sin información en blanco; datos históricos descargables.",
                        "La leyenda que une categoría y riesgo, el blanco para «sin información» y la publicación de los datos procesados.",
                        "SINAICA compara estaciones a escala nacional; nuestra decisión depende de la variación dentro del día en una estación, así que priorizamos la hora del día sobre el mapa."],
                      ["RESPIRA (app.respira.org.mx)", "Al consultarla, la dirección no mostraba la aplicación (redirigía a una página de inicio de sesión ajena); por las coordenadas del enlace corresponde a Mexicali, Baja California.",
                        "No fue posible revisar su diseño.", "—"],
                    ].map((r) => <tr key={r[0]} className="border-t border-rule">{r.map((c, i) => <td key={i} className={`${td} ${i === 0 ? "font-medium text-ink" : ""}`}>{c}</td>)}</tr>)}
                  </tbody>
                </table>
              </Tabla>
              <Tabla n={6} titulo="Visualizaciones empleadas y justificación de su elección para la agencia.">
                <table className="w-full min-w-[560px] text-sm">
                  <tbody>{VISUALES.map(([t, d], i) => <tr key={t} className={i ? "border-t border-rule" : ""}><td className={`${td} w-56 font-medium text-ink`}>{t}</td><td className={`${td} text-ink-2`}>{d}</td></tr>)}</tbody>
                </table>
              </Tabla>
            </Sub>
          </Seccion>

          {/* ======================= 4 ======================= */}
          <Seccion id="resultados" n="4" titulo="Resultados">
            <Sub n="4.1" titulo={`Simulación horaria: ${fechaCorta(rec.inicio)} al ${fechaCorta(rec.fin)}`}>
              <P>
                La Figura 3 reproduce el periodo seleccionado. Puede recorrerse como una secuencia de diapositivas con los momentos clave, o hora por hora
                con los controles de reproducción. Para cada hora se muestra el flujo completo: dato horario, procesamiento, indicador, categoría e información para la comunidad.
              </P>
              <Figura n={3} pie={<>Simulación de la llegada horaria de datos en la estación {ESTACION.clave}. Las franjas de color son las bandas de la NOM; la línea delgada es el dato horario y la gruesa, el indicador. Las flechas indican hacia dónde sopla el viento.</>} fuente="elaboración propia con datos de SEMADET.">
                <SimulationPlayer data={sim} />
              </Figura>

              <Tabla n={7} titulo="Elementos requeridos para la simulación y dónde se muestran en la Figura 3.">
                <table className="w-full min-w-[640px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Elemento</th><th className={th}>Cómo se muestra</th></tr></thead>
                  <tbody className="text-ink-2">
                    {[
                      ["Llegada progresiva de los datos", "La línea de tiempo de 72 h solo dibuja las horas ya recibidas y se completa al reproducir; los indicadores usan únicamente horas pasadas."],
                      ["Fecha y hora", "Encabezado del aviso y eje de la línea de tiempo."],
                      ["Concentración del contaminante", "Línea delgada de cada contaminante y paso 01 «Dato horario»."],
                      ["Procesamiento", "Paso 02 y panel «Información disponible»: horas válidas en cada ventana (12, 3 y 8 h) y factor W del NowCast."],
                      ["Indicador calculado", "Línea gruesa (NowCast, promedio de 8 h u O₃ horario) y paso 03."],
                      ["Categoría de calidad del aire", "Franja superior con la categoría global de cada hora, bandas de la NOM de fondo y paso 04."],
                      ["Cambios de categoría", "Marcas verticales en la franja superior, bitácora de avisos emitidos y recorrido guiado."],
                      ["Variables meteorológicas", "Paneles de temperatura y de viento (velocidad y dirección con flechas)."],
                      ["Información para el usuario", "Riesgo (tabla 10) y mensajes por grupo de población (tabla 12) de la NOM; paso 05."],
                      ["Periodo representativo", `Selección automática (${fechaCorta(rec.inicio)} al ${fechaCorta(rec.fin)}) con el criterio de la sección 3.3; puede elegirse cualquier otro periodo del mes.`],
                    ].map((r) => <tr key={r[0]} className="border-t border-rule"><td className={`${td} w-60 font-medium text-ink`}>{r[0]}</td><td className={td}>{r[1]}</td></tr>)}
                  </tbody>
                </table>
              </Tabla>

              <div className="max-w-[72ch] space-y-5">
                <P><b>¿Qué información estaba disponible en cada momento?</b> Solo la hora en curso y las anteriores. El NowCast de partículas exige datos en 2 de las 3 horas más recientes y el promedio de CO, en 6 de las últimas 8; la categoría diaria no existe hasta las 23:00. Cuando un indicador no puede calcularse, la categoría global se obtiene con los contaminantes restantes.</P>
                <div className="space-y-2">
                  <P><b>¿Cuándo se presentaron los cambios más importantes?</b> Hubo {rec.cambios} cambios de categoría en 72 horas y {rec.horas_mala_o_peor} horas en Mala o peor. La secuencia de momentos clave fue:</P>
                  <ol className="list-decimal space-y-2 pl-6 text-[0.98rem] leading-[1.7] text-ink-2">
                    {momentos.slice(1).map((m) => <li key={m.k}><b className="text-ink">{m.titulo}.</b> {m.texto}</li>)}
                  </ol>
                </div>
                <P><b>¿Qué variables pudieron relacionarse con esos cambios?</b> Los aumentos de partículas se presentan junto con las temperaturas bajas de la madrugada y la mañana y con viento débil; los de ozono, con las temperaturas máximas de la tarde (sección 4.4). Son coincidencias temporales: sin humedad relativa ni radiación solar no es posible sostener una relación causal.</P>
                <div className="space-y-2">
                  <P><b>¿Qué debería comunicar la academia?</b> En el momento de mayor deterioro (categoría {peorSim}), los mensajes que corresponden según la tabla 12 de la NOM son:</P>
                  <div className="rounded-lg border border-rule bg-surface p-4"><MensajesNOM m={D.mensajes[peorSim]} /></div>
                  <P>Como el NowCast responde con retraso a la mejora del dato horario, conviene advertir que el retiro del aviso puede demorar algunas horas.</P>
                </div>
              </div>
            </Sub>

            <Sub n="4.2" titulo="Análisis diario y numeralia">
              <Tabla n={8} titulo={`Numeralia diaria de ${mes} de 2024.`}>
                <table className="w-full min-w-[480px] text-sm">
                  <tbody className="text-ink-2">
                    {([
                      ["Días del periodo", N.dias_mes],
                      ["Días con categoría diaria", dt],
                      ["Días sin categoría (datos insuficientes)", `${N.dias_sin_datos.length} (${N.dias_sin_datos.map((d) => +d.slice(8)).join(" y ")})`],
                      ...CATS.map((c) => [<span key={c} className="inline-flex items-center gap-2"><i className="inline-block size-3 rounded-sm" style={catBg(c)} />Días en {c}</span>, N.dias_por_categoria[c] ?? 0]),
                      ...resp.map(([p, n]) => [<>Días con <Pol p={p} /> como responsable</>, n]),
                      ["Horas en Muy Mala o peor", N.horas_por_categoria["Muy Mala"] + N.horas_por_categoria["Extremadamente Mala"]],
                    ] as [ReactNode, ReactNode][]).map(([k, v], i) => (
                      <tr key={i} className={i ? "border-t border-rule" : ""}><td className={td}>{k}</td><td className={`${td} num text-right text-ink`}>{v}</td></tr>
                    ))}
                  </tbody>
                </table>
              </Tabla>
              <Figura n={4} pie="Calendario de categorías diarias. Cada día muestra su categoría, el contaminante responsable y su indicador; la tira inferior contiene las 24 categorías horarias. SS: Semana Santa. Al seleccionar un día se abre en la simulación." fuente="elaboración propia con datos de SEMADET.">
                <div className="space-y-3"><Legend /><CalendarMonth diario={D.diario} horas={horas} unidades={D.unidades} /></div>
              </Figura>
              <Tabla n={9} titulo="Días con las condiciones más desfavorables."
                nota="Orden: peor categoría diaria y, dentro de ella, cercanía del indicador al límite superior de la banda.">
                <table className="w-full min-w-[600px] text-sm">
                  <thead className="bg-surface-2"><tr><th className={th}>Fecha</th><th className={th}>Categoría</th><th className={th}>Responsable</th><th className={`${th} text-right`}>Indicador diario</th><th className={`${th} text-right`}>Horas en Mala o peor</th></tr></thead>
                  <tbody>{N.dias_mas_desfavorables.map((d) => { const p = parseT(d.fecha); return (
                    <tr key={d.fecha} className="border-t border-rule"><td className={`${td} num`}>{dow(d.fecha)} {p.d}</td><td className={td}><CatPill c={d.categoria} /></td><td className={td}><Pol p={d.responsable} /></td><td className={`${td} num text-right`}>{fmt(d.indicador, dec(d.responsable))} {d.unidad}</td><td className={`${td} num text-right`}>{d.horas_mala_o_peor}</td></tr>); })}</tbody>
                </table>
              </Tabla>
              <P>
                <b>¿Qué categoría predominó?</b> {pred[0]}, con {pred[1]} de {dt} días ({pct(pred[1], dt)} %). {CATS.filter((c) => c !== pred[0] && N.dias_por_categoria[c]).map((c) => `${c}: ${N.dias_por_categoria[c]} ${N.dias_por_categoria[c] === 1 ? "día" : "días"}`).join("; ")}.
                {" "}<b>¿Qué contaminante fue dominante con mayor frecuencia?</b> {PL[resp[0][0]]}, responsable en {resp[0][1]} días{resp[1] ? `; ${PL[resp[1][0]]} lo fue en ${resp[1][1]}` : ""}.
                Por hora el reparto es más equilibrado: {Object.entries(N.horas_por_responsable).map(([p, n]) => `${PL[p]} ${n} h`).join(", ")}.
              </P>
            </Sub>

            <Sub n="4.3" titulo="Perspectiva horaria frente a perspectiva diaria">
              <div className="grid gap-6 lg:grid-cols-2">
                <Figura n={5} pie="Porcentaje de días y de horas en cada categoría."><DaysVsHoursChart n={N} /></Figura>
                <Figura n={6} pie="Porcentaje de días y de horas en que cada contaminante definió la categoría."><ResponsibleChart n={N} /></Figura>
              </div>
              <Figura n={7} pie="Número de días en cada categoría según la hora del día." fuente="elaboración propia con datos de SEMADET.">
                <HourOfDayChart porHora={C} />
              </Figura>
              <P>
                <b>¿Qué diferencias existen entre la interpretación horaria y la diaria?</b> Por hora, el {pct(hb, ht)} % del tiempo tuvo calidad Buena; por día, el {pct(db, dt)} %.
                El promedio de 24 h de partículas extiende el pico de la mañana a todo el día. En {hv.dias_con_horas_peores} de {dt} días hubo horas peores que la categoría
                diaria ({hv.horas_peores_total} horas en total){hMM.length ? `, y las ${N.horas_por_categoria["Muy Mala"]} horas en Muy Mala, ocurridas entre las ${hh(hMM[0])}:00 y las ${hh(hMM[hMM.length - 1])}:59, ${N.dias_por_categoria["Muy Mala"] ? "no siempre se reflejan" : "no se reflejan"} en la categoría de ningún día` : ""}.
                De {fmtTramos(F.critica)} la mitad o más de los días estuvo en Mala o peor; de {fmtTramos(F.buena)}, al menos ocho de cada diez días fueron Buena.
              </P>
              <P>
                <b>¿Qué información se pierde al resumir el día en una sola categoría?</b> El momento en que ocurre el deterioro, su duración, el valor máximo y el cambio
                de contaminante a lo largo del día. También se pierde lo ocurrido en días incompletos
                {ocultos.length > 0 ? <>: {ocultos.slice(0, 2).map((d) => `el ${+d.FECHA.slice(8)} de ${mes} quedó en ${d.Cat_global} aunque su peor hora fue ${d.peor_horaria}`).join(", y ")}, porque sus datos de partículas no alcanzaron la compleción de 18 horas.</> : "."}
              </P>
            </Sub>

            <Sub n="4.4" titulo="Máximos y relación con la meteorología">
              {maximos.length > 0 && (
                <Tabla n={10} titulo="Valores máximos y mínimos del periodo, con fecha, hora y categoría."
                  nota="La concentración horaria y el indicador pueden alcanzar su máximo en horas o días distintos, porque el NowCast y el promedio de 8 h ponderan las horas previas.">
                  <Maximos maximos={maximos} />
                </Tabla>
              )}
              {pmMax && o3Max && (
                <P>El indicador de PM₁₀ alcanzó {fmt(pmMax.valor)} µg/m³ ({fechaHora(pmMax.fecha_hora)}, categoría {pmMax.categoria}) y el O₃, {fmt(o3Max.valor, 3)} ppm ({fechaHora(o3Max.fecha_hora)}, categoría {o3Max.categoria}). En promedio, las partículas son más altas por la mañana, cuando la temperatura es más baja, y el ozono por la tarde, cuando la temperatura es máxima (Figura 8).</P>
              )}
              <Figura n={8} pie="Promedio por hora del día de PM₁₀ (NowCast), O₃, temperatura y velocidad del viento. Cada panel tiene su propia escala; las franjas de color son las bandas de la NOM." fuente="elaboración propia con datos de SEMADET.">
                <div className="grid gap-5 sm:grid-cols-2">
                  {([["PM10_NowCast", "PM₁₀ · NowCast", D.unidades.PM10], ["O3", "O₃ · horario", D.unidades.O3], ["ET", "Temperatura", "°C"], ["WS", "Velocidad del viento", "m/s"]] as const).map(([serie, nombre, unidad]) => (
                    <div key={serie}>
                      <p className="flex items-baseline justify-between text-sm font-medium text-ink">{nombre}<span className="num text-xs text-muted">{unidad}</span></p>
                      <DiurnalChart serie={serie} nombre={nombre} unidad={unidad} valores={D.perfil_diurno[serie]} bandas={D.bandas} />
                    </div>
                  ))}
                </div>
              </Figura>
            </Sub>
          </Seccion>

          {/* ======================= 5 ======================= */}
          <Seccion id="discusion" n="5" titulo="Discusión: interpretación desde la academia">
            <P>
              <b>Información útil.</b> El deterioro tiene un horario definido. A las 08:00 hubo categoría Mala o peor en {(C.Mala?.[8] ?? 0) + (C["Muy Mala"]?.[8] ?? 0) + (C["Extremadamente Mala"]?.[8] ?? 0)} días,
              mientras que a las 16:00 fue Buena en {C.Buena?.[16] ?? 0}. {PL[resp[0][0]]} explica la mayoría de las horas en Mala o peor. Esto permite planear por franja horaria y no solo por día.
            </P>
            <P>
              <b>Decisión que apoya.</b> Programar la actividad física, los entrenamientos, las ceremonias y los eventos al aire libre de preferencia de {fmtTramos(F.buena)},
              y reducir la actividad vigorosa en exteriores de {fmtTramos(F.critica)}, sobre todo para los grupos sensibles que define la NOM. En los días en que el
              ozono alcanza Aceptable o Mala, revisar también las primeras horas de la tarde.
            </P>
            <P>
              <b>Forma de comunicarlo.</b> La categoría diaria, por sí sola, sobrestima el riesgo de la tarde y subestima el de la mañana. Se propone un aviso horario cuando
              cambie la categoría, que indique el contaminante responsable y los mensajes de la tabla 12. Cuando la estación no reporte, el aviso debe decir «Fuera de operación»
              o «Sin información» (numeral 5.1.2.6), nunca suponer que el aire está bien.
            </P>
          </Seccion>

          {/* ======================= 6 ======================= */}
          <Seccion id="conclusiones" n="6" titulo="Conclusiones y limitaciones">
            <ol className="max-w-[72ch] list-decimal space-y-3 pl-6 text-[1.02rem] leading-[1.7] text-ink-2">
              <li>Un dato horario solo se vuelve información útil después de validarlo, transformarlo en una concentración base conforme a la NOM, clasificarlo en una banda y traducirlo en un mensaje para cada grupo de población. Cada paso quedó documentado y es reproducible.</li>
              <li>En {mes} de 2024 predominó la categoría {pred[0]} y {PL[resp[0][0]]} fue el principal responsable. El deterioro se concentró en la mañana y la tarde fue mayoritariamente Buena.</li>
              <li>La perspectiva diaria es adecuada para el resumen del mes; la decisión operativa requiere la perspectiva horaria, porque un mismo día puede pasar de {hMM.length ? "Muy Mala" : "Mala"} en la mañana a Buena en la tarde.</li>
            </ol>
            <div className="max-w-[72ch] space-y-2">
              <p className="text-[1.02rem] font-semibold text-ink">Limitaciones</p>
              <ul className="list-disc space-y-1.5 pl-6 text-[0.98rem] leading-[1.7] text-ink-2">
                <li>Se analizó un solo mes en una sola estación; los patrones deben confirmarse con los periodos de los siguientes sprints.</li>
                <li>Las relaciones con la meteorología son coincidencias temporales, no relaciones causales demostradas.</li>
                <li>No hay datos de {sinDatos.filter((v) => ["RH", "RS", "PP"].includes(v.variable)).map((v) => v.nombre.toLowerCase()).join(", ")}; el anemómetro solo registra de 0.4 a 1.2 m/s.</li>
                <li>PM₁₀ no alcanzó la compleción diaria los días {diasSinSuf("PM10").join(", ")}, y PM₂.₅ los días {diasSinSuf("PM2.5").join(", ")}: en esos días la categoría diaria se basa en menos contaminantes.</li>
                <li>La fuente no incluye la escala de representatividad espacial de la estación (numeral 5.1.2.5).</li>
              </ul>
            </div>
          </Seccion>

          {/* ======================= 7 ======================= */}
          <Seccion id="evidencia" n="7" titulo="Reproducibilidad y evidencia técnica">
            <P>
              Todo el cálculo se realiza en Python y se ejecuta con un solo comando desde la raíz del repositorio; el sitio web solo presenta las tablas procesadas.
              Si se ejecuta de nuevo con la misma base, los resultados son idénticos. Las pruebas automáticas verifican el NowCast contra los casos de referencia y que
              los resultados de {mes} no cambien.
            </P>
            <Reproducir periodo={PERIODO} />
            <div className="space-y-3">
              <p className="text-[1.02rem] font-semibold text-ink">Descargas documentadas</p>
              <Descargas items={getDescargas(PERIODO)} />
            </div>
            <p className="text-sm text-ink-2">La justificación de cada visualización está en la sección 3.4. Los criterios completos están en la <Link href="/metodologia" className="text-accent underline-offset-2 hover:underline">página de metodología</Link>.</p>
          </Seccion>

          {/* ======================= Referencias ======================= */}
          <Seccion id="referencias" n="" titulo="Referencias">
            <ul className="max-w-[80ch] space-y-3 pl-6 text-sm leading-relaxed text-ink-2 [text-indent:-1.5rem]">
              <li>Secretaría de Medio Ambiente y Recursos Naturales. (2024, 25 de enero). <i>NOM-172-SEMARNAT-2023, Lineamientos para la obtención y comunicación del Índice AIRE Y SALUD</i>. Diario Oficial de la Federación. https://sidof.segob.gob.mx/notas/docFuente/5715154</li>
              <li>Instituto Nacional de Ecología y Cambio Climático. (2024). <i>NOM-172-SEMARNAT-2023. Índice AIRE Y SALUD</i> [Documento PDF]. SINAICA. https://sinaica.inecc.gob.mx/archivo/noms/NOM-172-SEMARNAT-2023-Indice-AIRE-y-SALUD.pdf</li>
              <li>Secretaría de Medio Ambiente y Desarrollo Territorial del Estado de Jalisco. (2024). <i>Base de datos horaria de calidad del aire 2024</i> [BD_2024.xlsx]. https://aire.jalisco.gob.mx/</li>
              <li>Secretaría de Salud. (2021). <i>NOM-025-SSA1-2021, Salud ambiental. Criterio para evaluar la calidad del aire ambiente, con respecto a las partículas suspendidas PM₁₀ y PM₂.₅</i>. Diario Oficial de la Federación.</li>
              <li>U.S. Environmental Protection Agency. (2018). <i>Technical assistance document for the reporting of daily air quality: The Air Quality Index (AQI)</i> (EPA-454/B-18-007).</li>
              <li>Instituto Nacional de Estadística y Geografía. (2023). <i>Marco Geoestadístico: límites municipales de Jalisco</i>.</li>
            </ul>
          </Seccion>
        </div>
      </div>
    </article>
  );
}
