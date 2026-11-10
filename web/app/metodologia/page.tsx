import type { Metadata } from "next";
import Link from "next/link";
import { REPOSITORIO } from "@/lib/site";
import { getSprint2 } from "@/lib/sprint2";

export const metadata: Metadata = {
  title: "Metodología · histórico 2015–2024 y evaluación",
  description: "Fuentes, indicadores de la NOM-172 y criterios adicionales de cobertura y comparación del análisis retrospectivo de Miravalle 2023–2024.",
};
export const dynamic = "force-static";

const NORMATIVA = [
  ["Indicadores horarios", "Las partículas usan NowCast de 12 horas con al menos 2 mediciones en las 3 horas más recientes. CO usa un promedio móvil de 8 horas con al menos 6 mediciones. O₃ y NO₂ usan la concentración base de una hora."],
  ["Indicadores diarios", "PM₁₀ y PM₂.₅ usan el promedio de 24 horas, con al menos 18 lecturas. CO usa el máximo diario de los promedios móviles de 8 horas; O₃ y NO₂, el máximo horario diario. El requisito adicional de 18 lecturas para gases se explica por separado."],
  ["Ajuste y redondeo", "El NowCast incorpora los factores de ajuste de partículas antes de redondear la concentración base final. Se aplica redondeo decimal mitad hacia arriba: partículas a enteros, CO a dos decimales y los demás gases a tres. Las categorías se asignan a la base redondeada."],
  ["Categoría más desfavorable", "La condición global toma la peor categoría de los contaminantes evaluables, sin promediar sus códigos ordinales. La composición fija de cuatro contaminantes para comparar años es una decisión adicional del proyecto."],
];
const PROYECTO = [
  ["Una referencia común", "Se eligen las bandas de 2024 de la NOM para clasificar ambos años. Es una comparación retrospectiva bajo la misma referencia; no reconstruye los avisos oficiales de 2023 ni utiliza umbrales posteriores."],
  ["Suficiencia diaria adicional", "Para los máximos diarios de gases se requieren al menos 18 lecturas crudas del día, como criterio conservador del proyecto. La exigencia normativa de 18/24 citada para partículas no se extiende a gases como si fuera la misma regla."],
  ["Contexto de las ventanas", "En la comparación archivada 2023–2024, sin diciembre de 2022, se excluyen las primeras 11 horas de partículas y 7 horas de CO de 2023. Enero de 2024 sí utiliza diciembre de 2023. Es una precaución adicional a los mínimos de cada ventana."],
  ["Fechas comparables", "Se parean fechas por mes y día con indicador válido en ambos años. El 29 de febrero de 2024 permanece en los descriptivos y no forma un par. Así hay 365 fechas anuales posibles; el pareamiento no controla día de semana ni meteorología."],
  ["Cobertura para comparar", "Se destaca un cambio mensual con al menos 75 % de fechas pareadas. Para el año se requiere además al menos 75 % de pares en cada trimestre. Los resúmenes descriptivos mensuales se señalan suficientes con al menos 75 % de días evaluables. Estos umbrales del proyecto no son reglas normativas de compleción de ventanas ni garantizan representatividad."],
  ["Dos alcances globales", "El global comparable exige indicadores válidos de PM₁₀, PM₂.₅, O₃ y CO. El máximo disponible considera los contaminantes presentes y señala su composición parcial. NO₂ puede afectar este último, pero no entra en el conjunto comparable. Se conservan todos los determinantes empatados; sus frecuencias pueden sumar más que los días."],
  ["Eventos para inspección", "Se seleccionan tres máximos diarios por año y contaminante separados al menos 7 días, y tres máximos horarios separados al menos 24 horas. Un episodio reúne al menos 2 días consecutivos Mala o peor; los faltantes lo interrumpen. Si cruza de año conserva sus fechas y duración reales."],
  ["Meteorología descriptiva", "Temperatura externa (ET), humedad relativa (RH) y velocidad del viento (WS) se resumen diariamente con al menos 18 lecturas. Spearman usa pares del mismo mes y año y requiere al menos 15; una serie constante no produce correlación. No se calculan p-valores. La dirección del viento es circular y no se correlaciona linealmente."],
];

