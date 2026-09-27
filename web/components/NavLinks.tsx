"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Observatorio", short: "Inicio" },
  { href: "/sprint-1", label: "Boletín 1", short: "Boletín 1" },
  { href: "/metodologia", label: "Metodología", short: "Método" },
];

export function NavLinks() {
  const path = usePathname();
  return (
    <nav aria-label="Principal" className="flex items-center gap-1 overflow-x-auto">
      {LINKS.map((l) => {
        const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
        return (
          <Link key={l.href} href={l.href} aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap rounded-full px-2.5 py-1.5 text-[13px] transition sm:px-3 sm:text-sm ${active ? "bg-ink text-bg" : "text-ink-2 hover:bg-surface-2 hover:text-ink"}`}>
            <span className="sm:hidden">{l.short}</span><span className="hidden sm:inline">{l.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
