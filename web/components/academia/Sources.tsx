import type { Summary } from "@/lib/academia";
import { fmt } from "@/lib/academia";
import { REPOSITORIO } from "@/lib/site";
import { Panel } from "./Shared";
export function Sources({ data }: { data: Summary }) {
  return <div className="am-sources" id="fuentes">
        <Panel title="Fuentes y recursos reproducibles" question="¿De dónde procede cada versión y cómo contrastar los resultados?">
          <p><a className="am-text-link" href={REPOSITORIO} target="_blank" rel="noreferrer">Repositorio de CalidadAireJalisco ↗</a> · Los originales de 2023 y 2024 se reutilizaron sin sustituirlos; la procedencia de 2024 sigue siendo un archivo suministrado.</p>
          <details><summary>Procedencia y hashes de los diez libros originales</summary><ul className="am-source-list">{data.sources.map(s => <li key={s.year}><b>{s.year} · BD_{s.year}.xlsx</b><p>{s.origen} · {s.descargado_en_utc ? `Descarga ${s.descargado_en_utc.slice(0, 10)} (UTC)` : "Fecha de descarga original no acreditada"}</p>{s.url && <a href={s.url} target="_blank" rel="noreferrer">Fuente declarada ↗</a>}<code>{s.sha256}</code></li>)}</ul></details>
          <div className="am-downloads">{data.downloads.map(d => <a key={d.name} href={d.url} download><span>{d.name}</span><small>{fmt(d.bytes / 1024, 0)} KB · descargar</small></a>)}</div>
          <p className="am-note">Los CSV conservan resultados completos para contraste y cálculos. Las consultas visuales cargan agregados o detalles mensuales, no toda la década horaria al abrir. La evaluación y la configuración del modelo permanecen congeladas.</p>
        </Panel>  </div>;
}
