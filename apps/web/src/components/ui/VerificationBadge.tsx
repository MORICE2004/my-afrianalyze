"use client";

import * as Popover from "@radix-ui/react-popover";
import React from "react";
import { VerifiedCheck } from "@/components/motion/primitives";

// The one trust indicator used across AfriEdge. It is a statement about checking, not decoration, so it is
// quiet: only "Verified" and "Reviewed" carry a mark, and green is kept for price direction elsewhere.
export type Verification = "Verified" | "Reviewed" | "Updated" | "Stale" | "Limited" | "Unavailable";

const STYLE: Record<Verification, string> = {
  Verified: "text-fg", Reviewed: "text-fg", Updated: "text-muted",
  Stale: "text-warn", Limited: "text-warn", Unavailable: "text-faint",
};

export type Provenance = { source?: string; page?: string | number; retrieved?: string; currency?: string;
  period?: string; validation?: string; href?: string };

export function VerificationBadge({ state, detail, testId }: { state: Verification; detail?: Provenance; testId?: string }) {
  const mark = state === "Verified" ? <VerifiedCheck size={13} />
    : state === "Reviewed" ? <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />
    : <span aria-hidden className="h-1.5 w-1.5 rounded-full border border-current" />;
  const badge = (
    <span data-testid={testId} data-state={state}
      className={`inline-flex items-center gap-1 text-xs font-medium ${STYLE[state]} ${detail ? "cursor-pointer underline-offset-4 hover:underline" : ""}`}>
      {mark}{state}
    </span>
  );
  if (!detail) return badge;
  const rows: [string, React.ReactNode][] = [
    ["Source", detail.source], ["Page", detail.page], ["Period", detail.period], ["Currency", detail.currency],
    ["Retrieved", detail.retrieved], ["Validation", detail.validation],
  ].filter(([, v]) => v !== undefined && v !== null && v !== "") as [string, React.ReactNode][];
  return (
    <Popover.Root>
      <Popover.Trigger asChild><button type="button" aria-label={`${state}: show source`}>{badge}</button></Popover.Trigger>
      <Popover.Portal>
        <Popover.Content sideOffset={6} align="start"
          className="z-50 w-72 rounded-lg border border-line bg-surface p-3 text-xs text-fg shadow-lg data-[state=open]:animate-[pop_0.18s_ease-out]">
          <div className="mb-2 flex items-center gap-1.5 font-semibold">{mark}{state}</div>
          <dl className="grid grid-cols-[5.5rem_1fr] gap-x-2 gap-y-1">
            {rows.map(([k, v]) => <React.Fragment key={k}><dt className="text-muted">{k}</dt><dd>{v}</dd></React.Fragment>)}
          </dl>
          {detail.href && <a href={detail.href} target="_blank" rel="noreferrer" className="mt-2 inline-block underline underline-offset-4">Open source →</a>}
          <Popover.Arrow className="fill-[var(--line)]" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
