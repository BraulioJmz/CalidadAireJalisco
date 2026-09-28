"use client";
import { useMemo } from "react";
import { CATS, dec, fmt } from "@/lib/aire";
import type { ResumenPeriodo } from "@/lib/resumen";
import { EChart } from "../charts/EChart";
import { useTokens, withAlpha, type Tokens } from "../charts/useTokens";

const axis = (T: Tokens) => ({
  axisLabel: { color: T.muted, fontFamily: T.fontMono, fontSize: 10 }, axisLine: { lineStyle: { color: T.rule } },
  splitLine: { lineStyle: { color: T.rule, opacity: 0.7 } }, axisTick: { show: false },
});
const tip = (T: Tokens) => ({ backgroundColor: T.surface, borderColor: T.rule, textStyle: { color: T.ink, fontSize: 12 }, confine: true });

/** Serie del perfil diurno → contaminante cuyas bandas le corresponden (solo si el indicador horario es ese valor). */
const BANDA: Record<string, string> = { PM10_NowCast: "PM10", "PM2.5_NowCast": "PM2.5", O3: "O3" };

/** Promedio por hora del día de una variable, con las bandas NOM de fondo cuando aplica. Un eje por gráfica. */
export function DiurnalChart({ serie, valores, bandas, unidad, nombre }: {
  serie: string; valores: (number | null)[]; bandas: Record<string, number[]>; unidad: string; nombre: string;
}) {
  const T = useTokens();
  const option = useMemo(() => {
    if (!T) return null;
    const pol = BANDA[serie];
    const d = pol ? dec(pol) : serie === "WS" ? 2 : 1;
    const max = Math.max(...valores.map((v) => v ?? 0)) || 1;
    const lims = pol ? bandas[pol] : [];
    // bandas NOM de fondo; el eje se ajusta a los datos y recorta lo que sobra. Solo se rotula una banda si se ve completa.
    const areas = lims.map((hi, i) => ({ lo: i ? lims[i - 1] : 0, hi, c: CATS[i] })).concat(lims.length ? [{ lo: lims[lims.length - 1], hi: lims[lims.length - 1] * 10, c: CATS[4] }] : [])
      .filter((b) => b.lo < max * 1.1)
      .map((b) => [{ yAxis: b.lo, itemStyle: { color: withAlpha(T.cat[b.c], T.bandAlpha) }, label: { show: b.hi <= max * 1.05 || b.lo < max * 0.7, position: "insideBottomLeft", formatter: b.c, color: T.muted, fontSize: 10, fontFamily: T.fontSans } }, { yAxis: b.hi }]);
    const ejeDec = pol === "O3" ? 2 : serie === "WS" ? 1 : 0;
    return {
      animation: false, textStyle: { fontFamily: T.fontSans }, grid: { left: 42, right: 10, top: 10, bottom: 24 },
      tooltip: { ...tip(T), trigger: "axis", axisPointer: { type: "line", lineStyle: { color: T.muted } },
        formatter: (ps: { name: string; value: number | null }[]) => `<b>${ps[0].name}:00</b><br>${nombre}: <b>${fmt(ps[0].value, d)}</b> ${unidad}` },
      xAxis: { type: "category", boundaryGap: false, data: Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0")), ...axis(T), axisLabel: { ...axis(T).axisLabel, interval: 5 } },
      yAxis: { type: "value", min: 0, ...axis(T), axisLabel: { ...axis(T).axisLabel, formatter: (v: number) => fmt(v, ejeDec) } },
      series: [{
        type: "line", data: valores, clip: true, symbol: "none", connectNulls: false, lineStyle: { width: 2, color: T.ink, cap: "round", join: "round" },
        markArea: areas.length ? { silent: true, data: areas } : undefined,
      }],
    };
  }, [T, serie, valores, bandas, unidad, nombre]);
  return <EChart option={option} height={170} ariaLabel={`${nombre}: promedio por hora del día`} />;
}

/** Días por categoría en cada periodo procesado (barras apiladas al 100 %). */
export function TrendChart({ periodos }: { periodos: ResumenPeriodo[] }) {
  const T = useTokens();
  const option = useMemo(() => {
    if (!T) return null;
    const cats = [...CATS, "Sin datos"].filter((c) => periodos.some((p) => (c === "Sin datos" ? p.numeralia.dias_sin_datos.length : p.numeralia.dias_por_categoria[c])));
    const n = (p: ResumenPeriodo, c: string) => (c === "Sin datos" ? p.numeralia.dias_sin_datos.length : p.numeralia.dias_por_categoria[c] ?? 0);
    return {
      animation: false, textStyle: { fontFamily: T.fontSans }, grid: { left: 110, right: 12, top: 34, bottom: 24 },
      legend: { top: 0, left: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: T.ink2, fontSize: 11 }, data: cats },
      tooltip: { ...tip(T), trigger: "axis", axisPointer: { type: "shadow" },
        formatter: (ps: { name: string; marker: string; seriesName: string; data: { n: number } }[]) => `<b>${ps[0].name}</b><br>` + ps.filter((p) => p.data.n).map((p) => `${p.marker}${p.seriesName}: <b>${p.data.n}</b> días`).join("<br>") },
      xAxis: { type: "value", max: 100, ...axis(T), axisLabel: { ...axis(T).axisLabel, formatter: "{value}%" } },
      yAxis: { type: "category", inverse: true, data: periodos.map((p) => p.nombre), ...axis(T), axisLabel: { ...axis(T).axisLabel, color: T.ink2, fontFamily: T.fontSans, fontSize: 12 } },
      series: cats.map((c) => ({
        type: "bar", name: c, stack: "p", barMaxWidth: 24, itemStyle: { color: T.cat[c], borderColor: T.surface, borderWidth: 2 },
        label: { show: true, formatter: (p: { data: { n: number; value: number } }) => (p.data.value >= 9 ? String(p.data.n) : ""), color: T.on[c], fontSize: 11, fontFamily: T.fontMono },
        data: periodos.map((p) => ({ value: (100 * n(p, c)) / p.numeralia.dias_mes, n: n(p, c) })),
      })),
    };
  }, [T, periodos]);
  return <EChart option={option} height={70 + periodos.length * 40} ariaLabel="Días por categoría en cada periodo analizado" />;
}
