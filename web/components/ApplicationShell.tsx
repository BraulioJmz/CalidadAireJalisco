"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";
import { Seal } from "./Seal";
import { ThemeToggle } from "./ThemeToggle";
import { NavLinks } from "./NavLinks";
import { REPOSITORIO } from "@/lib/site";
import "@/components/academia/academia.css";

export function ApplicationShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const archived = ["/sprint-1", "/sprint-2", "/observatorio-mensual"].includes(path);
  if (archived) return <><SiteHeader /><main>{children}</main><SiteFooter /></>;
  return <>
    <header className="am-edition-header">
      <div className="am-edition-brand">
        <Link href="/" aria-label="Academia Miravalle · Panorama"><Seal size={32} /><span className="display">Academia Miravalle<small>Observatorio de calidad del aire</small></span></Link>
        <div className="am-edition-tools"><Link href="/metodologia">Metodología y fuentes</Link><ThemeToggle /></div>
      </div>
      <NavLinks />
    </header>
    <main>{children}</main>
    <footer className="am-edition-footer">
      <div><p className="display">Academia Miravalle</p><p>Estación Miravalle (MIR) · SEMADET Jalisco.</p><p>Proyecto académico · Universidad de Guadalajara · Equipo 3.</p></div>
      <nav aria-label="Recursos"><Link href="/metodologia">Metodología y fuentes</Link><Link href="/#fuentes">Datos y descargas</Link><a href={REPOSITORIO}>Repositorio ↗</a></nav>
      <nav aria-label="Versiones anteriores"><span>Versiones anteriores</span><Link href="/sprint-1" prefetch={false}>Sprint 1 · marzo 2024</Link><Link href="/sprint-2" prefetch={false}>Sprint 2 · 2023–2024</Link></nav>
    </footer>
  </>;
}
