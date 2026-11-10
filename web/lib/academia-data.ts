import source from "@/data/academia.json";
import { validateSummary } from "./academia";
export function getAcademia() { const data: unknown = source; validateSummary(data); return data; }
