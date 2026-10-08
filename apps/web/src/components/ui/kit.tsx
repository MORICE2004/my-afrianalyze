"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import React from "react";
import { direction, fmtSignedPct } from "@/lib/format";

type Num = number | string;

// A surface with a quiet border. Used for every block on a page, so spacing and weight stay consistent.
export function Panel({ title, action, children, className = "", testId, id }: {
  title?: React.ReactNode; action?: React.ReactNode; children: React.ReactNode; className?: string;
  testId?: string; id?: string;
}) {
  return (
    <section id={id} data-testid={testId} className={`rounded-xl border border-line bg-surface ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
          {title && <h2 className="text-sm font-semibold text-fg">{title}</h2>}
          {action}
        </div>
      )}
      <div className="p-4 sm:p-5">{children}</div>
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

// Shown where data cannot be shown, saying why in plain words. Never "No data." or "Error."
export function Empty({ title, children, testId }: { title: string; children?: React.ReactNode; testId?: string }) {
  return (
    <div data-testid={testId} className="rounded-lg border border-dashed border-line-strong bg-surface-2/40 px-4 py-5 text-sm">
      <div className="font-medium text-fg">{title}</div>
      {children && <div className="mt-1 text-muted">{children}</div>}
    </div>
  );
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
