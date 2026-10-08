"use client";

import { motion, useReducedMotion } from "framer-motion";
import React from "react";
import { EASE } from "@/components/motion/primitives";

// The sign-in panel's artwork: stacked planes in isometric projection, like the floors of a building or the
// layers of a balance sheet, echoing the bars of the AfriEdge mark. Original geometry, flat tones, no glow. The
// planes settle into place once on load (about 0.8 s); with reduced motion they are simply there.
const BLOCKS = [
  // top, left side, right side for each block; the light face is the one accent.
  { faces: ["M520 40 L860 236 L520 432 L180 236 Z", "M180 236 L520 432 L520 520 L180 324 Z", "M520 432 L860 236 L860 324 L520 520 Z"],
    fills: ["#24272b", "#1c1e21", "#d8d2c4"] },
  { faces: ["M600 300 L860 450 L600 600 L340 450 Z", "M340 450 L600 600 L600 700 L340 550 Z", "M600 600 L860 450 L860 550 L600 700 Z"],
    fills: ["#2a2d32", "#1e2023", "#353a40"] },
  { faces: ["M300 520 L470 618 L300 716 L130 618 Z", "M130 618 L300 716 L300 760 L130 662 Z", "M300 716 L470 618 L470 662 L300 760 Z"],
    fills: ["#202326", "#191b1e", "#2c3035"] },
];

export function AuthArtwork() {
  const reduce = useReducedMotion();
  return (
    <svg viewBox="100 0 820 780" preserveAspectRatio="xMidYMin meet" aria-hidden className="absolute inset-x-0 top-0 h-[66%] w-full">
      {BLOCKS.map((b, i) => (
        <motion.g key={i} initial={reduce ? false : { opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 + i * 0.12, ease: EASE }}>
          {b.faces.map((d, j) => <path key={j} d={d} fill={b.fills[j]} />)}
        </motion.g>
      ))}
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <line key={i} x1={180 + i * 68} y1={236 + i * 39} x2={520 + i * 68} y2={40 + i * 39} stroke="#ffffff" strokeOpacity="0.05" />
      ))}
    </svg>
  );
}
