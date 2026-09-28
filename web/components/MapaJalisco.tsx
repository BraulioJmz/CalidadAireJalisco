import type { Mapa } from "@/lib/data";

/** Barra de escala: el múltiplo "redondo" de km que ocupa cerca de `objetivo` píxeles. */
function Escala({ pxKm, x, y, objetivo = 80 }: { pxKm: number; x: number; y: number; objetivo?: number }) {
  const km = [1, 2, 5, 10, 20, 50, 100].reduce((b, v) => (Math.abs(v * pxKm - objetivo) < Math.abs(b * pxKm - objetivo) ? v : b), 1);
  const w = km * pxKm;
  return (
    <g transform={`translate(${x},${y})`} className="text-ink-2">
      <path d={`M0,0 V5 H${w} V0`} fill="none" stroke="currentColor" strokeWidth="1" />
      <text x={w / 2} y={-4} textAnchor="middle" fontSize="10" fill="currentColor" className="num">{km} km</text>
    </g>
  );
}

function Norte({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x},${y})`} className="text-ink-2" aria-hidden="true">
      <path d="M0,-12 L5,4 L0,0 L-5,4 Z" fill="currentColor" />
      <text y={16} textAnchor="middle" fontSize="10" fill="currentColor">N</text>
    </g>
  );
}

/**
 * Figura de localización: Jalisco con el Área Metropolitana de Guadalajara (izquierda) y
 * acercamiento con las estaciones de SEMADET (derecha). Miravalle se resalta.
 */
export function MapaJalisco({ mapa, clave = "MIR" }: { mapa: Mapa; clave?: string }) {
  const E = mapa.estado, Z = mapa.zona;
  const r = E.recuadro;
  return (
    <div className="grid gap-4 md:grid-cols-[0.8fr_1.2fr]">
      <svg viewBox={`-6 -6 ${E.w + 12} ${E.h + 12}`} role="img" className="h-auto w-full"
        aria-label="Mapa de Jalisco con los municipios del Área Metropolitana de Guadalajara resaltados y la ubicación de la estación Miravalle">
        <title>Jalisco y el Área Metropolitana de Guadalajara</title>
        <text x={0} y={10} fontSize="13" fontWeight="600" fill="var(--ink)">(a)</text>
        {E.municipios.map((m) => (
          <path key={m.nombre} d={m.d} fill={m.amg ? "var(--accent-soft)" : "var(--surface-2)"} stroke="var(--rule)" strokeWidth="0.5" strokeLinejoin="round">
            <title>{m.nombre}</title>
          </path>
        ))}
        <rect x={r.x} y={r.y} width={r.w} height={r.h} fill="none" stroke="var(--ink)" strokeWidth="1" />
        <circle cx={E.mir[0]} cy={E.mir[1]} r="3" fill="var(--ink)" />
        <text x={r.x + r.w + 4} y={r.y + 4} fontSize="11" fill="var(--ink)" dominantBaseline="hanging">AMG</text>
        <text x={E.w * 0.08} y={E.h * 0.95} fontSize="13" fill="var(--ink-2)" className="display" fontStyle="italic">Jalisco</text>
        <Escala pxKm={E.px_km} x={E.w - 100} y={E.h - 10} objetivo={70} />
        <Norte x={E.w - 16} y={22} />
      </svg>

      <svg viewBox={`0 0 ${Z.w} ${Z.h}`} role="img" className="h-auto w-full rounded-lg border border-rule bg-surface"
        aria-label="Acercamiento al Área Metropolitana de Guadalajara con las 13 estaciones de monitoreo de SEMADET; la estación Miravalle está resaltada">
        <title>Estaciones de monitoreo de SEMADET en el Área Metropolitana de Guadalajara</title>
        <text x={12} y={22} fontSize="13" fontWeight="600" fill="var(--ink)">(b)</text>
        <defs><clipPath id="zona-clip"><rect width={Z.w} height={Z.h} /></clipPath></defs>
        <g clipPath="url(#zona-clip)">
          {Z.municipios.map((m) => <path key={m.nombre} d={m.d} fill="var(--surface-2)" stroke="var(--muted)" strokeWidth="0.6" strokeOpacity="0.5" />)}
          {Z.municipios.filter((m) => m.etiqueta).map((m) => (
            <text key={m.nombre} x={m.etiqueta![0]} y={m.etiqueta![1]} fontSize="10.5" textAnchor="middle" fill="var(--muted)" fontStyle="italic">
              {m.nombre.replace("San Pedro ", "")}
            </text>
          ))}
        </g>
        {Z.estaciones.map((e) => {
          const mir = e.clave === clave;
          return (
            <g key={e.clave}>
              <title>{`${e.nombre} (${e.clave}) · ${e.lat.toFixed(4)}, ${e.lon.toFixed(4)}${e.altitud ? ` · ${e.altitud} msnm` : ""}${e.contaminantes ? ` · mide ${e.contaminantes}` : ""}`}</title>
              {mir && <circle cx={e.xy[0]} cy={e.xy[1]} r="11" fill="none" stroke="var(--ink)" strokeWidth="1" />}
              <circle cx={e.xy[0]} cy={e.xy[1]} r={mir ? 5.5 : 3.5} fill={mir ? "var(--ink)" : "var(--surface)"} stroke="var(--ink)" strokeWidth="1.2" />
              <text x={e.xy[0] + (mir ? 15 : 7)} y={e.xy[1] + 3.5} fontSize={mir ? 12 : 10} fontWeight={mir ? 600 : 400} fill="var(--ink)" className="num">
                {mir ? `${e.nombre} (${e.clave})` : e.clave}
              </text>
            </g>
          );
        })}
        <Escala pxKm={Z.px_km} x={16} y={Z.h - 14} />
        <Norte x={Z.w - 20} y={26} />
      </svg>
    </div>
  );
}
