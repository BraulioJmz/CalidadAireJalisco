import fs from "node:fs";
import path from "node:path";
import type { IndicePeriodo, PeriodoData } from "./types";

const DIR = path.join(process.cwd(), "data", "periodos");

export function getPeriodo(periodo: string): PeriodoData {
  return JSON.parse(fs.readFileSync(path.join(DIR, `${periodo}.json`), "utf8"));
}

export function getIndice(): IndicePeriodo[] {
  return JSON.parse(fs.readFileSync(path.join(DIR, "index.json"), "utf8"));
}

export function getUltimoPeriodo(): PeriodoData {
  const idx = getIndice();
  return getPeriodo(idx[idx.length - 1].periodo);
}
