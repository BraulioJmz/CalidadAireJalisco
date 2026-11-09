"use client";
import type { Historical as History, Summary } from "@/lib/academia";
import { fmt } from "@/lib/academia";
import { useEntrance } from "@/components/sprint2/Motion";
import { Loading, useData } from "./Shared";

export function Panorama({ data, go }: { data: Summary; go: (key: string, pol?: string, year?: number) => void }) {
  const history = useData<History>("/datos/sprint-3/historico/PM10.json");
  const periods = [2023, 2024].map(year => history.data?.periods.find(r => r.year === year && r.month === 12));
  const ref = useEntrance<HTMLDivElement>(JSON.stringify(periods), "reveal");
  const finding = (id: string) => data.findings.find(f => f.id === id)!;
  const secondary = [
    { id: "H01", title: "En 2016 solo se observó el 23.9 % de las horas de PM₁₀", key: "historico/cobertura", year: 2016 },
    { id: "H03", title: "El perfil observado de PM₁₀ alcanza su máximo a las 08:00", key: "historico", year: 0 },
    { id: "H06", title: "Una secuencia de 52 días desfavorables cruzó de 2021 a 2022", key: "episodios", year: 2021 },
  ];
  return <>
    <div className="am-front-masthead"><p className="eyebrow">Estación Miravalle · MIR · SEMADET Jalisco</p><h1 className="display">Diez años de aire<br /><em>en Miravalle.</em></h1><p>Histórico 2015–2024. Concentraciones, cobertura y episodios de una misma estación de monitoreo.</p></div>
    <article className="am-lead" data-finding-id="H04">
      <div className="am-lead-story"><p className="eyebrow">La comparación · diciembre 2023–2024</p><h2 className="display">De 15 a 27 días con PM₁₀ Mala o peor en diciembre.</h2><p>{finding("H04").detail.split(". ").slice(1).join(". ")}</p><p className="am-note">{finding("H04").limitation}</p><button type="button" className="am-text-link" onClick={() => go("historico/comparar", "PM10")}>Comparar los dos periodos <span aria-hidden="true">↗</span></button></div>
      <figure className="am-lead-figure"><figcaption>¿Cómo se repartieron los 31 días de cada diciembre?</figcaption>
        {!history.data ? <Loading error={history.error} /> : <div ref={ref} className="am-lead-bars">{periods.map((r) => r && <div className="am-lead-row" key={r.year}><div><b>{r.year}</b><span>{r.bad} / {r.days_expected} días Mala o peor</span></div><div className="am-category-bar" role="img" aria-label={`Diciembre ${r.year}: ${r.bad} de ${r.days_expected} días Mala o peor`}>{r.counts?.map((n, c) => n > 0 && <span key={c} style={{ width: `${100 * n / r.days_expected}%`, background: data.categories[c].color }} title={`${data.categories[c].name}: ${n}/${r.days_expected}`} />)}</div><p className="am-note">{r.days_valid} días con indicador · {r.days_missing} sin indicador</p></div>)}</div>}
        <ul className="am-category-legend">{data.categories.map(c => <li key={c.code}><i style={{background:c.color}} />{c.name}</li>)}</ul><p className="am-note">Promedio diario de partículas. Bandas retrospectivas de 2024; no reconstruye los avisos oficiales de cada año.</p>
      </figure>
    </article>
    <div className="am-secondary">{secondary.map(item => <article key={item.id} data-finding-id={item.id}><p className="eyebrow">{finding(item.id).period}</p><h2 className="display">{item.title}</h2><p>{finding(item.id).detail}</p><details><summary>Alcance de esta lectura</summary><p>{finding(item.id).limitation}</p></details><button type="button" className="am-text-link" onClick={() => go(item.key, "PM10", item.year)}>Explorar la evidencia ↗</button></article>)}</div>
    <aside className="am-prediction-entry"><div><p className="eyebrow">PM₁₀ · evaluación retrospectiva de 2024</p><h2 className="display">Una hora de origen.<br />Tres horizontes para contrastar.</h2><p>Explora lo que se predijo a +1, +2 y +3 horas y compáralo con las concentraciones observadas.</p><button type="button" onClick={() => go("prediccion")}>Explorar predicciones ↗</button><button type="button" onClick={() => go("prediccion/evaluacion")}>Revisar métricas y errores →</button></div><div className="am-entry-number"><b>{fmt(data.model.metrics.find(r => r.model === "HGB" && r.horizon === 1)?.mae)}</b><span>µg/m³ · MAE a +1 h</span><p>{data.model.n.toLocaleString("es-MX")} orígenes evaluados · {fmt(data.model.coverage, 1)} % de las horas del año. El modelo subestima concentraciones altas.</p></div></aside>
  </>;
}
