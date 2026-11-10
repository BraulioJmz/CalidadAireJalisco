export type Pol = "PM10" | "PM2.5" | "O3" | "CO" | "NO2" | "SO2" | "NO" | "NOX";
export type Pollutant = { key: Pol; slug: string; label: string; unit: string; statistic: string; categoryApplicable: boolean };
export type Finding = { id: string; title: string; detail: string; figure: string; period: string; population: string; limitation: string; view: number };
export type Metric = { partition: string; model: string; horizon: number; n: number; mae: number | null; rmse: number | null; r2: number | null; r2_reason: string | null; bias: number | null; month?: number; threshold_train_p90?: number };
export type Summary = { schema: string; years: number[]; findings: Finding[]; pollutants: Pollutant[];
  categories: { code: number; name: string; color: string; ink: string }[];
  model: { id: string; n: number; expected: number; coverage: number; rawN: number; threshold: number; features: number; parameters: Record<string, unknown>; freezeSha256: string; metrics: Metric[] };
  sources: { year: number; path: string; sha256: string; url: string | null; origen: string; descargado_en_utc: string | null }[];
  downloads: { name: string; url: string; sha256: string; bytes: number }[]; warnings: string[] };
export type Period = { year: number; month: number; pollutant: Pol; n: number; expected: number; coverage: number; mean: number | null; max: number | null; median: number | null; p95: number | null; sufficient: boolean; quarterly_coverage: number[]; category_applicable: boolean; counts: number[] | null; days_valid: number | null; days_expected: number; days_missing: number | null; bad: number | null; bad_pct: number | null; daily_sufficient: boolean; exploratory: boolean };
export type Profile = { pollutant: Pol; year: number; kind: string; bin: number; n: number; expected: number; mean: number | null; coverage: number };
export type Coverage = { year: number; variable: string; expected_hours: number; numeric_unique_hours: number; usable_basic_hours: number; usable_basic_pct: number; warning: string | null; max_missing_or_excluded_hours: number };
export type Historical = { periods: Period[]; profiles: Profile[]; coverage: Coverage[] };
export type Pair = { year_a: number; year_b: number; month: number; pollutant: Pol; n: number; expected: number; a: number | null; b: number | null; delta: number | null; change_pct: number | null; sufficient: boolean; dates: string[]; quarterly: { quarter: number; expected: number; n: number }[] };
export type Day = { date: string; pollutants: Record<Pol, { value: number | null; exact: number | null; category: number | null; n: number; indN: number }>; weather: Record<string, { mean: number | null; n: number }> };
export type HourChunk = { time: string[]; values: Record<string, (number | null)[]> };
export type Episode = { pollutant: Pol; start: string; end: string; days: number; max_category: number; max_indicator: number; n_hours: number; expected_hours: number };
export type Events = { episodes: Episode[]; peaks: { date: string; value: number; year: number; pollutant: Pol; exploratory: boolean }[]; anomalies: { date: string; value: number; robust_z: number }[] };
export type Relation = { year: number; month: number; pollutant: Pol; variable: string; n: number; expected: number; rho: number | null; status: string; points: { date: string; x: number; y: number }[] };
export type Prediction = { origin: string; target: string[]; observed: number[]; models: Record<string, { predicted: number[]; error: number[] }> };
export type EvaluationPoint = { origin: string; target_time: string; observed: number; predicted: number; signed_error: number };
export type Metrics = { globales: Metric[]; mensuales: Metric[]; altas: Metric[] };
export const MONTHS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
export const pad = (v: number) => String(v).padStart(2, "0");
export const fmt = (v: number | null | undefined, digits = 2) => v == null ? "Sin dato" : v.toLocaleString("es-MX", { maximumFractionDigits: digits, minimumFractionDigits: digits });
export const dateLabel = (v: string) => v.replace("T", " · ").slice(0, 21);
/** Aritmética del calendario codificado, sin aplicar zona del navegador ni DST. */
export function shiftHour(v: string, offset: number) {
  const [date, time = "00:00:00"] = v.split("T"); const [y, m, d] = date.split("-").map(Number); const [h, n] = time.split(":").map(Number);
  return new Date(Date.UTC(y, m - 1, d, h, n) + offset * 3600000).toISOString().slice(0, 19);
}
export function hourGrid(start: string, end: string) { const rows: string[] = []; for (let t = start; t <= end; t = shiftHour(t, 1)) rows.push(t); return rows; }
export function chunkUrls(start: string, end: string) {
  const months = [...new Set(hourGrid(start, end).map(t => t.slice(0, 7)))].filter(m => m >= "2015-01" && m <= "2024-12");
  return months.map(m => `/datos/sprint-3/horas/${m}.json`);
}
export function mergeHours(chunks: HourChunk[] | null, grid: string[], pol: string): (number | null)[] {
  const values = new Map<string, number | null>(); chunks?.forEach(c => c.time.forEach((t, i) => values.set(t, c.values[pol]?.[i] ?? null)));
  return grid.map(t => values.get(t) ?? null);
}
export function validateSummary(value: unknown): asserts value is Summary {
  const d = value as Summary;
  if (d?.schema !== "academia-miravalle-v1" || d.years.length !== 10 || d.categories[0].code !== 0 || d.model.n !== 6225 || d.model.threshold !== 114) throw new Error("Contrato Academia Miravalle inválido");
}
