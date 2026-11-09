"use client";
import { useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";

export const VIEWS = ["Panorama", "Histórico", "Episodios", "Predicción"];
export const VIEW_KEYS = ["panorama", "historico", "episodios", "prediccion"];
const subscribe = (notify: () => void) => {
  window.addEventListener("hashchange", notify);
  window.addEventListener("popstate", notify);
  window.addEventListener("academia:navigate", notify);
  return () => {
    window.removeEventListener("hashchange", notify);
    window.removeEventListener("popstate", notify);
    window.removeEventListener("academia:navigate", notify);
  };
};
export function useAcademiaNavigation() {
  const path = usePathname(), router = useRouter();
  const hash = useSyncExternalStore(subscribe, () => window.location.hash.slice(1), () => "");
  const aliases: Record<string, string> = { resumen: "panorama", comparacion: "historico/comparar", evaluacion: "prediccion/evaluacion" };
  const selection = aliases[hash] ?? (hash || (path === "/sprint-3" ? "prediccion" : "panorama"));
  const navigate = (key: string) => {
    if (path !== "/" && path !== "/sprint-3") { router.push("/#" + key); return; }
    if (window.location.hash !== "#" + key) window.history.pushState(null, "", "#" + key);
    window.dispatchEvent(new Event("academia:navigate"));
    requestAnimationFrame(() => {
      const app = document.querySelector(".am"), header = document.querySelector(".am-edition-header");
      if (app) window.scrollTo({ top: app.getBoundingClientRect().top + scrollY - (header?.getBoundingClientRect().height ?? 0), behavior: "instant" });
    });
  };
  return { selection, active: VIEW_KEYS.indexOf(selection.split("/")[0]), navigate, isApplication: path === "/" || path === "/sprint-3" };
}
