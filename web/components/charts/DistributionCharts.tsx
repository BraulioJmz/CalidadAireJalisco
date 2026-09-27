"use client";
import { useMemo } from "react";
import { CATS, PL } from "@/lib/aire";
import type { Numeralia } from "@/lib/types";
import { EChart } from "./EChart";
import { useTokens, type Tokens } from "./useTokens";

const axis = (T: Tokens) => ({
  axisLabel: { color: T.muted, fontFamily: T.fontMono, fontSize: 11 }, axisLine: { lineStyle: { color: T.rule } },
  splitLine: { lineStyle: { color: T.rule, opacity: 0.7 } }, axisTick: { show: false },
});
const tip = (T: Tokens) => ({ backgroundColor: T.surface, borderColor: T.rule, textStyle: { color: T.ink, fontSize: 12 }, confine: true });

export function DaysVsHoursChart({ n }: { n: Numeralia }) {
  const T = useTokens();
  const option = useMemo(() => {
    if (!T) return null;
    const dt = n.dias_con_categoria, ht = n.horas_con_categoria;
    const cats = CATS.filter((c) => n.horas_por_categoria[c] + n.dias_por_categoria[c] > 0);
    return {
      animation: false, textStyle: { fontFamily: T.fontSans }, grid: { left: 84, right: 12, top: 30, bottom: 24 },
      legend: { top: 0, left: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: T.ink2, fontSize: 11 }, data: cats },
      tooltip: { ...tip(T), trigger: "item", formatter: (p: { seriesName: string; value: number; name: string; data: { n: number } }) => `${p.seriesName}: <b>${p.value.toFixed(0)}%</b> de los ${p.name.split(" ")[0].toLowerCase()} (${p.data.n})` },
      xAxis: { type: "value", max: 100, ...axis(T), axisLabel: { ...axis(T).axisLabel, formatter: "{value}%" } },
      yAxis: { type: "category", data: [`Días (${dt})`, `Horas (${ht})`], inverse: true, ...axis(T), axisLabel: { ...axis(T).axisLabel, color: T.ink2 } },
      series: cats.map((c) => ({
        type: "bar", name: c, stack: "t", barWidth: 28, itemStyle: { color: T.cat[c], borderColor: T.surface, borderWidth: 2 },
        label: { show: true, formatter: (p: { value: number }) => (p.value >= 7 ? `${p.value.toFixed(0)}%` : ""), color: T.on[c], fontSize: 11, fontFamily: T.fontMono },
        data: [{ value: (100 * n.dias_por_categoria[c]) / dt, n: n.dias_por_categoria[c] }, { value: (100 * n.horas_por_categoria[c]) / ht, n: n.horas_por_categoria[c] }],
      })),
    };
  }, [T, n]);
  return <EChart option={option} height={200} ariaLabel="Porcentaje de días y de horas por categoría" />;
}

export function ResponsibleChart({ n }: { n: Numeralia }) {
  const T = useTokens();
  const option = useMemo(() => {
    if (!T) return null;
    const dt = n.dias_con_categoria, ht = n.horas_con_categoria;
    const pols = ["PM10", "O3", "PM2.5", "CO"];
    const lab = (p: { value: number }) => `${p.value.toFixed(0)}%`;
    return {
      animation: false, textStyle: { fontFamily: T.fontSans }, grid: { left: 52, right: 44, top: 30, bottom: 24 },
      legend: { top: 0, left: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: T.ink2, fontSize: 11 } },
      tooltip: { ...tip(T), trigger: "axis", axisPointer: { type: "shadow" }, formatter: (ps: { name: string; seriesName: string; value: number; data: { n: number } }[]) => `<b>${ps[0].name}</b><br>` + ps.map((p) => `${p.seriesName}: <b>${p.value.toFixed(0)}%</b> (${p.data.n})`).join("<br>") },
      xAxis: { type: "value", max: 100, ...axis(T), axisLabel: { ...axis(T).axisLabel, formatter: "{value}%" } },
      yAxis: { type: "category", data: pols.map((p) => PL[p]), inverse: true, ...axis(T), axisLabel: { ...axis(T).axisLabel, color: T.ink2 } },
      series: [
        { name: "Días", type: "bar", barWidth: 10, barGap: "30%", itemStyle: { color: T.accent, borderRadius: [0, 4, 4, 0] },
          label: { show: true, position: "right", color: T.ink2, fontSize: 10, fontFamily: T.fontMono, formatter: lab },
          data: pols.map((p) => ({ value: (100 * (n.dias_por_responsable[p] || 0)) / dt, n: n.dias_por_responsable[p] || 0 })) },
        { name: "Horas", type: "bar", barWidth: 10, itemStyle: { color: T.accentSoft, borderRadius: [0, 4, 4, 0] },
          label: { show: true, position: "right", color: T.ink2, fontSize: 10, fontFamily: T.fontMono, formatter: lab },
          data: pols.map((p) => ({ value: (100 * (n.horas_por_responsable[p] || 0)) / ht, n: n.horas_por_responsable[p] || 0 })) },
      ],
    };
  }, [T, n]);
  return <EChart option={option} height={200} ariaLabel="Contaminante responsable: porcentaje de días y de horas" />;
}

export function HourOfDayChart({ porHora, height = 300 }: { porHora: Record<string, number[]>; height?: number }) {
  const T = useTokens();
  const option = useMemo(() => {
    if (!T) return null;
    return {
      animation: false, textStyle: { fontFamily: T.fontSans }, grid: { left: 34, right: 8, top: 34, bottom: 26 },
      legend: { top: 0, left: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: T.ink2, fontSize: 11 } },
      tooltip: { ...tip(T), trigger: "axis", axisPointer: { type: "shadow" }, formatter: (ps: { name: string; marker: string; seriesName: string; value: number }[]) => `<b>${ps[0].name}:00</b><br>` + ps.filter((p) => p.value).map((p) => `${p.marker}${p.seriesName}: <b>${p.value}</b> días`).join("<br>") },
      xAxis: { type: "category", data: Array.from({ length: 24 }, (_, h) => String(h).padStart(2, "0")), ...axis(T) },
      yAxis: { type: "value", ...axis(T) },
      series: CATS.filter((c) => porHora[c]?.some((v) => v)).map((c) => ({
        type: "bar", name: c, stack: "h", barWidth: "72%", itemStyle: { color: T.cat[c], borderColor: T.surface, borderWidth: 1 }, data: porHora[c],
      })),
    };
  }, [T, porHora]);
  return <EChart option={option} height={height} ariaLabel="Número de días con cada categoría según la hora del día" />;
}
