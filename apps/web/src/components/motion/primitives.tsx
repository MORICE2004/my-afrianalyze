"use client";

import { animate, motion, useReducedMotion } from "framer-motion";
import React, { useEffect, useRef } from "react";

// One timing system for the whole app. Micro-transitions sit between 0.2 and 0.35 s; only a finished research
// result uses the longer reveal. With reduced motion every primitive renders its final state at once.
export const T = { fast: 0.18, base: 0.28, reveal: 0.45 } as const;
export const EASE = [0.2, 0.7, 0.2, 1] as const;

export function FadeIn({ children, delay = 0, y = 6, className, as = "div" }: {
  children: React.ReactNode; delay?: number; y?: number; className?: string; as?: "div" | "section" | "li";
}) {
  const reduce = useReducedMotion();
  const M = motion[as];
  if (reduce) return React.createElement(as, { className }, children);
  return (
    <M className={className} initial={{ opacity: 0, y }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: T.base, delay, ease: EASE }}>
      {children}
    </M>
  );
}

// Children appear one after another, 40 ms apart. Used for result lists and news.
export function Stagger({ children, className, as = "div" }: { children: React.ReactNode; className?: string; as?: "div" | "ul" }) {
  const reduce = useReducedMotion();
  const M = motion[as];
  if (reduce) return React.createElement(as, { className }, children);
  return (
    <M className={className} initial="hidden" animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.04 } } }}>
      {children}
    </M>
  );
}

export function StaggerItem({ children, className, as = "div" }: { children: React.ReactNode; className?: string; as?: "div" | "li" }) {
  const M = motion[as];
  return (
    <M className={className} variants={{ hidden: { opacity: 0, y: 4 }, show: { opacity: 1, y: 0, transition: { duration: T.base, ease: EASE } } }}>
      {children}
    </M>
  );
}

// A number that settles into place once, the first time it is shown. It never re-counts on later renders, so
// a refreshed price does not "tick". `format` turns the number into its displayed text.
export function NumberReveal({ value, format, className }: { value: number; format: (n: number) => string; className?: string }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const done = useRef(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduce || done.current) {
      el.textContent = format(value);
      return;
    }
    done.current = true;
    const controls = animate(value * 0.985, value, {
      duration: T.reveal, ease: EASE, onUpdate: (v) => { el.textContent = format(v); },
      onComplete: () => { el.textContent = format(value); },
    });
    return () => controls.stop();
  }, [value, format, reduce]);
  return <span ref={ref} className={className}>{format(value)}</span>;
}

// A check that draws itself once and settles from 0.95 to 1 scale. One short pulse, never a loop.
export function VerifiedCheck({ size = 14, className = "" }: { size?: number; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-hidden className={className}
      initial={reduce ? false : { scale: 0.95, opacity: 0 }} animate={{ scale: [0.95, 1.06, 1], opacity: 1 }}
      transition={{ duration: T.reveal, ease: EASE, times: [0, 0.6, 1] }}>
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4" opacity="0.35" />
      <motion.path d="M4.8 8.3 7 10.4l4.3-4.7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
        initial={reduce ? false : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: T.base, delay: 0.1, ease: EASE }} />
    </motion.svg>
  );
}
