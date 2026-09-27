import Link from "next/link";
import { ACADEMIA } from "@/lib/site";
import { NavLinks } from "./NavLinks";
import { Seal } from "./Seal";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-bg/80 backdrop-blur-md" style={{ paddingTop: "env(safe-area-inset-top, 0px)" }}>
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-3">
          <Seal size={34} />
          <span className="hidden min-w-0 leading-tight sm:block">
            <span className="display block truncate text-[1.05rem] font-semibold text-brand">{ACADEMIA.nombre}</span>
            <span className="block truncate text-xs text-muted">{ACADEMIA.unidad}</span>
          </span>
        </Link>
        <div className="ml-auto flex min-w-0 items-center gap-2">
          <NavLinks />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
