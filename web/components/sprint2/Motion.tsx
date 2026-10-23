"use client";
import { useLayoutEffect, useRef, useSyncExternalStore, type HTMLAttributes } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";
const subscribe = (notify: () => void) => {
  const query = window.matchMedia(QUERY);
  query.addEventListener("change", notify);
  return () => query.removeEventListener("change", notify);
};
export function useReducedMotion() {
  return useSyncExternalStore(subscribe, () => window.matchMedia(QUERY).matches, () => true);
}

type Preset = "panel" | "detail" | "reveal";
const FRAMES: Record<Preset, Keyframe[]> = {
  panel: [{ opacity: .25, transform: "translateY(8px)" }, { opacity: 1, transform: "translateY(0)" }],
  detail: [{ opacity: .4, transform: "translateY(4px)" }, { opacity: 1, transform: "translateY(0)" }],
  reveal: [{ clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)" }],
};
/** Solo presentación: cancelar deja el estado final; nunca se encolan entradas/salidas. */
export function useEntrance<T extends Element>(signal: string, preset: Preset = "panel") {
  const ref = useRef<T>(null);
  const reduced = useReducedMotion();
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || reduced || typeof element.animate !== "function") return;
    const animation = element.animate(FRAMES[preset], {
      duration: preset === "reveal" ? 520 : 320,
      easing: "cubic-bezier(.2,.7,.3,1)", fill: "backwards",
    });
    return () => animation.cancel();
  }, [signal, preset, reduced]);
  return ref;
}

export function Motion({ signal, preset = "panel", ...props }: HTMLAttributes<HTMLDivElement> & { signal: string; preset?: Preset }) {
  const ref = useEntrance<HTMLDivElement>(signal, preset);
  return <div {...props} ref={ref} />;
}

export function AnimatedTabs({ labels, active, change }: { labels: string[]; active: number; change: (i: number) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const indicator = useRef<HTMLSpanElement>(null);
  const positioned = useRef(false);
  useLayoutEffect(() => {
    const nav = ref.current, marker = indicator.current;
    if (!nav || !marker) return;
    const measure = () => {
      const button = nav.querySelector<HTMLButtonElement>('[aria-selected="true"]');
      if (!button) return;
      if (!positioned.current) marker.style.transition = "none";
      marker.style.width = `${button.offsetWidth}px`;
      marker.style.transform = `translateX(${button.offsetLeft}px)`;
      marker.style.opacity = "1";
      if (!positioned.current) {
        marker.getBoundingClientRect();
        marker.style.transition = "";
        positioned.current = true;
      }
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(nav);
    nav.querySelectorAll('button').forEach(button => observer.observe(button));
    return () => observer.disconnect();
  }, [active]);
  return <div ref={ref} className="s2-tabs" role="tablist" aria-label="Vistas del Sprint 2">
    <span ref={indicator} className="s2-tab-indicator" aria-hidden="true" />
    {labels.map((label, i) => <button type="button" key={label} role="tab" id={`s2-tab-${i}`} aria-controls="s2-content" aria-selected={active === i} tabIndex={active === i ? 0 : -1} onClick={() => change(i)} onKeyDown={e => {
      const next = e.key === "ArrowRight" ? (i + 1) % labels.length : e.key === "ArrowLeft" ? (i + labels.length - 1) % labels.length : e.key === "Home" ? 0 : e.key === "End" ? labels.length - 1 : null;
      if (next === null) return;
      e.preventDefault();change(next);
      const nav = ref.current, button = nav?.querySelectorAll('button')[next];
      if (nav && button) {
        button.focus({ preventScroll: true });
        if (button.offsetLeft < nav.scrollLeft) nav.scrollLeft = button.offsetLeft;
        else if (button.offsetLeft + button.offsetWidth > nav.scrollLeft + nav.clientWidth) nav.scrollLeft = button.offsetLeft + button.offsetWidth - nav.clientWidth;
      }
    }}><span>{String(i + 1).padStart(2, "0")}</span>{label}</button>)}
  </div>;
}
