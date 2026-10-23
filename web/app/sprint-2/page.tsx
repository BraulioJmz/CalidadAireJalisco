import type { Metadata } from "next";
import { Sprint2 } from "@/components/sprint2/Sprint2";
import { getSprint2 } from "@/lib/sprint2";

export const metadata: Metadata = { title: "Sprint 2 · 2024 frente a 2023", description: "Comparación retrospectiva de Miravalle, con cobertura, categorías, meteorología y evidencia reproducible." };
export const dynamic = "force-static";
export default function Sprint2Page() { return <Sprint2 data={getSprint2()} />; }
