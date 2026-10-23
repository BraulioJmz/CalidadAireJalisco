/** Solo fechas y controles de recorrido. Los indicadores/categorías provienen del CSV. */
export function monthLength(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}
export function monthStart(year: number, month: number): number {
  return (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7;
}
export function timelineLength(years: number[], month: number): number {
  return Math.max(...years.map(y => monthLength(y, month)));
}
export function isoDate(year: number, month: number, day: number): string | null {
  if (day < 1 || day > monthLength(year, month)) return null;
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
export type TimelineState = { day: number; playing: boolean };
export type TimelineAction = { type: "play" | "pause" | "tick" } | { type: "step"; offset: number } | { type: "select"; day: number } | { type: "restart"; autoplay: boolean };
export function timelineReducer(state: TimelineState, action: TimelineAction, last: number): TimelineState {
  if (action.type === "restart") return { day: 1, playing: action.autoplay };
  if (action.type === "pause") return { ...state, playing: false };
  if (action.type === "play") return { ...state, playing: state.day < last };
  if (action.type === "tick" && !state.playing) return state;
  const day = Math.max(1, Math.min(last, action.type === "select" ? action.day : state.day + (action.type === "step" ? action.offset : 1)));
  return { day, playing: action.type === "tick" && day < last };
}
