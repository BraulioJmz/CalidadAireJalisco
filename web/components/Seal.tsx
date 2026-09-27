import { ACADEMIA } from "@/lib/site";

/** Monograma de la academia: sello circular con las siglas y una traza de concentración. */
export function Seal({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" className="shrink-0">
      <circle cx="24" cy="24" r="23" fill="var(--brand)" />
      <circle cx="24" cy="24" r="19.5" fill="none" stroke="var(--bg)" strokeOpacity=".35" strokeWidth="1" />
      <path d="M10 34 L15 32 L20 33.5 L25 28 L30 30 L35 26 L38 27.5" fill="none" stroke="var(--accent-soft)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <text x="24" y="23.5" textAnchor="middle" fontSize="12" fontWeight="600" fill="var(--bg)" fontFamily="var(--font-display)">{ACADEMIA.siglas}</text>
    </svg>
  );
}
