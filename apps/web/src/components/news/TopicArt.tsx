import React from "react";

// An original AfriEdge graphic for a news topic, drawn in SVG: the visual of a story when its publisher allows
// no image. It illustrates the topic (a rate step, a currency crossing, a yield curve...), never the event, so it
// cannot be mistaken for evidence. Deterministic: the same story always gets the same composition.
type Motif = (seed: number) => React.ReactNode;

const S = "#e9e4d8"; // the warm accent used across the brand artwork
const M: Record<string, Motif> = {
  "Monetary Policy": (k) => (
    <g fill={S}>{[0, 1, 2, 3, 4].map((i) => <rect key={i} x={70 + i * 52} y={150 - (i < 2 + (k % 2) ? i : 2 + (k % 2)) * 22} width="38" height={60 + (i < 2 + (k % 2) ? i : 2 + (k % 2)) * 22} opacity={0.35 + i * 0.13} />)}</g>
  ),
  Inflation: () => (
    <g fill="none" stroke={S} strokeWidth="5"><path d="M50 190 C130 180 170 120 230 110 S330 60 350 40" /><path d="M50 205 H360" strokeOpacity="0.25" strokeWidth="2" /></g>
  ),
  FX: () => (
    <g fill="none" stroke={S} strokeWidth="5"><path d="M50 70 C150 70 250 190 350 190" /><path d="M50 190 C150 190 250 70 350 70" strokeOpacity="0.45" /></g>
  ),
  Bonds: () => (
    <g fill="none" stroke={S}><path d="M50 200 C90 120 160 90 350 75" strokeWidth="5" />{[90, 150, 210, 270, 330].map((x) => <circle key={x} cx={x} cy={x < 100 ? 135 : x < 160 ? 100 : x < 220 ? 88 : x < 280 ? 81 : 77} r="6" fill={S} />)}</g>
  ),
  Banking: () => (
    <g fill={S}><path d="M200 40 L330 95 H70 Z" opacity="0.9" />{[95, 150, 205, 260].map((x) => <rect key={x} x={x} y="105" width="26" height="85" opacity="0.55" />)}<rect x="70" y="196" width="260" height="10" /></g>
  ),
  "Fiscal Policy": () => (
    <g fill={S}>{[0, 1, 2].map((i) => <rect key={i} x={110 + i * 20} y={60 + i * 20} width="150" height="110" opacity={0.25 + i * 0.3} />)}</g>
  ),
  GDP: () => (
    <g fill={S}>{[0, 1, 2, 3, 4, 5].map((i) => <rect key={i} x={60 + i * 48} y={200 - (40 + i * 24)} width="30" height={40 + i * 24} opacity={0.4 + i * 0.1} />)}</g>
  ),
};

// Stories without a recognised topic get one of three abstract compositions, chosen by the story's id.
function fallback(k: number) {
  const v = k % 3;
  if (v === 0) {
    return <g fill={S}>{[0, 1, 2].map((i) => <path key={i} d={`M${90 + i * 70} ${170 - i * 30} l60 -35 l60 35 l-60 35 Z`} opacity={0.3 + ((i + k) % 3) * 0.25} />)}</g>;
  }
  if (v === 1) {
    return <g fill="none" stroke={S} strokeWidth="4">{[40, 75, 110, 145].map((r, i) => <path key={r} d={`M${200 - r} 220 A${r} ${r} 0 0 1 ${200 + r} 220`} strokeOpacity={0.25 + i * 0.2} />)}</g>;
  }
  return <g fill={S}>{Array.from({ length: 24 }, (_, i) => <circle key={i} cx={95 + (i % 6) * 42} cy={70 + Math.floor(i / 6) * 38} r={4 + ((i + k) % 4)} opacity={0.3 + ((i * 7 + k) % 5) * 0.14} />)}</g>;
}

export function TopicArt({ id, topic, source, large = false }: { id: string; topic?: string; source: string; large?: boolean }) {
  const seed = parseInt(id.slice(0, 6), 16) || 0;
  const draw = (topic && M[topic]) || fallback;
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#1a1c1f]" data-testid="topic-art">
      <svg viewBox="0 0 400 240" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full" aria-hidden>
        <path d="M0 240 L400 0 V240 Z" fill="#202327" />
        {draw(seed)}
      </svg>
      <div className={`absolute inset-x-0 top-0 flex items-center justify-between ${large ? "p-5" : "p-3"}`}>
        <span className={`font-semibold uppercase tracking-[0.08em] text-white/80 ${large ? "text-xs" : "text-[10px]"}`}>{source}</span>
      </div>
      <div className={`absolute bottom-0 left-0 ${large ? "p-5" : "p-3"}`}>
        <span className={`font-medium text-white/90 ${large ? "text-sm" : "text-[11px]"}`}>{topic ?? "Official release"}</span>
      </div>
    </div>
  );
}
