"use client";
import { useEffect, useState } from "react";
import { CATS } from "@/lib/aire";

export type Tokens = {
  dark: boolean; ink: string; ink2: string; muted: string; rule: string; surface: string; bg: string;
  accent: string; accentSoft: string; bandAlpha: number;
  cat: Record<string, string>; on: Record<string, string>;
  fontSans: string; fontMono: string;
};

const KEYS: Record<string, string> = { Buena: "buena", Aceptable: "aceptable", Mala: "mala", "Muy Mala": "muymala", "Extremadamente Mala": "extrema", "Sin datos": "sin" };

function read(): Tokens {
  const cs = getComputedStyle(document.documentElement);
  const v = (n: string) => cs.getPropertyValue(n).trim();
  const cat: Record<string, string> = {}; const on: Record<string, string> = {};
  [...CATS, "Sin datos"].forEach((c) => { cat[c] = v(`--c-${KEYS[c]}`); on[c] = v(`--on-${KEYS[c]}`); });
  const body = getComputedStyle(document.body);
  return {
    dark: document.documentElement.classList.contains("dark"),
    ink: v("--ink"), ink2: v("--ink-2"), muted: v("--muted"), rule: v("--rule"), surface: v("--surface"), bg: v("--bg"),
    accent: v("--accent"), accentSoft: v("--accent-soft"), bandAlpha: parseFloat(v("--band-alpha")) || 0.16,
    cat, on,
    fontSans: body.fontFamily || "system-ui, sans-serif",
    fontMono: v("--font-geist-mono") ? `${v("--font-geist-mono")}, ui-monospace, monospace` : "ui-monospace, monospace",
  };
}

/** Lee los tokens de color del tema actual y se actualiza cuando cambia (toggle o sistema). */
export function useTokens(): Tokens | null {
  const [t, setT] = useState<Tokens | null>(null);
  useEffect(() => {
    const update = () => setT(read());
    update();
    const mo = new MutationObserver(update);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => mo.disconnect();
  }, []);
  return t;
}

export function withAlpha(color: string, a: number) {
  const h = color.replace("#", "");
  if (!/^[0-9a-f]{6}$/i.test(h)) return color;
  const n = parseInt(h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
