import { ACADEMIA } from "@/lib/site";
import { Seal } from "./Seal";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-rule">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 text-sm text-muted sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
        <div className="flex items-start gap-3">
          <Seal size={30} />
          <div className="space-y-1">
            <p className="text-ink-2"><span className="font-medium text-ink">{ACADEMIA.nombre}</span> · {ACADEMIA.unidad}</p>
            <p>Institución ficticia creada para el proyecto de {ACADEMIA.materia}, {ACADEMIA.universidad} · {ACADEMIA.equipo}.</p>
            <p>Datos: SEMADET Jalisco, estación Miravalle (MIR). Criterios: NOM-172-SEMARNAT-2023.</p>
          </div>
        </div>
        <p className="num self-end text-xs">Índice AIRE Y SALUD</p>
      </div>
    </footer>
  );
}
