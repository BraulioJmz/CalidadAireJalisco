import type { Mensaje } from "@/lib/types";

const GRUPOS: [keyof Mensaje, string][] = [
  ["general", "Población en general"],
  ["menores_gestantes", "Menores de 12 años y personas gestantes"],
  ["sensibles", "Personas con enfermedades cardiovasculares o respiratorias y mayores de 60 años"],
];

/** Mensajes de la tabla 12 de la NOM-172-SEMARNAT-2023. Los grupos con el mismo texto se muestran juntos. */
export function MensajesNOM({ m, className = "" }: { m: Mensaje | undefined; className?: string }) {
  if (!m) return null;
  const filas: { grupos: string[]; texto: string }[] = [];
  GRUPOS.forEach(([k, grupo]) => {
    const texto = m[k];
    if (!texto) return;
    const igual = filas.find((f) => f.texto === texto);
    if (igual) igual.grupos.push(grupo);
    else filas.push({ grupos: [grupo], texto });
  });
  return (
    <dl className={`space-y-2 text-sm leading-relaxed text-ink-2 ${className}`}>
      {filas.map((f) => (
        <div key={f.texto}>
          <dt className="font-semibold text-ink">{filas.length === 1 && f.grupos.length === GRUPOS.length ? "Toda la población" : f.grupos.join(" · ")}</dt>
          <dd>{f.texto}</dd>
        </div>
      ))}
    </dl>
  );
}
