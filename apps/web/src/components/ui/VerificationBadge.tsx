"use client";

import * as Popover from "@radix-ui/react-popover";
import { motion, useReducedMotion } from "framer-motion";
import React from "react";
import { EASE, T, VerifiedCheck } from "@/components/motion/primitives";

// One trust indicator for AfriEdge, with three distinct meanings that are never mixed up:
//   Verified data          automated: two independent extraction methods agreed (no person checked it)
//   Reviewed research      a named reviewer examined the research run
//   Approved publication   a named reviewer approved it for publication
// Each is shown only when that process actually happened. Freshness words (Updated, Stale...) are separate.
export type Verification = "Verified data" | "Reviewed research" | "Approved publication" | "Updated" | "Stale" | "Limited" | "Unavailable";

const QUIET = new Set<Verification>(["Verified data", "Reviewed research", "Approved publication", "Updated"]);

export type Provenance = {
  kind?: string; source?: string; page?: string | number; reporting?: string; retrieved?: string; currency?: string;
  method?: string; reviewer?: string; href?: string;
};

export function VerificationBadge({ state, detail, testId }: { state: Verification; detail?: Provenance; testId?: string }) {
  const reduce = useReducedMotion();
  const tone = QUIET.has(state) ? "text-fg" : state === "Unavailable" ? "text-faint" : "text-warn";
  const mark = state === "Verified data" || state === "Approved publication" ? <VerifiedCheck size={14} />
    : state === "Reviewed research" ? <span aria-hidden className="h-2 w-2 rounded-full bg-current" />
    : <span aria-hidden className="h-2 w-2 rounded-full border border-current" />;
  const badge = (
    <motion.span data-testid={testId} data-state={state}
      initial={reduce ? false : { scale: 0.96 }} animate={{ scale: 1 }} transition={{ duration: T.base, ease: EASE, delay: 0.35 }}
      className={`inline-flex items-center gap-1.5 rounded-full border border-line px-2 py-0.5 text-xs font-medium ${tone} ${detail ? "cursor-pointer transition-colors hover:border-line-strong" : ""}`}>
      {mark}
      <motion.span initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: T.base, delay: 0.2 }}>{state}</motion.span>
    </motion.span>
  );
  if (!detail) return badge;
  const rows = ([
    ["Type", detail.kind], ["Source", detail.source], ["Page", detail.page], ["Reporting date", detail.reporting],
    ["Retrieved", detail.retrieved], ["Currency", detail.currency], ["Method", detail.method], ["Reviewer", detail.reviewer],
  ] as [string, React.ReactNode][]).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return (
    <Popover.Root>
      <Popover.Trigger asChild><button type="button" aria-label={`${state}: show details`}>{badge}</button></Popover.Trigger>
      <Popover.Portal>
        <Popover.Content sideOffset={6} align="start" collisionPadding={12} data-testid="verification-detail"
          className="z-50 w-80 max-w-[calc(100vw-24px)] rounded-lg border border-line bg-surface p-4 text-xs text-fg shadow-lg data-[state=open]:animate-[pop_0.18s_ease-out]">
          <div className="mb-2.5 flex items-center gap-1.5 text-sm font-semibold">{mark}{state}</div>
          <dl className="grid grid-cols-[6.5rem_1fr] gap-x-2 gap-y-1.5">
            {rows.map(([k, v]) => <React.Fragment key={k}><dt className="text-muted">{k}</dt><dd className="min-w-0 break-words">{v}</dd></React.Fragment>)}
          </dl>
          {detail.href && <a href={detail.href} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block font-medium underline underline-offset-4">Original source ↗</a>}
          <Popover.Arrow className="fill-[var(--line)]" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
