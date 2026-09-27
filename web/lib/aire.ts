export const CATS = ["Buena", "Aceptable", "Mala", "Muy Mala", "Extremadamente Mala"] as const;
export const ORD: Record<string, number> = { Buena: 0, Aceptable: 1, Mala: 2, "Muy Mala": 3, "Extremadamente Mala": 4 };
const KEY: Record<string, string> = {
  Buena: "buena", Aceptable: "aceptable", Mala: "mala", "Muy Mala": "muymala", "Extremadamente Mala": "extrema", "Sin datos": "sin",
};
export const catVar = (c: string) => `var(--c-${KEY[c] ?? "sin"})`;
export const onVar = (c: string) => `var(--on-${KEY[c] ?? "sin"})`;
export const catKey = (c: string) => KEY[c] ?? "sin";

/** Etiquetas con subíndices Unicode (para texto plano y gráficas). */
export const PL: Record<string, string> = { PM10: "PM₁₀", "PM2.5": "PM₂.₅", O3: "O₃", CO: "CO", NO2: "NO₂", SO2: "SO₂", "": "—" };
export const MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
export const MES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
export const DOW = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

export const dec = (p: string) => (p === "O3" ? 3 : p === "CO" ? 2 : 0);

export function fmt(v: unknown, d = 0): string {
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "—";
  return Number(v).toLocaleString("es-MX", { minimumFractionDigits: d, maximumFractionDigits: d });
}

export function num(v: unknown): number | null {
  return v === null || v === undefined || v === "" ? null : Number(v);
}

export function parseT(t: string) {
  const [a, b = "00:00"] = t.split(" ");
  const [y, m, d] = a.split("-").map(Number);
  const [h] = b.split(":").map(Number);
  return { y, m, d, h };
}

export function tLabel(t: string) {
  const p = parseT(t);
  return `${p.d} ${MES[p.m - 1]} ${String(p.h).padStart(2, "0")}:00`;
}

export function dow(t: string) {
  const p = parseT(t);
  return DOW[new Date(p.y, p.m - 1, p.d).getDay()];
}

export const pct = (a: number, b: number) => (b ? Math.round((100 * a) / b) : 0);
