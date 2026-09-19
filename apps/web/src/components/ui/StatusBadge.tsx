import React from "react";
import type { DataStatus } from "@/lib/api";

// The data status words from CLAUDE.md, with a plain-language meaning for the tooltip.
export const STATUS_INFO: Record<DataStatus, { meaning: string; cls: string }> = {
  VERIFIED: {
    meaning: "Read the same way by two independent extraction methods and checked against the source page.",
    cls: "border-green-300 bg-green-50 text-green-900",
  },
  PARTIALLY_VERIFIED: {
    meaning: "Read by one method only (for example from the report text). Check the source page before relying on it.",
    cls: "border-sky-300 bg-sky-50 text-sky-900",
  },
  INSUFFICIENT_DATA: {
    meaning: "Not reported, or not enough sourced data to calculate it.",
    cls: "border-neutral-300 bg-neutral-50 text-neutral-600",
  },
  BLOCKED: {
    meaning: "Needs data we do not have the right to use yet (for example licensed exchange prices).",
    cls: "border-red-300 bg-red-50 text-red-900",
  },
  STALE: {
    meaning: "The source is older than the freshness limit set in the configuration.",
    cls: "border-amber-300 bg-amber-50 text-amber-900",
  },
  CONFLICTING_SOURCE: {
    meaning: "Sources, or figures inside one source, disagree. No number is shown until a person resolves it.",
    cls: "border-orange-300 bg-orange-50 text-orange-900",
  },
};

export function statusWord(status: DataStatus): string {
  return status.replace(/_/g, " ");
}

export function StatusBadge({ status, title }: { status: DataStatus; title?: string }) {
  const info = STATUS_INFO[status];
  return (
    <span
      title={title ? `${statusWord(status)}: ${title}` : `${statusWord(status)}: ${info.meaning}`}
      className={`inline-block border px-1.5 py-0.5 text-[10px] leading-none font-mono uppercase tracking-wide whitespace-nowrap cursor-help ${info.cls}`}
      data-status={status}
    >
      {statusWord(status)}
    </span>
  );
}

// A small marker for figures that are shown but only partly verified. Verified figures carry no marker.
export function PartialMarker() {
  return (
    <sup
      className="ml-0.5 text-sky-700 cursor-help font-sans"
      title={`${statusWord("PARTIALLY_VERIFIED")}: ${STATUS_INFO.PARTIALLY_VERIFIED.meaning}`}
      data-status="PARTIALLY_VERIFIED"
    >
      PV
    </sup>
  );
}

export function StatusLegend() {
  return (
    <p className="text-xs text-neutral-500 flex flex-wrap items-center gap-x-3 gap-y-1">
      <span>Every number shown is VERIFIED unless marked</span>
      <span className="inline-flex items-center gap-1"><span className="text-sky-700 font-semibold">PV</span> = partly verified</span>
      <span>Missing figures show their status:</span>
      {(["CONFLICTING_SOURCE", "INSUFFICIENT_DATA", "BLOCKED", "STALE"] as const).map((s) => <StatusBadge key={s} status={s} />)}
    </p>
  );
}
