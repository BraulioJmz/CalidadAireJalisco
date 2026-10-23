/** Contrato de presentación. La normativa y los resultados se calculan en Python. */
export type PolS2 = "PM10" | "PM2.5" | "O3" | "CO";
export type DailyReadingS2 = { indicator: number | null; exact: number | null; category: number | null; readings: number; indicators: number };
export type DailyS2 = {
  date: string; year: number; month: number; day: number; expected: number;
  pollutants: Record<PolS2, DailyReadingS2>;
  weather: Record<"ET" | "RH" | "WS", { value: number | null; readings: number }>;
};
export type ContextPoint = { t: string; raw: number | null; indicator: number | null };
export type PeriodS2 = { year: number; month: number; pollutant: string; counts: number[]; valid: number; missing: number; expected: number; bad: number; badPct: number | null; mean: number | null; median: number | null; sufficient: boolean };
export type ComparisonS2 = { pollutant: string; month: number; n: number; expected: number; coverage: number; comparable: boolean; a: number | null; b: number | null; delta: number | null; change_pct: number | null; quarterly_coverage: number[]; dates: string[] };
export type ProfileS2 = { year: number; month: number; hour: number; pollutant: string; valid: number; expected: number; missing: number; bad: number; bad_pct: number | null; counts: number[] };
export type CoverageS2 = { year: number; month: number; variable: string; expected: number; usable: number; pct: number; source_rows: number; absent_rows: number; excluded: number; missing_measurements: number };
export type MeteoS2 = { year: number; month: number; pollutant: string; variable: string; n: number; expected: number; coverage_pct: number; rho: number | null; status: string; points: [string, number, number][] };
export type EventS2 = { id: string; kind: string; pollutant: string; date: string; year: number; month: number; value: number; raw: number | null; category: number; n: number | null; selection: string; context: ContextPoint[] };
export type EpisodeS2 = { id: string; pollutant: string; start: string; end: string; days: number; max_category: number; max_indicator: number; n_raw_hours: number; expected_hours: number; selection: string; crossYear: boolean; context: ContextPoint[] };
export type Sprint2Data = {
  schema: "mir-s2-v2"; station: string; agency: string; reference: number; source: string;
  daily: DailyS2[]; dailyStatistics: Record<PolS2, { label: string; unit: string }>;
  months: string[]; categories: { name: string; color: string }[];
  pollutants: { key: string; label: string; unit: string; daily: string; hourly: string }[];
  periods: PeriodS2[]; comparisons: ComparisonS2[]; profiles: ProfileS2[]; coverage: CoverageS2[];
  determinants: { year: number; month: number; scope: string; days: number; counts: Record<string, number> }[];
  meteorology: MeteoS2[]; events: EventS2[]; episodes: EpisodeS2[];
  quality: { raw_hours: Record<string, number>; missing_source_rows: number; flags: number };
  rules: Record<string, string>; processedHashes: Record<string, string>;
  downloads: { name: string; url: string }[];
  figures: { id: string; question: string; svg: string; png: string }[];
};

