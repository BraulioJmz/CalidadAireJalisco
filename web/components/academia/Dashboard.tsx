"use client";
import { useState } from "react";
import Link from "next/link";
import type { Pol, Summary } from "@/lib/academia";
import { Historical, Comparison, CoverageView } from "./Historical";
import { Calendar } from "./Calendar";
import { Evaluation, ModelScope, PredictionView } from "./Model";
import { Motion, Select, Sections } from "./Shared";
import { useAcademiaNavigation } from "./Navigation";
import { Panorama } from "./Panorama";
import { Sources } from "./Sources";
import "@/components/sprint2/sprint2.css";
import "./academia.css";

export function Dashboard({ data }: { data: Summary }) {
  const { selection, active, navigate } = useAcademiaNavigation();
  const [pol, setPol] = useState<Pol>("PM10"), [historicalYear, setHistoricalYear] = useState(0), [episodeYear, setEpisodeYear] = useState(2024);
  const pollutant = data.pollutants.find(p => p.key === pol)!;
  const sourceView = ["fuentes", "metodo"].includes(selection);
  const historySection = selection.endsWith("/comparar") ? 1 : selection.endsWith("/cobertura") ? 2 : 0;
  const evaluation = selection.endsWith("/evaluacion");
  const go = (key: string, pollutantKey?: string, year?: number) => {
    if (pollutantKey) setPol(pollutantKey as Pol);
    setHistoricalYear(year ?? 0); setEpisodeYear(year ?? 2024); navigate(key);
  };
  return <div className="am s2 mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
    {active !== 0 && <header className="am-page-heading"><p className="eyebrow">Estación Miravalle · {active === 3 ? "evaluación retrospectiva de 2024" : "histórico 2015–2024"}</p><h1 className="display">{sourceView ? "Fuentes y descargas." : active === 1 ? "Concentraciones y cobertura." : active === 2 ? "Episodios y fechas críticas." : "Predecir PM₁₀, contrastar el resultado."}</h1></header>}
    {active === 1 && <Sections labels={["Series y categorías", "Comparar periodos", "Cobertura"]} active={historySection} change={i => navigate(["historico", "historico/comparar", "historico/cobertura"][i])} label="Explorar el histórico" />}
    {active === 3 && <><ModelScope summary={data} /><Sections labels={["Explorar un origen", "Métricas y errores"]} active={evaluation ? 1 : 0} change={i => navigate(i ? "prediccion/evaluacion" : "prediccion")} label="Explorar la predicción" /></>}
    {(active === 2 || (active === 1 && historySection !== 2)) && <div className="am-view-heading"><Select label="Contaminante" value={pol} change={v => setPol(v as Pol)}>{data.pollutants.map(p => <option key={p.key} value={p.key}>{p.label} · {p.unit}</option>)}</Select><span className="am-context-label">{active === 2 ? "Selección aplicada al calendario y su contexto horario" : historySection === 1 ? "Selección aplicada a los dos periodos comparados" : "Selección aplicada a series, perfiles y categorías"}</span></div>}
    {active === 1 && ["NO2", "SO2", "NO", "NOX"].includes(pol) && <p className="am-callout" role="note">{pol === "SO2" ? "SO₂ 2023 excluido por falta de calibración documentada; 2024 está ausente." : `${pol === "NO2" ? "NO₂" : pollutant.label} de 2024 no está declarado en el catálogo MIR del libro. Procedencia y calibración no acreditadas: datos exploratorios. ${pol === "NO2" ? "" : "Esta variable no tiene categoría normativa en este análisis."}`}</p>}
    <Motion signal={`${selection}|${pol}`} className="am-content" id="am-content" aria-label={sourceView ? "Fuentes" : ["Panorama", "Histórico", "Episodios", "Predicción"][active] ?? "Panorama"} role="region" tabIndex={-1}>
      {sourceView ? <Sources data={data} /> : active === 1 ? <>
        {historySection === 0 && <Historical summary={data} pol={pollutant} initialYear={historicalYear} />}
        {historySection === 1 && <Comparison summary={data} pol={pollutant} />}
        {historySection === 2 && <CoverageView summary={data} />}
      </> : active === 2 ? <Calendar summary={data} pol={pollutant} initialYear={episodeYear} /> : active === 3 ? (evaluation ? <Evaluation summary={data} /> : <PredictionView summary={data} />) : <Panorama data={data} go={go} />}
    </Motion>
    {!sourceView && <p className="am-method-link"><Link href="/metodologia">Cómo se obtuvieron estos resultados</Link><span aria-hidden="true"> · </span><Link href="/#fuentes">Fuentes y descargas</Link></p>}
  </div>;
}
