"use client";

import * as Popover from "@radix-ui/react-popover";
import React from "react";
import { statusWord } from "@/components/ui/StatusBadge";
import Link from "next/link";
import type { DataStatus, DocRef } from "@/lib/api";
import { fmtDate } from "@/lib/format";

// Click (or press Enter on) a figure to see where it came from: document, page, period, currency, how it was
// read and its validation status, then open the source itself.
export function EvidenceCell({ source, children, method, status, period, currency, asReported, column }: {
  source: DocRef; children: React.ReactNode; method?: string; status?: DataStatus; period?: string;
  currency?: string; asReported?: string; column?: string;
}) {
  const rows: [string, React.ReactNode][] = [
    ["Document", source.title],
    ["Page", source.page ?? "Not recorded"],
    ...(period ? [["Period", `Year ending ${fmtDate(period)}`] as [string, React.ReactNode]] : []),
    ...(currency ? [["Currency", currency] as [string, React.ReactNode]] : []),
    ...(asReported ? [["As printed", `“${asReported}”${column ? ` (${column} column)` : ""}`] as [string, React.ReactNode]] : []),
    ...(method ? [["Read by", method.replace("+", " and ")] as [string, React.ReactNode]] : []),
    ["Validation", status ? statusWord(status) : "VERIFIED"],
    ["Retrieved", fmtDate(source.retrieved_at)],
  ];
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" data-source-page={source.page ?? ""}
          className="cursor-pointer rounded-sm text-right underline decoration-line-strong decoration-dotted underline-offset-4 hover:decoration-fg">
          {children}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content sideOffset={6} collisionPadding={12} data-testid="evidence-card"
          className="z-50 w-80 max-w-[calc(100vw-24px)] rounded-lg border border-line bg-surface p-4 text-left text-xs shadow-xl">
          <div className="mb-2 text-sm font-semibold text-fg">Source</div>
          <dl className="grid grid-cols-[88px_1fr] gap-x-3 gap-y-1.5">
            {rows.map(([k, v]) => (
              <React.Fragment key={k}>
                <dt className="text-muted">{k}</dt>
                <dd className="min-w-0 break-words text-fg">{v}</dd>
              </React.Fragment>
            ))}
          </dl>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {source.viewer_url && (
              <Link href={source.viewer_url} data-testid="view-source-page"
                className="inline-flex items-center rounded-md bg-selected px-3 py-1.5 text-xs font-medium text-on-selected hover:opacity-90">
                View {source.page ? `page ${source.page}` : "document"}
              </Link>
            )}
            {source.url && (
              <a href={source.url.split(" ")[0]} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-fg underline underline-offset-4">
                Original publication ↗
              </a>
            )}
          </div>
          <Popover.Arrow className="fill-[var(--line)]" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
