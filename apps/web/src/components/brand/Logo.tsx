"use client";

import { motion, useReducedMotion } from "framer-motion";
import React, { useEffect, useState } from "react";
import { EASE } from "@/components/motion/primitives";
import { MARK, MARK_VIEWBOX } from "./mark";

// The AfriEdge mark as inline SVG in currentColor: crisp at any size, follows the theme, no image request.
export function LogoMark({ size = 22, className = "", title }: { size?: number; className?: string; title?: string }) {
  return (
    <svg width={size} height={size} viewBox={MARK_VIEWBOX} fill="currentColor" className={className}
      role={title ? "img" : undefined} aria-label={title} aria-hidden={title ? undefined : true}>
      <path d={MARK.leftLeg} /><path d={MARK.rightLeg} /><path d={MARK.edge} />
      {MARK.bars.map((b) => <rect key={b.x} x={b.x} y={b.y} width={b.w} height={b.h} />)}
    </svg>
  );
}

// Mark plus wordmark. The wordmark is set in the site's own typeface at semibold weight.
export function Logo({ size = 22, className = "", wordClass = "text-[15px]" }: { size?: number; className?: string; wordClass?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 text-fg ${className}`}>
      <LogoMark size={size} />
      <span className={`font-semibold tracking-tight ${wordClass}`}>AfriEdge</span>
    </span>
  );
}

const SEEN = "afriedge-logo-revealed";

// The brand reveal, used on the sign-in page and loading states: the legs of the A enter, the bars rise one by
// one, the edge sweeps across, then the wordmark appears and everything settles into the static logo. It plays
// once per browser session (never on ordinary navigation), takes under a second, and with reduced motion the
// static logo is shown at once. Nothing waits for it; it is decoration over a page that already works.
export function AnimatedLogo({ size = 32, wordClass = "text-xl" }: { size?: number; wordClass?: string }) {
  const reduce = useReducedMotion();
  const [play, setPlay] = useState(false);
  useEffect(() => {
    let seen = true;
    try {
      seen = sessionStorage.getItem(SEEN) === "1";
      sessionStorage.setItem(SEEN, "1");
    } catch { /* storage blocked: show the static logo */ }
    // Starting the reveal is the effect's whole job: it reads browser state that does not exist during rendering.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!seen) setPlay(true);
  }, []);
  if (reduce || !play) return <span data-testid="brand-logo"><Logo size={size} wordClass={wordClass} /></span>;
  const t = (delay: number, duration = 0.35) => ({ duration, delay, ease: EASE });
  return (
    <span className="inline-flex items-center gap-2 text-fg" data-testid="brand-logo" data-animated="true">
      <svg width={size} height={size} viewBox={MARK_VIEWBOX} fill="currentColor" aria-hidden className="overflow-visible">
        <motion.path d={MARK.leftLeg} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={t(0)} />
        <motion.path d={MARK.rightLeg} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={t(0.08)} />
        {MARK.bars.map((b, i) => (
          <motion.rect key={b.x} x={b.x} y={b.y} width={b.w} height={b.h} style={{ transformBox: "fill-box", transformOrigin: "bottom" }}
            initial={{ scaleY: 0 }} animate={{ scaleY: 1 }} transition={t(0.2 + i * 0.07, 0.3)} />
        ))}
        <motion.path d={MARK.edge} style={{ transformBox: "fill-box", transformOrigin: "left center" }}
          initial={{ scaleX: 0, opacity: 0 }} animate={{ scaleX: 1, opacity: 1 }} transition={t(0.42, 0.4)} />
      </svg>
      <motion.span className={`font-semibold tracking-tight ${wordClass}`} initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} transition={t(0.62, 0.3)}>
        AfriEdge
      </motion.span>
    </span>
  );
}
