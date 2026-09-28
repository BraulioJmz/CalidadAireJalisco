"use client";
import Link from "next/link";
import { catBg, dec, fmt, PL } from "@/lib/aire";
import { Pol } from "../ui";
import { catsDelDia, hh, type ResumenDia } from "@/lib/resumen";

type Props = { dias: ResumenDia[]; unidades: Record<string, string>; hrefBase?: string };

const COLS = "grid-cols-[2.6rem_0.9rem_repeat(24,minmax(0,1fr))] sm:grid-cols-[4.2rem_5.6rem_2.8rem_repeat(24,minmax(0,1fr))_2.6rem]";

/**
 * Mapa día × hora: cada fila es un día; la segunda columna es su categoría diaria y las 24 celdas,
 * la categoría global de cada hora. Deja ver lo que se pierde al resumir el día.
 */
export function DayHourMatrix({ dias, unidades, hrefBase }: Props) {
  return (
    <div role="table" aria-label="Categoría global por día y hora" className="text-[0.7rem]">
      <div role="row" className={`grid ${COLS} items-end gap-x-[2px] pb-1.5 text-muted`}>
        <span role="columnheader" className="eyebrow !text-[0.6rem]">Día</span>
        <span role="columnheader" className="eyebrow !text-[0.6rem]"><span className="sr-only sm:not-sr-only">Diaria</span></span>
        <span role="columnheader" className="eyebrow hidden !text-[0.6rem] sm:block" title="Contaminante responsable de la categoría diaria">Resp.</span>
        {Array.from({ length: 24 }, (_, h) => (
          <span role="columnheader" key={h} className="num text-center text-[0.6rem]">{h % 6 === 0 ? hh(h) : <span className="sr-only">{hh(h)}</span>}</span>
        ))}
        <span role="columnheader" className="eyebrow hidden text-right !text-[0.6rem] sm:block" title="Horas peores que la categoría diaria">+peor</span>
      </div>
      <div className="space-y-[2px]">
        {dias.map((d, i) => {
          const dia = i + 1;
          const sin = d.Cat_global === "Sin datos";
          const resp = d.Responsable;
          const ind = sin ? "" : `, ${PL[resp]} ${fmt(d[`${resp}_indicador`], dec(resp))} ${unidades[resp] ?? ""}`;
          const label = `${dia} (${d.dia_semana}): categoría diaria ${d.Cat_global}${ind}; peor hora ${d.peor_horaria}; ${d.horas_peores} h peores que la diaria.`;
          const body = (
            <>
              <span role="rowheader" className="num flex items-baseline gap-1 text-ink-2">
                <b className="font-semibold text-ink">{hh(dia)}</b>
                <span className="hidden text-muted sm:inline">{d.dia_semana.slice(0, 3)}</span>
              </span>
              <span role="cell" className="flex h-full items-center">
                <i className="block h-full w-full rounded-[3px] sm:hidden" style={catBg(d.Cat_global)} title={d.Cat_global} />
                <span className="hidden w-full items-center gap-1.5 truncate sm:flex">
                  <i className="block size-2.5 shrink-0 rounded-[2px]" style={catBg(d.Cat_global)} />
                  <span className="truncate text-ink-2">{d.Cat_global}</span>
                </span>
              </span>
              <span role="cell" className="hidden items-center text-ink-2 sm:flex">{sin ? "—" : <Pol p={resp} />}</span>
              {catsDelDia(d).map((c, h) => (
                <i role="cell" key={h} title={`${hh(h)}:00 · ${c}`} aria-label={`${hh(h)}:00 ${c}`}
                  className="block h-full rounded-[2px]" style={catBg(c)} />
              ))}
              <span role="cell" className="num hidden text-right text-ink-2 sm:block">{d.horas_peores ? `+${d.horas_peores}` : ""}</span>
            </>
          );
          const cls = `grid ${COLS} h-[15px] items-stretch gap-x-[2px] rounded-[3px] sm:h-[18px]`;
          return hrefBase ? (
            <Link role="row" key={d.FECHA} href={`${hrefBase}?dia=${dia}#simulacion`} aria-label={`${label} Ver en la simulación`}
              className={`${cls} transition hover:bg-surface-2 hover:outline hover:outline-1 hover:outline-[var(--ink-2)]`}>{body}</Link>
          ) : (
            <div role="row" key={d.FECHA} aria-label={label} className={cls}>{body}</div>
          );
        })}
      </div>
    </div>
  );
}
