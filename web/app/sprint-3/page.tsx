import type { Metadata } from "next";
import { Dashboard } from "@/components/academia/Dashboard";
import { getAcademia } from "@/lib/academia-data";
export const metadata: Metadata = { title: "Miravalle · evaluación retrospectiva de PM10" };
export default function Sprint3() { return <Dashboard data={getAcademia()} />; }
