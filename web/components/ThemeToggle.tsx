"use client";
import { useEffect, useState } from "react";

export const THEME_SCRIPT = `(()=>{try{var t=localStorage.getItem('tema');var d=t?t==='oscuro':matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.classList.toggle('dark',d)}catch(e){}})()`;

export function ThemeToggle() {
  const [dark, setDark] = useState<boolean | null>(null);
  useEffect(() => setDark(document.documentElement.classList.contains("dark")), []);
  const toggle = () => {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    try { localStorage.setItem("tema", next ? "oscuro" : "claro"); } catch {}
    setDark(next);
  };
  return (
    <button type="button" onClick={toggle} aria-label={dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className="grid size-9 place-items-center rounded-full border border-rule bg-surface text-ink-2 transition hover:text-ink">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        {dark ? (
          <><circle cx="12" cy="12" r="4.5" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>
        ) : (
          <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
        )}
      </svg>
    </button>
  );
}
