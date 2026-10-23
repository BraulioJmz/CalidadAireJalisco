import fs from "node:fs";
import path from "node:path";
import { assertSprint2, type Sprint2Data } from "./sprint2-contract";

export function getSprint2(): Sprint2Data {
  const data: unknown = JSON.parse(fs.readFileSync(path.join(process.cwd(), "data/sprint2.json"), "utf8"));
  assertSprint2(data);
  return data;
}