export default function Metodologia() {
  const data = getSprint2();
  return (
    <div className="mx-auto max-w-5xl space-y-14 px-4 py-16 sm:px-6 lg:px-8">
      <header className="space-y-4">
        <p className="eyebrow">Metodología · Miravalle (MIR)</p>
        <h1 className="display text-5xl font-medium leading-[1.05] text-ink sm:text-6xl">De la medición a la evidencia</h1>
        <p className="text-ink-2 leading-relaxed">Todo el análisis corresponde a la estación de monitoreo Miravalle (MIR), durante 2015–2024. Los perfiles por mes describen temporadas del año, no otras estaciones de monitoreo. Las medias históricas mensuales requieren al menos 75 % de horas; las anuales exigen además ese mínimo por trimestre. Son criterios adicionales del proyecto, no garantías de representatividad. Las bandas retrospectivas de 2024 se mantienen explícitas.</p>
        <p className="text-ink-2 leading-relaxed">La evaluación de PM10 usa 24 horas observadas hasta el origen t y calendario para predecir concentraciones horarias a +1, +2 y +3 horas. Entrena con 2015–2022, selecciona con 2023 y reajusta con 2015–2023 antes de evaluar 2024. Se conserva la exposición descriptiva previa de 2024, la población completa de 6,225 orígenes (70.9 %) y la subestimación de altas. Los pronósticos no se convierten directamente en categorías; 114 µg/m³ es un umbral diagnóstico de entrenamiento.</p>
        <p className="text-ink-2 leading-relaxed">El histórico puede usar contexto de años previos a 2023 que no estaba disponible en la comparación archivada 2023–2024. Las diferencias de arranque no sustituyen sus resultados. Se mantienen SO₂ 2023 excluido por calibración y NO₂ 2024 exploratorio. Las reglas de 2023–2024 conservadas se detallan a continuación.</p>
        <p className="text-ink-2 leading-relaxed">El modelo actual utiliza PM10 y calendario. Las fuentes contienen meteorología con disponibilidad discontinua; se conserva su análisis descriptivo reproducible. Se excluyó de esta primera muestra para no reducir su continuidad, sin demostrar que carezca de utilidad predictiva.</p>
        <p><Link href="/#fuentes" className="underline text-accent">Fuentes de 2015–2024, hashes y descargas del panel integrado →</Link></p>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-2">La comparación pareada de 2023 y 2024 es una consulta dentro del histórico, bajo las mismas bandas retrospectivas de 2024. Distingue las reglas del Índice AIRE Y SALUD de las decisiones adicionales que permiten describir cobertura, fechas coincidentes y asociaciones meteorológicas.</p>
        <p className="text-sm text-ink-2"><Link className="font-medium text-accent" href="/#historico/comparar">Comparar periodos →</Link></p>
      </header>

      <section className="space-y-4 text-sm leading-relaxed text-ink-2" aria-labelledby="lectura-historica">
        <h2 id="lectura-historica" className="display text-3xl text-ink">Qué se compara en 2015–2024</h2>
        <p>Las medias históricas resumen concentraciones horarias crudas: no son categorías. Las categorías diarias usan promedios de partículas, máximo móvil de 8 horas de CO y máximo horario diario de O₃, NO₂ y SO₂, con bandas retrospectivas de 2024. NO y NOX no se clasifican.</p>
        <p>El mínimo de 18 lecturas diarias de partículas es normativo. Exigir 18 lecturas crudas también para los máximos de gases, 75 % de cobertura mensual y cobertura trimestral adicional para el año son criterios del proyecto. Los huecos interrumpen las líneas y los episodios; no se imputan mediciones.</p>
        <p>Para comparar se usan las mismas fechas mes/día y se exige 75 % de pares, además por trimestre si el periodo es anual. El 29 de febrero solo tiene par si ambos años son bisiestos. El histórico aprovecha contexto desde 2015; sus originales y resultados están disponibles en las descargas.</p>
      </section>
      <details className="space-y-8 border-t border-rule pt-5"><summary className="cursor-pointer display text-2xl text-ink">Reglas y evidencia de la comparación archivada 2023–2024</summary>
      <section className="space-y-5" aria-labelledby="fuentes">
        <h2 id="fuentes" className="display text-3xl font-medium text-ink">De la medición al resumen</h2>
        <div className="card space-y-4 p-5 text-sm leading-relaxed text-ink-2">
          <p>Se utilizan los libros horarios de SEMADET suministrados para 2023 y 2024, filtrados a la estación MIR. Los originales se conservan íntegros. La rejilla comprende 8,760 horas en 2023 y 8,784 en 2024; una fila presente puede contener mediciones ausentes o excluidas. Las fechas conservan la hora civil codificada en la fuente, sin inferir conversiones de zona horaria.</p>
          <p>El control de calidad distingue ausencia de fila, medición faltante, exclusión y lectura utilizable. Se excluyen valores no finitos, negativos y valores meteorológicos fuera de los rangos de plausibilidad definidos por el proyecto. Los extremos y los casos PM₂.₅ mayor que PM₁₀ se conservan con banderas para revisión; un atípico estadístico no demuestra un error instrumental.</p>
          <p>Los indicadores y las categorías se calculan antes de llegar al tablero. Las vistas, CSV y figuras comparten esos resultados; cada resumen identifica su población, unidad y denominador.</p>
        </div>
      </section>

      <section className="space-y-5" aria-labelledby="indicadores">
        <h2 id="indicadores" className="display text-3xl font-medium text-ink">Qué magnitud se muestra</h2>
        <div className="card overflow-x-auto" tabIndex={0} role="region" aria-label="Indicadores y unidades">
          <table className="w-full min-w-[640px] text-left text-sm">
            <caption className="sr-only">Indicador horario y estadístico del resumen de días evaluables</caption>
            <thead className="bg-surface-2 text-ink"><tr><th scope="col" className="px-4 py-3">Variable y unidad</th><th scope="col" className="px-4 py-3">Base horaria</th><th scope="col" className="px-4 py-3">Resumen del periodo</th></tr></thead>
            <tbody>{data.pollutants.map(p => <tr key={p.key} className="border-t border-rule text-ink-2"><th scope="row" className="px-4 py-3 font-medium text-ink">{p.label} · {p.unit}{p.key === "NO2" && <span className="block text-xs font-normal text-muted">Exploratorio, solo 2024</span>}</th><td className="px-4 py-3">{p.hourly}</td><td className="px-4 py-3">{p.daily}</td></tr>)}</tbody>
          </table>
        </div>
        <p className="text-sm leading-relaxed text-ink-2">La media de máximos diarios de un gas no equivale a su concentración media durante el periodo. La comparación pareada usa solo fechas válidas coincidentes; los descriptivos usan todos los días evaluables de cada año. No se suman concentraciones de contaminantes distintos ni se promedian categorías.</p>
      </section>

      <section className="space-y-5" aria-labelledby="normativa">
        <h2 id="normativa" className="display text-3xl font-medium text-ink">Reglas normativas aplicadas</h2>
        <p className="text-sm leading-relaxed text-ink-2">La referencia es la NOM-172-SEMARNAT-2023: bases diarias (tabla 3 y numeral 5.1.2.3), redondeo y suficiencia (5.2.4–5.2.5), bandas (tablas 4–9), categoría más desfavorable (5.4.2) y NowCast (anexo A). Elegir su referencia de 2024 para ambos años es una decisión retrospectiva del proyecto.</p>
        <dl className="card divide-y divide-[var(--rule)]">{NORMATIVA.map(([title, text]) => <div key={title} className="grid gap-2 p-5 sm:grid-cols-[200px_1fr] sm:gap-6"><dt className="font-semibold text-ink">{title}</dt><dd className="text-sm leading-relaxed text-ink-2">{text}</dd></div>)}</dl>
      </section>

      <section className="space-y-5" aria-labelledby="criterios-proyecto">
        <h2 id="criterios-proyecto" className="display text-3xl font-medium text-ink">Criterios adicionales del proyecto</h2>
        <p className="text-sm leading-relaxed text-ink-2">Las siguientes decisiones organizan la comparación académica. Se distinguen de los requisitos normativos de cada indicador.</p>
        <dl className="card divide-y divide-[var(--rule)]">{PROYECTO.map(([title, text]) => <div key={title} className="grid gap-2 p-5 sm:grid-cols-[200px_1fr] sm:gap-6"><dt className="font-semibold text-ink">{title}</dt><dd className="text-sm leading-relaxed text-ink-2">{text}</dd></div>)}</dl>
      </section>

      <section className="space-y-5" aria-labelledby="alcance">
        <h2 id="alcance" className="display text-3xl font-medium text-ink">Cobertura e incertidumbre</h2>
        <div className="card space-y-4 p-5 text-sm leading-relaxed text-ink-2">
          <p>El periodo completo no alcanza el criterio de comparación anual del proyecto. Se muestran los datos y su cobertura, sin concluir una mejora o un deterioro anual representativo. El porcentaje de días Mala o peor divide entre días evaluables; la distribución de categorías incluye también los días sin datos del calendario. Una ausencia no representa cero ni Buena y los huecos no se conectan como si hubiera mediciones.</p>
          <p>Los archivos no contienen registros subhorarios para comprobar 45 de 60 minutos ni calibraciones o bitácoras instrumentales individuales. Pasar controles de software, plausibilidad y suficiencia no acredita validación instrumental. SO₂ de 2023 se excluye por invalidación documentada en el Informe Nacional de Calidad del Aire 2023 del INECC (p. 222); no hay datos de SO₂ de 2024.</p>
          <p>En la comparación 2023–2024, NO₂ es un complemento exploratorio de 2024: hay lecturas desde el 16 de agosto, pero el catálogo Param de MIR no lo enumera. Los archivos no acreditan su procedencia instrumental, calibración ni un cambio de equipamiento. No se presenta como comparación con 2023.</p>
          <p>La cobertura desigual, la dependencia temporal, la estacionalidad y las variables omitidas limitan la interpretación. Una correlación no demuestra causalidad; un pico o el contaminante determinante de una categoría no identifica incendios, tráfico, inversión térmica ni otra fuente emisora. Las ventanas suficientes tampoco garantizan haber observado el verdadero máximo diario.</p>
        </div>
      </section>

      </details>
      <details className="space-y-4 border-t border-rule pt-5"><summary className="cursor-pointer display text-2xl text-ink">Cálculo y configuración reproducibles</summary>
        <p className="text-sm leading-relaxed text-ink-2">Los indicadores históricos, sus categorías y los agregados se calculan en el pipeline Python y se exportan como resultados procesados. La aplicación consulta esas salidas; no recalcula normativa ni entrena modelos en el navegador.</p>
        <p className="text-sm leading-relaxed text-ink-2">El experimento PM10 C05 utiliza HistGradientBoostingRegressor directo por horizonte. Se probaron ocho configuraciones prefijadas y se seleccionó por MAE medio en 2023. Configuración congelada: 31 hojas, tasa 0.05, 150 iteraciones, mínimo de 30 muestras por hoja, regularización L2=1 y sin early stopping automático. Los parámetros y predicciones no se ajustan con los errores de 2024.</p>
        <p className="text-sm leading-relaxed text-ink-2">La referencia de persistencia repite PM10(t). La referencia diaria usa PM10(t+h−24), la misma hora objetivo del día anterior. El acercamiento del gráfico cambia la ventana visible, no las predicciones ni las muestras evaluadas.</p>
      </details>
      <section className="space-y-5" aria-labelledby="evidencia">
        <h2 id="evidencia" className="display text-3xl font-medium text-ink">Evidencia y continuidad del análisis</h2>
        <p className="text-sm leading-relaxed text-ink-2">El <Link className="font-medium text-accent" href="/#fuentes">archivo de datos y descargas</Link> conserva fuentes, fechas y denominadores. Las versiones anteriores están disponibles en el pie de página y mantienen su evidencia histórica.</p>
        <p className="text-sm leading-relaxed text-ink-2">Las decisiones detalladas, instrucciones de reproducción, desarrollo y organización del código se conservan en la documentación técnica del <a className="font-medium text-accent" href={REPOSITORIO}>repositorio del proyecto</a>.</p>
      </section>
    </div>
  );
}
