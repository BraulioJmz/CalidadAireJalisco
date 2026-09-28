import fs from "node:fs";
import path from "node:path";
import type { IndicePeriodo, PeriodoData } from "./types";

const DIR = path.join(process.cwd(), "data", "periodos");

export function getPeriodo(periodo: string): PeriodoData {
  return JSON.parse(fs.readFileSync(path.join(DIR, `${periodo}.json`), "utf8"));
}

export function getIndice(): IndicePeriodo[] {
  return JSON.parse(fs.readFileSync(path.join(DIR, "index.json"), "utf8"));
}

export function getUltimoPeriodo(): PeriodoData {
  const idx = getIndice();
  return getPeriodo(idx[idx.length - 1].periodo);
}

export type Descarga = { nombre: string; href: string; titulo: string; descripcion: string; paso: number };

/** Qué es cada archivo descargable y en qué paso del pipeline se genera (orden = orden del flujo). */
const DESCARGAS: { patron: RegExp; titulo: string; descripcion: string; paso: number }[] = [
  { patron: /^miravalle_.*_clean\.csv$/, paso: 1, titulo: "Datos limpios del periodo",
    descripcion: "Salida del ETL: todas las variables de MIR con tipos corregidos, sin imputar, más las 24 h de calentamiento (CALENTAMIENTO = True)." },
  { patron: /^bitacora_limpieza\.csv$/, paso: 2, titulo: "Bitácora de control de calidad",
    descripcion: "Cada valor marcado, la regla que lo detectó, su clasificación (error, evento real, revisar) y la decisión. No se eliminó ninguno." },
  { patron: /^Archivo1_Calculos_Horarios\.csv$/, paso: 3, titulo: "Archivo 1 · cálculos horarios",
    descripcion: "Tabla procesada NOM-172 por hora: NowCast de PM₁₀ y PM₂.₅, CO 8 h, O₃, categorías, categoría global y contaminante responsable." },
  { patron: /^Archivo2_Calculos_Diarios\.csv$/, paso: 4, titulo: "Archivo 2 · cálculos diarios",
    descripcion: "Tabla procesada NOM-172 por día: datos válidos, suficiencia, indicador diario y categoría de cada contaminante, categoría global y responsable." },
  { patron: /^reporte_resultados_.*\.txt$/, paso: 4.5, titulo: "Reporte de resultados en texto",
    descripcion: "Numeralia lista para copiar al reporte: suficiencia, estadísticos de los indicadores, categorías por contaminante y globales, responsables, días más desfavorables y comparación horaria contra diaria." },
  { patron: /_horario\.xlsx$/, paso: 5, titulo: "Excel horario",
    descripcion: "Archivo 1 con meteorología, banderas de calidad y mensajes, más las hojas de perfil de variables, bitácora y metodología." },
  { patron: /_diario\.xlsx$/, paso: 6, titulo: "Excel diario",
    descripcion: "Archivo 2 con la lectura horaria de cada día, meteorología resumida y metodología." },
];

/** Archivos descargables del periodo en public/descargas/AAAA-MM (si existen), documentados y en orden del flujo. */
export function getDescargas(periodo: string): Descarga[] {
  const dir = path.join(process.cwd(), "public", "descargas", periodo);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).map((f) => {
    const info = DESCARGAS.find((x) => x.patron.test(f));
    return { nombre: f, href: `/descargas/${periodo}/${f}`, titulo: info?.titulo ?? f, descripcion: info?.descripcion ?? "", paso: info?.paso ?? 99 };
  }).sort((a, b) => a.paso - b.paso);
}

export type Mapa = {
  fuente: string;
  estado: { w: number; h: number; px_km: number; municipios: { nombre: string; amg: boolean; d: string }[];
    recuadro: { x: number; y: number; w: number; h: number }; mir: [number, number] };
  zona: { w: number; h: number; px_km: number; municipios: { nombre: string; d: string; etiqueta: [number, number] | null }[];
    estaciones: { clave: string; nombre: string; xy: [number, number]; lat: number; lon: number; altitud: number | null; contaminantes: string; anio: number | null }[] };
};

/** Mapa de referencia de Jalisco y estaciones SEMADET (lo genera pipeline/mapa.py). */
export function getMapa(): Mapa | null {
  const f = path.join(process.cwd(), "data", "mapa_jalisco.json");
  return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : null;
}
