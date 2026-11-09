import type { Metadata } from "next";
import { Dashboard } from "@/components/academia/Dashboard";
import { getAcademia } from "@/lib/academia-data";
export const metadata: Metadata = { title: "Academia Miravalle · histórico y evaluación", description: "Histórico Miravalle 2015–2024, cobertura, comparación, episodios y evaluación retrospectiva de PM10. Evidencia de los tres sprints." };
export default function Inicio() { return <Dashboard data={getAcademia()} />; }
