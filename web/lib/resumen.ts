import { CATS } from "./aire";
import type { DayRec, Numeralia, PeriodoData } from "./types";

/**
 * Resumen compacto de un periodo para el Observatorio.
 * Solo reorganiza y cuenta lo que ya trae el JSON del pipeline; no recalcula nada de la NOM.
 */

/** Categorías con "Sin datos" al final; las horas se guardan como índice de esta lista. */
export const CATS_ALL = [...CATS, "Sin datos"] as const;
const SIN = CATS_ALL.length - 1;

/** `horas`: 24 dígitos, uno por hora, con el índice de la categoría en CATS_ALL (compacto para el cliente). */
export type ResumenDia = DayRec & { horas: string; peor_horaria: string; horas_peores: number };

export type ResumenPeriodo = {
  clave: string;
  nombre: string;
  mes: number;
  sprint: { slug: string; numero: number } | null;
  descargas: { nombre: string; href: string }[];
  numeralia: Numeralia;
  categorias_por_hora: Record<string, number[]>;
  /** Horas en que cada contaminante fue responsable, por hora del día (0–23). */
  responsable_por_hora: Record<string, number[]>;
  dias: ResumenDia[];
  perfil_diurno: Record<string, (number | null)[]>;
  bandas: Record<string, number[]>;
  unidades: Record<string, string>;
  mensajes: Record<string, { general: string; sensibles: string }>;
  riesgo: Record<string, string>;
  disponibilidad: { variable: string; nombre: string; unidad: string; disponibilidad: number }[];
  ausentes: string[];
  limitaciones: string[];
};

const DIURNO = ["PM10_NowCast", "PM2.5_NowCast", "O3", "ET", "WS"];

export function construirResumen(
  D: PeriodoData,
  sprint: ResumenPeriodo["sprint"],
  descargas: ResumenPeriodo["descargas"],
): ResumenPeriodo {
  const idx = (c: string) => { const i = CATS_ALL.indexOf(c as (typeof CATS_ALL)[number]); return i < 0 ? SIN : i; };
  const resp: Record<string, number[]> = {};
  D.horario.forEach((h) => {
    const r = h.Responsable;
    if (!r || h.Cat_global === "Sin datos") return;
    (resp[r] ??= Array(24).fill(0))[Number(h.t.slice(11, 13))]++;
  });
  const dias: ResumenDia[] = D.diario.map((d) => {
    const hs = D.horario.filter((h) => h.t.startsWith(d.FECHA));
    const horas = Array.from({ length: 24 }, (_, i) => idx(hs.find((h) => Number(h.t.slice(11, 13)) === i)?.Cat_global ?? "Sin datos")).join("");
    const ind = `${d.Responsable}_indicador`;
    return {
      FECHA: d.FECHA, dia_semana: d.dia_semana, Cat_global: d.Cat_global, Responsable: d.Responsable,
      evento: d.evento, evento_sigla: d.evento_sigla, [ind]: d[ind] ?? null,
      horas, peor_horaria: String(d.peor_horaria ?? "Sin datos"), horas_peores: Number(d.horas_peores_que_diaria ?? 0),
    };
  });
  const medidas = [...D.estacion.contaminantes, ...D.estacion.meteorologia];
  const vars = D.perfil.variables.filter((v) => medidas.includes(v.variable));
  return {
    clave: D.periodo.clave,
    nombre: D.periodo.nombre,
    mes: Number(D.periodo.inicio.slice(5, 7)),
    sprint,
    descargas,
    numeralia: D.numeralia,
    categorias_por_hora: D.categorias_por_hora,
    responsable_por_hora: resp,
    dias,
    perfil_diurno: Object.fromEntries(DIURNO.filter((k) => D.perfil_diurno[k]).map((k) => [k, D.perfil_diurno[k]])),
    bandas: D.bandas,
    unidades: D.unidades,
    mensajes: D.mensajes,
    riesgo: D.riesgo,
    disponibilidad: vars.map((v) => ({ variable: v.variable, nombre: v.nombre, unidad: v.unidad, disponibilidad: v.disponibilidad })),
    ausentes: vars.filter((v) => !v.validos).map((v) => v.nombre),
    limitaciones: D.bitacora.filter((b) => b.clasificacion === "Limitación").map((b) => `${b.variable}: ${b.detalle}`),
  };
}

/* ---------- utilidades para los textos del tablero (cliente y servidor) ---------- */

/** Categoría de cada hora de un día resumido. */
export const catsDelDia = (d: ResumenDia) => [...d.horas].map((c) => CATS_ALL[Number(c)]);

export const hh = (h: number) => String(h).padStart(2, "0");

/** Agrupa horas en tramos continuos: [6,7,8,15] → [[6,8],[15,15]]. */
export function tramos(hs: number[]): [number, number][] {
  const out: [number, number][] = [];
  hs.forEach((h) => { const t = out[out.length - 1]; if (t && h === t[1] + 1) t[1] = h; else out.push([h, h]); });
  return out;
}

export const fmtTramo = ([a, b]: [number, number]) => `${hh(a)}:00–${hh(b)}:59`;
/** Como `tramos`, pero une el tramo que termina a las 23 con el que empieza a las 0 (el día es circular). */
export function tramosCirculares(hs: number[]): [number, number][] {
  const t = tramos(hs);
  if (t.length > 1 && t[0][0] === 0 && t[t.length - 1][1] === 23) return [[t[t.length - 1][0], t[0][1]], ...t.slice(1, -1)];
  return t;
}

export const fmtTramos = (hs: number[]) => (hs.length ? tramosCirculares(hs).map(fmtTramo).join(" y ") : "—");

export type Franja = "buena" | "precaucion" | "critica";

/** Criterio de la academia para planear: ≥ 80 % de días en Buena → buena; ≥ 50 % en Mala o peor → crítica. */
export function franjasDelDia(C: Record<string, number[]>) {
  const horas = Array.from({ length: 24 }, (_, h) => {
    const n = CATS.map((c) => C[c]?.[h] ?? 0);
    const tot = n.reduce((a, b) => a + b, 0);
    const buena = n[0], malas = n[2] + n[3] + n[4];
    const moda = CATS[n.indexOf(Math.max(...n))];
    const franja: Franja = !tot ? "precaucion" : buena / tot >= 0.8 ? "buena" : malas / tot >= 0.5 ? "critica" : "precaucion";
    return { h, tot, buena, malas, moda: tot ? moda : "Sin datos", franja };
  });
  const de = (f: Franja) => horas.filter((x) => x.franja === f).map((x) => x.h);
  return { horas, buena: de("buena"), precaucion: de("precaucion"), critica: de("critica") };
}

/** Categoría más frecuente dentro de un conjunto de horas del día. */
export function modaEn(C: Record<string, number[]>, hs: number[]) {
  const n = CATS.map((c) => hs.reduce((s, h) => s + (C[c]?.[h] ?? 0), 0));
  return n.some(Boolean) ? CATS[n.indexOf(Math.max(...n))] : "Sin datos";
}

/** Contaminante responsable más frecuente dentro de un conjunto de horas del día. */
export function responsableEn(R: Record<string, number[]>, hs: number[]) {
  const n = Object.entries(R).map(([p, v]) => [p, hs.reduce((s, h) => s + (v[h] ?? 0), 0)] as const).sort((a, b) => b[1] - a[1]);
  return n[0] && n[0][1] ? n[0][0] : "";
}


