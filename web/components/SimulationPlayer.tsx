"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ECharts } from "echarts/core";
import { CATS, MES, MES_LARGO, ORD, PL, dec, dow, fmt, num, parseT, tLabel } from "@/lib/aire";
import { momentosClave } from "@/lib/momentos";
import type { HourRec, SimPayload } from "@/lib/types";
import { MensajesNOM } from "./MensajesNOM";
import { CatPill, Pol } from "./ui";
import { EChart } from "./charts/EChart";
import { useTokens, withAlpha, type Tokens } from "./charts/useTokens";

const LEN = 72;
const ARROW = "path://M0,-10 L6,6 L0,2 L-6,6 Z";

type Panel = { key: string; title: string; raw: string | null; ind: string; bands: number[] | null; indName: string };

function indicatorOf(r: HourRec, c: string) {
  return num(c === "O3" ? r.O3 : c === "CO" ? r.CO_8h : r[`${c}_NowCast`]);
}

export function SimulationPlayer({ data }: { data: SimPayload }) {
  const H = data.horario;
  const idx = useMemo(() => Object.fromEntries(H.map((h, i) => [h.t, i])) as Record<string, number>, [H]);
  const rec = data.periodo_simulacion;
  const recStart = idx[rec.inicio] ?? 0;
  const [start, setStart] = useState(recStart);
  // Estado inicial: la primera hora con la peor categoría del periodo recomendado
  const [k, setK] = useState(() => {
    const win = H.slice(recStart, recStart + LEN);
    return win.reduce((best, h, i) => ((ORD[h.Cat_global] ?? -1) > (ORD[win[best].Cat_global] ?? -1) ? i : best), 0);
  });
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(350);
  const [narrow, setNarrow] = useState(false);
  const tokens = useTokens();
  const w = useMemo(() => H.slice(start, start + LEN), [H, start]);
  const lastIdx = w.length - 1;

  // Ir a un día desde el calendario (evento) o desde la URL (?dia=N)
  const goToDay = useCallback((dia: number) => {
    const maxStart = Math.max(1, Math.floor(H.length / 24) - 2);
    const d0 = Math.min(Math.max(1, dia), maxStart);
    setPlaying(false);
    setStart((d0 - 1) * 24);
    setK((dia - d0) * 24 + 8);
  }, [H.length]);
  useEffect(() => {
    const onDia = (e: Event) => goToDay((e as CustomEvent<number>).detail);
    window.addEventListener("sim:dia", onDia);
    const q = new URLSearchParams(window.location.search).get("dia");
    if (q) goToDay(Number(q));
    const onResize = () => setNarrow(window.innerWidth < 640);
    onResize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("sim:dia", onDia); window.removeEventListener("resize", onResize); };
  }, [goToDay]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setK((x) => {
        if (x >= lastIdx) { setPlaying(false); return x; }
        return x + 1;
      });
    }, speed);
    return () => clearInterval(id);
  }, [playing, speed, lastIdx]);

  const r = w[Math.min(k, lastIdx)];
  const panels: Panel[] = useMemo(() => [
    { key: "PM10", title: "PM₁₀ · µg/m³", raw: "PM10", ind: "PM10_NowCast", bands: data.bandas.PM10, indName: "NowCast" },
    { key: "PM2.5", title: "PM₂.₅ · µg/m³", raw: "PM2.5", ind: "PM2.5_NowCast", bands: data.bandas["PM2.5"], indName: "NowCast" },
    { key: "O3", title: "O₃ · ppm (indicador = dato horario)", raw: null, ind: "O3", bands: data.bandas.O3, indName: "O₃ horario" },
    { key: "CO", title: "CO · ppm", raw: "CO", ind: "CO_8h", bands: data.bandas.CO, indName: "Promedio 8 h" },
    { key: "ET", title: "Temperatura exterior · °C", raw: null, ind: "ET", bands: null, indName: "Temperatura" },
    { key: "WS", title: "Viento · m/s y hacia dónde sopla", raw: null, ind: "WS", bands: null, indName: "Velocidad" },
  ], [data.bandas]);

  const layout = useMemo(() => {
    const left = narrow ? 40 : 52;
    const top0 = 34, ribbonH = 26, gap = 48, ph = narrow ? 96 : 110;
    const grids = [{ left, right: 16, top: top0, height: ribbonH }];
    const titles = [{ text: "Categoría global horaria", top: top0 - 24 }];
    let y = top0 + ribbonH + gap;
    panels.forEach((p) => { grids.push({ left, right: 16, top: y, height: ph }); titles.push({ text: p.title, top: y - 26 }); y += ph + gap; });
    return { grids, titles, height: y - gap + 36, left };
  }, [panels, narrow]);

  const option = useMemo(() => tokens && buildOption(tokens, w, k, panels, layout, narrow), [tokens, w, k, panels, layout, narrow]);

  // clic en la gráfica = saltar a esa hora
  const layoutRef = useRef(layout); layoutRef.current = layout;
  const onReady = useCallback((c: ECharts) => {
    c.getZr().on("click", (e: { offsetX: number; offsetY: number }) => {
      const pt = [e.offsetX, e.offsetY];
      for (let gi = 0; gi < layoutRef.current.grids.length; gi++) {
        if (c.containPixel({ gridIndex: gi }, pt)) {
          const x = c.convertFromPixel({ gridIndex: gi }, pt) as number[];
          if (x && x[0] != null) { setPlaying(false); setK(Math.max(0, Math.min(LEN - 1, Math.round(x[0])))); }
          break;
        }
      }
    });
  }, []);

  const opciones = useMemo(() => {
    const dias = Math.floor(H.length / 24);
    return Array.from({ length: Math.max(0, dias - 2) }, (_, i) => i + 1);
  }, [H.length]);

  const events = useMemo(() => {
    const out: { t: string; prev: string; h: HourRec }[] = [];
    for (let i = 0; i <= k && i < w.length; i++) {
      const h = w[i];
      if (!h.Cambio_categoria) continue;
      out.push({ t: h.t, prev: (i > 0 ? w[i - 1] : H[start - 1])?.Cat_global ?? "—", h });
    }
    return out.reverse();
  }, [w, k, H, start]);

  const momentos = useMemo(() => momentosClave(w, data.diario, data.unidades), [w, data.diario, data.unidades]);
  const mi = momentos.findIndex((m) => m.k === k);
  const irMomento = (i: number) => { const m = momentos[Math.max(0, Math.min(momentos.length - 1, i))]; if (m) { setPlaying(false); setK(m.k); } };
  const siguiente = momentos.findIndex((m) => m.k > k);
  const anterior = momentos.map((m) => m.k < k).lastIndexOf(true);

  if (!r) return null;
  const p = parseT(r.t);
  const g = r.Cat_global;
  const resp = r.Responsable;
  const ind = resp ? indicatorOf(r, resp) : null;
  const msg = data.mensajes[g] ?? data.mensajes["Sin datos"];
  const dia = data.diario.find((d) => d.FECHA === r.t.slice(0, 10));
  const pr = resp || "PM10";
  const u = data.unidades[pr];

  return (
    <div className="space-y-5">
      {/* Controles */}
      <div className="card flex flex-wrap items-center gap-3 p-3 sm:p-4">
        <label className="flex items-center gap-2 text-xs text-muted">Periodo
          <select className="rounded-lg border border-rule bg-surface px-3 py-2 text-sm text-ink" value={start}
            onChange={(e) => { setPlaying(false); setStart(Number(e.target.value)); setK(0); }}>
            <option value={recStart}>Recomendado · {tLabel(rec.inicio).slice(0, -6)} – {tLabel(rec.fin).slice(0, -6)}</option>
            {opciones.map((d) => <option key={d} value={(d - 1) * 24}>{d} – {d + 2} de {MES_LARGO[p.m - 1]}</option>)}
          </select>
        </label>
        <div className="flex items-center gap-1.5">
          <button type="button" className="rounded-lg border border-rule px-3 py-2 text-sm hover:border-ink-2" onClick={() => { setPlaying(false); setK((x) => Math.max(0, x - 1)); }} aria-label="Hora anterior">◀</button>
          <button type="button" onClick={() => { if (!playing && k >= lastIdx) setK(0); setPlaying((x) => !x); }}
            className="min-w-32 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg transition hover:opacity-90">
            {playing ? "❚❚ Pausa" : "▶ Reproducir"}
          </button>
          <button type="button" className="rounded-lg border border-rule px-3 py-2 text-sm hover:border-ink-2" onClick={() => { setPlaying(false); setK((x) => Math.min(lastIdx, x + 1)); }} aria-label="Hora siguiente">▶</button>
        </div>
        <label className="flex items-center gap-2 text-xs text-muted">Velocidad
          <select className="rounded-lg border border-rule bg-surface px-3 py-2 text-sm text-ink" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
            <option value={900}>1 h/s</option><option value={350}>3 h/s</option><option value={120}>8 h/s</option>
          </select>
        </label>
        <div className="flex min-w-[220px] flex-1 items-center gap-3">
          <span className="num hidden text-xs text-muted md:inline">{tLabel(w[0].t)}</span>
          <input type="range" min={0} max={lastIdx} value={k} aria-label="Hora de la simulación" className="w-full accent-[var(--accent)]"
            onChange={(e) => { setPlaying(false); setK(Number(e.target.value)); }} />
          <span className="num hidden text-xs text-muted md:inline">{tLabel(w[lastIdx].t)}</span>
        </div>
      </div>

      {/* Recorrido guiado: los momentos clave como diapositivas */}
      {momentos.length > 1 && (
        <div className="card p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="eyebrow">Recorrido guiado · {momentos.length} momentos clave</p>
            <div className="flex items-center gap-1.5">
              <button type="button" disabled={anterior < 0} onClick={() => irMomento(anterior)}
                className="rounded-lg border border-rule px-3 py-1.5 text-sm text-ink transition hover:border-ink-2 disabled:opacity-40">← Anterior</button>
              <button type="button" disabled={siguiente < 0} onClick={() => irMomento(siguiente)}
                className="rounded-lg border border-rule px-3 py-1.5 text-sm text-ink transition hover:border-ink-2 disabled:opacity-40">Siguiente →</button>
            </div>
          </div>
          <ol className="mt-3 flex flex-wrap gap-1.5" aria-label="Momentos clave">
            {momentos.map((m, i) => (
              <li key={m.k}>
                <button type="button" onClick={() => irMomento(i)} aria-current={i === mi ? "step" : undefined}
                  className={`rounded-full border px-3 py-1 text-xs transition ${i === mi ? "border-ink bg-ink text-bg" : "border-rule text-ink-2 hover:border-ink-2 hover:text-ink"}`}>
                  <span className="num">{i + 1}</span> · {m.titulo} <span className="num opacity-70">{tLabel(w[m.k].t)}</span>
                </button>
              </li>
            ))}
          </ol>
          <p className="mt-3 min-h-[3rem] text-[0.95rem] leading-relaxed text-ink-2" aria-live="polite">
            {mi >= 0 ? momentos[mi].texto : "Usa «Siguiente» para avanzar por los momentos clave, o reproduce la simulación hora por hora."}
          </p>
        </div>
      )}

      {/* Estado actual */}
      <div className="grid gap-4 lg:grid-cols-[1.05fr_1fr]">
        <div className="card relative overflow-hidden p-5 sm:p-6">
          <div className="absolute inset-x-0 top-0 h-1" style={{ background: tokens?.cat[g] ?? "transparent" }} />
          <div className="flex items-center gap-2">
            <span className="live-dot inline-block size-2 rounded-full" style={{ color: tokens?.cat[g] }}><span className="block size-2 rounded-full bg-current" /></span>
            <p className="eyebrow">Aviso para la comunidad · {playing ? "en reproducción" : "en pausa"}</p>
          </div>
          <p className="num mt-3 text-3xl font-medium tracking-tight text-ink">
            {p.d} {MES[p.m - 1]} {p.y} · {String(p.h).padStart(2, "0")}:00 <span className="text-base text-muted">{dow(r.t)}</span>
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <CatPill c={g} size="lg" />
            <span className="text-sm text-ink-2">Riesgo <b className="text-ink">{data.riesgo[g] ?? "—"}</b></span>
            {resp && <span className="text-sm text-ink-2">Define <b className="text-ink"><Pol p={resp} /></b> {fmt(ind, dec(resp))} {data.unidades[resp]}</span>}
            {r.Cambio_categoria && <span className="rounded-md bg-surface-2 px-2 py-1 text-xs font-medium text-ink-2">Cambio de categoría</span>}
          </div>
          <div className="mt-5 border-l-2 pl-4" style={{ borderColor: tokens?.cat[g] }}>
            <MensajesNOM m={msg} />
            <p className="mt-2 text-xs text-muted">Mensajes de la NOM-172-SEMARNAT-2023, tabla 12.</p>
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <p className="eyebrow">Información disponible en este momento</p>
          <div className="mt-3 divide-y divide-dashed divide-[var(--rule)] text-sm">
            {(["PM10", "PM2.5"] as const).map((c) => {
              const nc = num(r[`${c}_NowCast`]);
              return (
                <Row key={c} label={<Pol p={c} />} right={nc == null ? <span className="text-muted">NowCast no válido</span> : <span className="flex items-center gap-2"><span className="num">{fmt(nc)}</span><CatPill c={String(r[`Cat_${c}`])} /></span>}>
                  dato {r[c] == null ? <b>sin dato</b> : `${fmt(r[c])} µg/m³`} · {String(r[`${c}_datos_12h`] ?? 0)}/12 h en ventana · {String(r[`${c}_datos_3h`] ?? 0)}/3 recientes (mín. 2){r[`${c}_W`] != null ? ` · W = ${fmt(r[`${c}_W`], 2)}` : ""}
                </Row>
              );
            })}
            <Row label={<Pol p="O3" />} right={r.O3 == null ? <span className="text-muted">sin indicador</span> : <CatPill c={String(r.Cat_O3)} />}>
              dato {r.O3 == null ? <b>sin dato</b> : `${fmt(r.O3, 3)} ppm`} · se usa el valor horario
            </Row>
            <Row label="CO" right={r.CO_8h == null ? <span className="text-muted">8 h no válido</span> : <span className="flex items-center gap-2"><span className="num">{fmt(r.CO_8h, 2)}</span><CatPill c={String(r.Cat_CO)} /></span>}>
              dato {r.CO == null ? <b>sin dato</b> : `${fmt(r.CO, 3)} ppm`} · {String(r.CO_datos_8h ?? 0)}/8 h (mín. 6)
            </Row>
            <Row label="Día" right={null}>
              {p.h < 23 ? <>Categoría diaria aún no disponible: el día cierra a las 23:00 (faltan {23 - p.h} h).</>
                : dia && dia.Cat_global !== "Sin datos" ? <span className="inline-flex flex-wrap items-center gap-2">Categoría del {p.d}: <CatPill c={dia.Cat_global} /> por <Pol p={dia.Responsable} /></span>
                : <>Sin datos suficientes para el día.</>}
            </Row>
          </div>
        </div>
      </div>

      {/* Flujo del dato */}
      <div>
        <p className="eyebrow mb-2">Recorrido del contaminante responsable en esta hora</p>
        <ol className="grid grid-cols-2 gap-2 md:grid-cols-5">
          {[
            ["Dato horario", r[pr] == null ? "Sin dato" : `${fmt(r[pr], dec(pr))} ${u}`, `${PL[pr]} · ${tLabel(r.t)}`],
            ["Procesamiento", pr === "CO" ? `Promedio de ${String(r.CO_datos_8h)}/8 h` : pr === "O3" ? "Valor horario" : `NowCast · W = ${fmt(r[`${pr}_W`], 2)}`, "Solo con horas ya recibidas"],
            ["Indicador", ind == null ? "No válido" : `${fmt(ind, dec(pr))} ${u}`, data.indicador_horario[pr]],
            ["Categoría", null, `Riesgo ${data.riesgo[g] ?? "—"}`],
            ["Información", r.Cambio_categoria ? "Emitir aviso" : "Mantener aviso", data.descripcion_riesgo?.[g]?.general ?? msg.general],
          ].map(([k1, v, s], i) => (
            <li key={String(k1)} className={`card flex flex-col gap-1.5 p-3.5 ${i === 4 ? "col-span-2 md:col-span-1" : ""}`}>
              <span className="num text-[0.66rem] uppercase tracking-[0.12em] text-muted">{String(i + 1).padStart(2, "0")} · {k1}</span>
              <span className="text-[1.02rem] font-semibold leading-tight text-ink">{i === 3 ? <CatPill c={resp ? g : "Sin datos"} size="md" /> : v}</span>
              <span className="text-xs leading-snug text-ink-2">{s}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Línea de tiempo */}
      <div className="card p-2 sm:p-3">
        <EChart option={option} height={layout.height} ariaLabel="Línea de tiempo de concentraciones, indicadores, categorías y meteorología" onReady={onReady} replace />
      </div>
      <p className="text-xs leading-relaxed text-muted">
        Franjas: categorías del Índice AIRE Y SALUD de cada contaminante. Línea delgada: dato horario; línea gruesa: indicador de la NOM.
        Flechas: hacia dónde sopla el viento (norte arriba). La línea vertical es la hora simulada; toca la gráfica para saltar a otra hora.
      </p>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="mb-3 font-semibold text-ink">Cambios de categoría hasta esta hora</h3>
          <div className="scroll-thin max-h-72 divide-y divide-[var(--rule)] overflow-auto text-sm">
            {events.length === 0 && <p className="text-muted">Todavía no hay cambios en este periodo.</p>}
            {events.map((e) => (
              <div key={e.t} className="grid grid-cols-[110px_1fr] items-center gap-3 py-2">
                <span className="num text-xs text-ink-2">{tLabel(e.t)}</span>
                <span className="flex flex-wrap items-center gap-1.5 text-ink-2"><span>{e.prev} →</span> <CatPill c={e.h.Cat_global} />
                  {e.h.Responsable && <span>por <Pol p={e.h.Responsable} /> ({fmt(indicatorOf(e.h, e.h.Responsable), dec(e.h.Responsable))} {data.unidades[e.h.Responsable]})</span>}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="mb-2 font-semibold text-ink">¿Por qué este periodo?</h3>
          <p className="text-sm leading-relaxed text-ink-2">{rec.criterio} El periodo recomendado alcanzó <b className="text-ink">{rec.peor}</b>, tuvo {rec.cambios} cambios de categoría y {rec.horas_mala_o_peor} horas en Mala o peor.</p>
        </div>
      </div>
    </div>
  );
}

function Row({ label, right, children }: { label: React.ReactNode; right: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[46px_1fr] gap-x-3 gap-y-1.5 py-2.5 sm:grid-cols-[52px_1fr_auto] sm:items-center">
      <span className="font-semibold text-ink">{label}</span>
      <span className="leading-snug text-ink-2">{children}</span>
      {right && <span className="col-start-2 sm:col-start-3">{right}</span>}
    </div>
  );
}

type Layout = { grids: { left: number; right: number; top: number; height: number }[]; titles: { text: string; top: number }[]; height: number; left: number };

function buildOption(T: Tokens, w: HourRec[], k: number, panels: Panel[], L: Layout, narrow: boolean) {
  const labels = w.map((r) => { const p = parseT(r.t); return `${p.d} ${MES[p.m - 1]} ${String(p.h).padStart(2, "0")}h`; });
  const cut = <V,>(arr: V[]) => arr.map((v, i) => (i <= k ? v : null));
  const series: Record<string, unknown>[] = [];
  series.push({
    type: "custom", xAxisIndex: 0, yAxisIndex: 0, name: "Categoría", animation: false,
    renderItem: (_: unknown, api: { value: (d: number) => number; coord: (v: number[]) => number[]; size: (v: number[]) => number[] }) => {
      const i = api.value(0); const pt = api.coord([i, 0]); const sz = api.size([1, 1]); const r = w[i];
      const kids: Record<string, unknown>[] = [{ type: "rect", shape: { x: pt[0] - sz[0] / 2 + 0.5, y: pt[1] - sz[1] / 2, width: Math.max(sz[0] - 1, 1), height: sz[1], r: 2 }, style: { fill: T.cat[r.Cat_global] ?? T.cat["Sin datos"] } }];
      if (r.Cambio_categoria) kids.push({ type: "rect", shape: { x: pt[0] - sz[0] / 2 - 1, y: pt[1] - sz[1] / 2 - 5, width: 2, height: sz[1] + 10 }, style: { fill: T.ink } });
      return { type: "group", children: kids };
    },
    data: w.map((_, i) => (i <= k ? [i, 0] : null)).filter(Boolean),
  });
  panels.forEach((p, j) => {
    const gi = j + 1;
    const markLine = { silent: true, symbol: "none", lineStyle: { color: T.ink, width: 1, type: "solid" }, label: { show: false }, data: [{ xAxis: k }] };
    if (p.raw) series.push({ type: "line", name: "Dato horario", xAxisIndex: gi, yAxisIndex: gi, data: cut(w.map((r) => num(r[p.raw!]))), showSymbol: false, lineStyle: { width: 1, color: T.muted }, itemStyle: { color: T.muted }, animation: false });
    const isWS = p.key === "WS";
    const indData = w.map((r, i) => {
      if (i > k) return null;
      const v = num(r[p.ind]);
      const wd = num(r.WD);
      if (isWS && v != null && wd != null) return { value: v, symbol: ARROW, symbolSize: narrow ? 8 : 11, symbolRotate: -((wd + 180) % 360) };
      return v;
    });
    const b = p.bands;
    const bands = b ? [[0, b[0]], [b[0], b[1]], [b[1], b[2]], [b[2], b[3]], [b[3], b[3] * 3]] : [];
    series.push({
      type: "line", name: p.indName, xAxisIndex: gi, yAxisIndex: gi, data: indData, animation: false,
      showSymbol: isWS, showAllSymbol: true, symbol: isWS ? ARROW : "circle",
      lineStyle: { width: isWS ? 1.5 : 2.2, color: T.ink }, itemStyle: { color: isWS ? T.accent : T.ink },
      markLine,
      markArea: bands.length ? { silent: true, data: bands.map((bb, bi) => [{ yAxis: bb[0], itemStyle: { color: withAlpha(T.cat[CATS[bi]], T.bandAlpha) } }, { yAxis: bb[1] }]) } : undefined,
    });
  });
  const yMax = (p: Panel) => {
    if (!p.bands) return undefined;
    const vals = w.flatMap((r) => [num(r[p.ind]), p.raw ? num(r[p.raw]) : null]).filter((v): v is number => v != null);
    const mx = vals.length ? Math.max(...vals) : 1;
    const v = Math.max(mx * 1.05, p.bands[1] * 1.02);
    const st = Math.pow(10, Math.floor(Math.log10(v))) / 2;
    return Math.ceil(v / st) * st;
  };
  const axisFont = { color: T.muted, fontFamily: T.fontMono, fontSize: 10 };
  return {
    animation: false,
    textStyle: { fontFamily: T.fontSans },
    title: L.titles.map((t) => ({ ...t, left: L.left, textStyle: { fontSize: 12, fontWeight: 600, color: T.ink2, fontFamily: T.fontSans } })),
    grid: L.grids,
    xAxis: L.grids.map((_, i) => ({
      type: "category", gridIndex: i, data: labels, boundaryGap: true, axisTick: { show: false }, axisLine: { lineStyle: { color: T.rule } },
      axisLabel: { ...axisFont, show: i === L.grids.length - 1 || i === 0, interval: (n: number) => n % (narrow ? 24 : 6) === 0 },
      splitLine: { show: false },
    })),
    yAxis: L.grids.map((_, i) => {
      if (i === 0) return { type: "category", gridIndex: 0, data: ["g"], show: false };
      const p = panels[i - 1];
      return { type: "value", gridIndex: i, min: p.key === "ET" ? "dataMin" : 0, max: yMax(p), splitNumber: 3,
        axisLabel: { ...axisFont, showMaxLabel: !p.bands }, splitLine: { lineStyle: { color: T.rule, opacity: 0.7 } } };
    }),
    axisPointer: { link: [{ xAxisIndex: "all" }], lineStyle: { color: T.muted } },
    tooltip: {
      trigger: "axis", confine: true, backgroundColor: T.surface, borderColor: T.rule, textStyle: { color: T.ink, fontSize: 12 },
      formatter: (ps: { dataIndex: number }[]) => {
        const i = ps[0].dataIndex; const r = w[i];
        if (i > k) return `<b>${tLabel(r.t)}</b><br><span style="color:${T.muted}">Este dato aún no llega.</span>`;
        const line = (a: string, v: string) => `<div style="display:flex;justify-content:space-between;gap:16px"><span>${a}</span><b>${v}</b></div>`;
        return `<div style="min-width:220px"><b>${tLabel(r.t)}</b> · ${r.Cat_global}${r.Responsable ? " por " + PL[r.Responsable] : ""}` +
          line("PM₁₀ dato / NowCast", `${fmt(r.PM10)} / ${fmt(r.PM10_NowCast)}`) +
          line("PM₂.₅ dato / NowCast", `${fmt(r["PM2.5"])} / ${fmt(r["PM2.5_NowCast"])}`) +
          line("O₃ ppm", fmt(r.O3, 3)) + line("CO dato / 8 h", `${fmt(r.CO, 3)} / ${fmt(r.CO_8h, 2)}`) +
          line("Temperatura", r.ET == null ? "—" : `${fmt(r.ET)} °C`) +
          line("Viento", r.WS == null ? "—" : `${fmt(r.WS, 1)} m/s ${r.Sector_viento ?? ""}`) + `</div>`;
      },
    },
    series,
  };
}
