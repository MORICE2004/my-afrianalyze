"use client";

import Link from "next/link";
import React from "react";
import * as Popover from "@radix-ui/react-popover";
import { ProBadge } from "@/components/ui/kit";
import { useToast } from "@/components/ui/Toast";
import { useAccount } from "@/lib/account";
import { API_URL } from "@/lib/api";

// PDF for everyone; the Excel analyst workbook for Pro. The button's state only explains what the reader can do:
// the API refuses the workbook to any account without the entitlement, whatever this page shows.
export function ExportButtons({ securityId }: { securityId: string }) {
  const { status, user } = useAccount();
  const toast = useToast();
  const pro = !!user?.features.includes("excel_export");
  const btn = "inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium transition-colors hover:bg-surface-2";
  return (
    <div className="flex flex-wrap items-center gap-2 no-print">
      <a href={`${API_URL}/api/v1/reports/${encodeURIComponent(securityId)}/pdf`} className={btn} data-testid="download-pdf"
        onClick={() => toast("Preparing the PDF report…")}>
        PDF report
      </a>
      {pro ? (
        <a href={`/api/export/${encodeURIComponent(securityId)}`} className={btn} data-testid="export-excel"
          onClick={() => toast("Exporting the research workbook…")}>
          Export to Excel
        </a>
      ) : (
        <Popover.Root>
          <Popover.Trigger asChild>
            <button type="button" className={btn} data-testid="export-excel-locked" disabled={status === "loading"}>
              Export to Excel
            </button>
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content align="end" sideOffset={8} data-testid="pro-explainer"
              className="z-50 w-80 rounded-lg border border-line bg-surface p-4 text-sm shadow-lg data-[state=open]:animate-[pop_0.18s_ease-out]">
              <div className="flex items-center gap-2 font-semibold">Research workbook <ProBadge /></div>
              <p className="mt-1 text-xs text-muted">Available with AfriEdge Pro: the full research for this company as an Excel workbook, ready for your own model.</p>
              <ul className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                {["13 sheets", "Financial statements", "Ratios", "Valuation", "Sensitivity", "Technical analysis", "Risk", "Every figure's source"].map((b) => (
                  <li key={b} className="flex items-center gap-1.5"><span aria-hidden className="h-1 w-1 rounded-full bg-fg" />{b}</li>
                ))}
              </ul>
              <p className="mt-3 border-t border-line pt-2 text-xs text-muted">
                {user ? "Your account is on the Free plan. Pro is enabled by AfriEdge for now; there is no online checkout yet." :
                  <><Link href="/login" className="font-medium text-fg underline underline-offset-4">Sign in</Link> to check your plan.</>}
              </p>
              <Popover.Arrow className="fill-[var(--line)]" />
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      )}
    </div>
  );
}
