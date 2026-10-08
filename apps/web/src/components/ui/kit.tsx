"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import React from "react";
import { direction, fmtSignedPct } from "@/lib/format";

type Num = number | string;

// A section of a page: a heading on a hairline rule, then content. No box around it; hierarchy comes from type,
// spacing and dividers, so pages do not turn into a wall of rounded cards. `boxed` keeps a surface for the few
// blocks that need one (a chart over a tinted page, a form).
export function Panel({ title, action, children, className = "", testId, id, boxed = false }: {
  title?: React.ReactNode; action?: React.ReactNode; children: React.ReactNode; className?: string;
  testId?: string; id?: string; boxed?: boolean;
}) {
  return (
    <section id={id} data-testid={testId}
      className={`min-w-0 ${boxed ? "rounded-lg border border-line bg-surface p-4 sm:p-5" : "border-t border-line pt-3"} ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-center justify-between gap-3">
          {title && <h2 className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">{title}</h2>}
          {action}
        </div>
      )}
      <div>{children}</div>
    </section>
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return <div className="text-xs font-medium text-muted">{children}</div>;
}

// A signed change. Colour always comes with a sign and an arrow, so it reads without colour too.
export function Change({ value, digits = 2, className = "", label }: {
  value: Num | null | undefined; digits?: number; className?: string; label?: string;
}) {
  const d = direction(value);
  if (value === null || value === undefined) return <span className={`text-faint ${className}`}>—</span>;
  const cls = d === "pos" ? "text-pos" : d === "neg" ? "text-neg" : "text-muted";
  const arrow = d === "pos" ? "▲" : d === "neg" ? "▼" : "";
  return (
    <span className={`whitespace-nowrap ${cls} ${className}`} aria-label={label ? `${label} ${fmtSignedPct(Number(value), digits)}` : undefined}>
      {arrow && <span aria-hidden className="mr-0.5 text-[0.7em]">{arrow}</span>}
      {fmtSignedPct(Number(value), digits)}
    </span>
  );
}

// Plain words for readers; the technical detail sits in the tooltip.
export function Hint({ content, children }: { content: React.ReactNode; children: React.ReactNode }) {
  return (
    <Tooltip.Provider delayDuration={150}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content sideOffset={6} className="z-50 max-w-xs rounded-md border border-line bg-surface px-3 py-2 text-xs leading-relaxed text-fg shadow-lg">
            {content}
            <Tooltip.Arrow className="fill-[var(--line)]" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}

const TONES = {
  good: "bg-pos-bg text-pos",
  warn: "bg-warn-bg text-warn",
  bad: "bg-neg-bg text-neg",
  neutral: "bg-surface-2 text-muted",
};

// A short state word for readers ("Updated", "Delayed", "Limited data"), with its reason on hover or focus.
export function Pill({ tone = "neutral", children, hint, testId }: {
  tone?: keyof typeof TONES; children: React.ReactNode; hint?: React.ReactNode; testId?: string;
}) {
  const pill = (
    <span tabIndex={hint ? 0 : undefined} data-testid={testId}
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${TONES[tone]} ${hint ? "cursor-help" : ""}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {children}
    </span>
  );
  return hint ? <Hint content={hint}>{pill}</Hint> : pill;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />;
}

// Shown where data cannot be shown: what is missing, in plain words, and what the reader can do next.
// Never "No data." or "Error."
export function Empty({ title, children, testId, action }: {
  title: string; children?: React.ReactNode; testId?: string; action?: { label: string; href?: string; onClick?: () => void };
}) {
  return (
    <div data-testid={testId} className="rounded-lg bg-surface-2/60 px-4 py-4 text-sm">
      <div className="font-medium text-fg">{title}</div>
      {children && <div className="mt-1 max-w-prose text-muted">{children}</div>}
      {action && <NextAction {...action} />}
    </div>
  );
}

export function NextAction({ label, href, onClick }: { label: string; href?: string; onClick?: () => void }) {
  const cls = "mt-3 inline-flex h-8 items-center rounded-md border border-line-strong bg-surface px-3 text-sm font-medium text-fg transition-colors hover:bg-surface-2";
  return href ? <a href={href} className={cls}>{label} →</a> : <button type="button" onClick={onClick} className={cls}>{label}</button>;
}

export function Stat({ label, value, sub, testId }: { label: string; value: React.ReactNode; sub?: React.ReactNode; testId?: string }) {
  return (
    <div data-testid={testId} className="min-w-0">
      <Label>{label}</Label>
      <div className="mt-1 truncate text-lg font-semibold text-fg sm:text-xl">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export function ProBadge() {
  return <span className="rounded border border-line-strong px-1.5 py-px text-[10px] font-semibold uppercase tracking-wide text-fg">Pro</span>;
}
