import { dec, fmt, MES_LARGO, num, ORD, parseT, PL } from "./aire";
import type { DayRec, HourRec } from "./types";

/** Un momento del recorrido guiado de la simulación: a qué hora saltar y qué explicar. */
export type Momento = { k: number; titulo: string; texto: string };

const hora = (t: string) => `${t.slice(11, 13)}:00`;
const fecha = (t: string) => { const p = parseT(t); return `${p.d} de ${MES_LARGO[p.m - 1]}`; };
const indicador = (r: HourRec, c: string) => num(c === "O3" ? r.O3 : c === "CO" ? r.CO_8h : r[`${c}_NowCast`]);
const nombreInd = (c: string) => (c === "O3" ? "valor horario" : c === "CO" ? "promedio de 8 h" : "NowCast");

function meteo(r: HourRec) {
  const et = num(r.ET), ws = num(r.WS);
  const partes = [];
  if (et != null) partes.push(`temperatura de ${fmt(et)} °C`);
  if (ws != null) partes.push(`viento de ${fmt(ws, 1)} m/s${r.Sector_viento ? ` del ${r.Sector_viento}` : ""}`);
  return partes.length ? ` En esa hora se registró ${partes.join(" y ")}.` : "";
}

/**
 * Momentos clave de una ventana de la simulación, calculados solo con los datos.
 * Sirven para recorrerla como diapositivas: cada uno fija una hora y la explica.
 */
export function momentosClave(w: HourRec[], diario: DayRec[], unidades: Record<string, string>): Momento[] {
  if (!w.length) return [];
  const out: Momento[] = [];
  const u = (c: string) => unidades[c] ?? "";
  const val = (r: HourRec, c: string) => `${fmt(indicador(r, c), dec(c))} ${u(c)}`;

  // 1. Punto de partida
  const r0 = w[0];
  out.push({
    k: 0, titulo: "Inicio del periodo",
    texto: `${fecha(r0.t)}, 00:00. La categoría global es ${r0.Cat_global}${r0.Responsable ? ` y la define ${PL[r0.Responsable]} (${nombreInd(r0.Responsable)} de ${val(r0, r0.Responsable)})` : ""}. `
      + "Las ventanas de 12 h (NowCast) y de 8 h (CO) ya están completas porque se usan las horas previas.",
  });

  // 2. Peor categoría del periodo (primera vez)
  const peor = w.reduce((a, r) => ((ORD[r.Cat_global] ?? -1) > (ORD[a] ?? -1) ? r.Cat_global : a), "Buena");
  const kp = w.findIndex((r) => r.Cat_global === peor);
  if (kp > 0) {
    const r = w[kp], c = r.Responsable, prev = w[kp - 1].Cat_global;
    const crudo = c && c !== "O3" && num(r[c]) != null ? ` (dato horario: ${fmt(num(r[c]), dec(c))} ${u(c)})` : "";
    out.push({
      k: kp, titulo: `Sube a ${peor}`,
      texto: `${fecha(r.t)}, ${hora(r.t)}. ${c ? `El ${nombreInd(c)} de ${PL[c]} alcanza ${val(r, c)}${crudo}` : "Cambia la categoría"} `
        + `y la categoría global pasa de ${prev} a ${peor}, la peor condición del periodo: es el momento de emitir un aviso.${meteo(r)}`,
    });


    // 3. Cambio del contaminante responsable después del pico
    const kc = w.findIndex((x, i) => i > kp && x.Responsable && x.Responsable !== c && x.Cat_global !== "Buena");
    if (kc > 0) {
      const x = w[kc];
      out.push({
        k: kc, titulo: `Cambia a ${PL[x.Responsable]}`,
        texto: `${fecha(x.t)}, ${hora(x.t)}. El contaminante responsable deja de ser ${PL[c]} y pasa a ser ${PL[x.Responsable]} (${nombreInd(x.Responsable)} de ${val(x, x.Responsable)}), con categoría ${x.Cat_global}. `
          + `El aviso sigue, pero cambia su motivo.${meteo(x)}`,
      });
    }

    // 4. Regreso a Buena
    const kb = w.findIndex((x, i) => i > kp && x.Cat_global === "Buena");
    if (kb > 0) {
      const x = w[kb];
      const pm = ["PM10", "PM2.5"].find((p) => num(x[p]) != null && num(x[`${p}_NowCast`]) != null);
      out.push({
        k: kb, titulo: "Regresa a Buena",
        texto: `${fecha(x.t)}, ${hora(x.t)}. Todos los indicadores vuelven a la banda Buena y el aviso puede retirarse.`
          + (pm ? ` El NowCast de ${PL[pm]} (${fmt(num(x[`${pm}_NowCast`]))} µg/m³) todavía pondera las horas anteriores: responde con retraso a la mejora del dato horario (${fmt(num(x[pm]))} µg/m³).` : "")
          + meteo(x),
      });
    }

    // 5. Cierre del día del pico: aparece la categoría diaria
    const kd = w.findIndex((x, i) => i >= kp && x.t.slice(0, 10) === r.t.slice(0, 10) && x.t.endsWith("23:00"));
    const d = diario.find((x) => x.FECHA === r.t.slice(0, 10));
    if (kd > 0 && d) {
      const peores = Number(d.horas_peores_que_diaria ?? 0);
      out.push({
        k: kd, titulo: "Cierra el día",
        texto: `${fecha(w[kd].t)}, 23:00. Solo al cerrar el día se conoce su categoría diaria: ${d.Cat_global}${d.Responsable ? ` por ${PL[d.Responsable]}` : ""}. `
          + (peores ? `${peores} horas de ese día estuvieron en una categoría peor que la diaria: el resumen suaviza el episodio.` : "Ninguna hora superó la categoría diaria."),
      });
    }
  }

  // 6. Máximo de ozono (si llegó al menos a Aceptable)
  const ko = w.reduce((b, x, i) => ((num(x.O3) ?? -1) > (num(w[b].O3) ?? -1) ? i : b), 0);
  if ((ORD[String(w[ko].Cat_O3)] ?? 0) >= 1 && !out.some((m) => m.k === ko)) {
    const x = w[ko];
    out.push({
      k: ko, titulo: "Máximo de ozono",
      texto: `${fecha(x.t)}, ${hora(x.t)}. El O₃ llega a ${fmt(num(x.O3), 3)} ppm, su máximo en el periodo (categoría ${x.Cat_O3}).${meteo(x)} Es una coincidencia en el tiempo; no demuestra una causa.`,
    });
  }

  // 7. Pérdida de datos: un NowCast deja de ser válido
  const kn = w.findIndex((x, i) => i > 0 && ["PM10", "PM2.5"].some((p) => num(x[`${p}_NowCast`]) == null && num(w[i - 1][`${p}_NowCast`]) != null));
  if (kn > 0 && !out.some((m) => m.k === kn)) {
    const x = w[kn];
    const p = ["PM10", "PM2.5"].find((q) => num(x[`${q}_NowCast`]) == null && num(w[kn - 1][`${q}_NowCast`]) != null)!;
    out.push({
      k: kn, titulo: "Faltan datos",
      texto: `${fecha(x.t)}, ${hora(x.t)}. El NowCast de ${PL[p]} deja de calcularse: faltan datos en 2 de las 3 horas más recientes (NOM, 5.2.5.3). `
        + `La categoría global se obtiene con los contaminantes que sí tienen indicador (${x.Cat_global}).`,
    });
  }

  return out.sort((a, b) => a.k - b.k).filter((m, i, arr) => i === 0 || m.k !== arr[i - 1].k);
}