function object(v: unknown): Record<string, unknown> {
  if (!v || typeof v !== "object" || Array.isArray(v)) throw new Error("Objeto esperado en contrato Sprint 2");
  return v as Record<string, unknown>;
}
function array(v: unknown, n?: number): unknown[] {
  if (!Array.isArray(v) || (n !== undefined && v.length !== n)) throw new Error("Dimensión inválida en contrato Sprint 2");
  return v;
}
function number(v: unknown): number {
  if (typeof v !== "number" || !Number.isFinite(v)) throw new Error("Número inválido en contrato Sprint 2");
  return v;
}
export function assertSprint2(value: unknown): asserts value is Sprint2Data {
  const d = object(value);
  if (d.schema !== "mir-s2-v2" || d.reference !== 2024) throw new Error("Versión de datos Sprint 2 incompatible");
  array(d.months, 12); array(d.categories, 5);
  const units = new Map([["PM10", "µg/m³"], ["PM2.5", "µg/m³"], ["O3", "ppm"], ["CO", "ppm"], ["NO2", "ppm"]]);
  for (const v of array(d.pollutants, 5)) {
    const p = object(v); if (units.get(String(p.key)) !== p.unit) throw new Error("Unidad inesperada en Sprint 2");
  }
  const keys = new Set<string>();
  for (const v of array(d.periods, 182)) {
    const r = object(v); const counts = array(r.counts, 5).map(number);
    const valid = number(r.valid), expected = number(r.expected), missing = number(r.missing);
    const key = `${r.year}-${r.month}-${r.pollutant}`;
    if (keys.has(key) || counts.some(n => n < 0 || !Number.isInteger(n)) || counts.reduce((a, b) => a + b, 0) !== valid || valid + missing !== expected) throw new Error("Denominador diario inconsistente");
    keys.add(key);
    if (counts.slice(2).reduce((a, b) => a + b, 0) !== r.bad) throw new Error("Numerador incorrecto");
    if (valid === 0 && (r.mean !== null || r.badPct !== null)) throw new Error("Ausencia sustituida por cero");
    if (r.mean !== null) number(r.mean);
    if (valid && Math.abs(number(r.badPct) - 100 * number(r.bad) / valid) > 1e-10) throw new Error("Proporción inconsistente");
  }
  for (const v of array(d.comparisons, 65)) {
    const r = object(v); if (number(r.n) > number(r.expected) || r.a === 0 && r.change_pct !== null) throw new Error("Comparación inválida");
  }
  array(d.coverage, 390); array(d.profiles, 2304);
  for (const v of array(d.meteorology, 360)) {
    const r = object(v); array(r.points, number(r.n));
    if (number(r.n) < 15 && r.rho !== null) throw new Error("Meteorología sin suficiencia");
  }
  for (const v of array(d.downloads)) if (!String(object(v).url).startsWith("/descargas/sprint-2/")) throw new Error("Descarga ajena a evidencia web");
  const statistics = object(d.dailyStatistics);
  const labels = { PM10: "Promedio diario de 24 h", "PM2.5": "Promedio diario de 24 h", O3: "Máximo horario diario", CO: "Máximo diario del promedio móvil de 8 h" };
  for (const [p, label] of Object.entries(labels)) {
    const s = object(statistics[p]);
    if (s.label !== label || s.unit !== units.get(p)) throw new Error("Estadístico/unidad diaria incorrecta");
  }
  const count = (v: unknown) => { const n = number(v); if (!Number.isInteger(n) || n < 0 || n > 24) throw new Error("Conteo diario incorrecto"); return n; };
  const daily = array(d.daily, 731).map(object);
  daily.forEach((r, i) => {
    const date = new Date(Date.UTC(2023, 0, 1 + i));
    if (r.date !== date.toISOString().slice(0, 10) || r.year !== date.getUTCFullYear() || r.month !== date.getUTCMonth() + 1 || r.day !== date.getUTCDate() || r.expected !== 24) throw new Error("Fecha diaria inexistente o fuera de orden");
    const pollutants = object(r.pollutants), weather = object(r.weather);
    if (Object.keys(pollutants).sort().join() !== ["PM10", "PM2.5", "O3", "CO"].sort().join() || Object.keys(weather).sort().join() !== "ET,RH,WS") throw new Error("Dimensión diaria incorrecta");
    for (const v of Object.values(pollutants)) {
      const p = object(v); count(p.readings); count(p.indicators);
      if (p.category !== null && (!Number.isInteger(number(p.category)) || number(p.category) < 0 || number(p.category) > 4)) throw new Error("Categoría diaria incorrecta");
      if ((p.category === null) !== (p.indicator === null) || (p.category === null) !== (p.exact === null)) throw new Error("Ausencia diaria incoherente");
      for (const k of ["indicator", "exact"]) if (p[k] !== null && number(p[k]) < 0) throw new Error("Indicador diario negativo");
    }
    for (const v of Object.values(weather)) {
      const w = object(v); const n = count(w.readings);
      if (w.value !== null) { number(w.value); if (n < 18) throw new Error("Meteorología diaria insuficiente"); }
    }
  });
  for (const v of array(d.periods)) {
    const p = object(v); if (!Object.hasOwn(labels, String(p.pollutant))) continue;
    const rows = daily.filter(r => r.year === p.year && (!p.month || r.month === p.month));
    const categories = rows.map(r => object(object(r.pollutants)[String(p.pollutant)]).category);
    if (categories.filter(c => c === null).length !== p.missing || array(p.counts).some((n, c) => categories.filter(v => v === c).length !== n)) throw new Error("Calendario no reconcilia con el periodo");
  }
}
