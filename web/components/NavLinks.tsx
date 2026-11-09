"use client";
import Link from "next/link";
import { useLayoutEffect, useRef } from "react";
import { VIEWS, VIEW_KEYS, useAcademiaNavigation } from "./academia/Navigation";

export function NavLinks() {
  const { active, navigate, isApplication } = useAcademiaNavigation();
  const nav = useRef<HTMLElement>(null), marker = useRef<HTMLSpanElement>(null), ready = useRef(false);
  useLayoutEffect(() => {
    const update = () => {
      const selected = nav.current?.querySelector<HTMLElement>('[aria-current="page"]'), m = marker.current;
      if (!m) return;
      m.style.opacity = selected ? "1" : "0";
      if (!selected) return;
      if (!ready.current) m.style.transition = "none";
      m.style.width = `${selected.offsetWidth}px`; m.style.transform = `translateX(${selected.offsetLeft}px)`;
      if (!ready.current) { m.getBoundingClientRect(); m.style.transition = ""; ready.current = true; }
    };
    update(); const observer = new ResizeObserver(update); if (nav.current) observer.observe(nav.current);
    return () => observer.disconnect();
  }, [active, isApplication]);
  return <nav ref={nav} className="am-primary" aria-label="Principal"><span ref={marker} className="am-tab-marker" aria-hidden="true" />{VIEWS.map((label, i) => <Link key={label} id={`am-nav-${i}`} href={`/#${VIEW_KEYS[i]}`} prefetch={false} aria-current={isApplication && active === i ? "page" : undefined} onClick={e => {
    if (isApplication && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey) { e.preventDefault(); navigate(VIEW_KEYS[i]); }
  }} onKeyDown={e => {
    const index = e.key === "ArrowRight" ? (i + 1) % 4 : e.key === "ArrowLeft" ? (i + 3) % 4 : e.key === "Home" ? 0 : e.key === "End" ? 3 : null;
    if (index === null) return; e.preventDefault(); const link = nav.current?.querySelectorAll<HTMLAnchorElement>('a')[index]; link?.focus({preventScroll:true}); if(isApplication) navigate(VIEW_KEYS[index]);
  }}>{label}</Link>)}</nav>;
}
