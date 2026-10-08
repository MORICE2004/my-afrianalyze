"use client";

import Link from "next/link";
import React, { useState } from "react";
import { ProBadge } from "@/components/ui/kit";
import { useAccount } from "@/lib/account";
import { API_URL } from "@/lib/api";

// PDF for everyone; the Excel analyst workbook for Pro. The button's state only explains what the reader can do:
// the API refuses the workbook to any account without the entitlement, whatever this page shows.
export function ExportButtons({ securityId }: { securityId: string }) {
  const { status, user } = useAccount();
  const [explain, setExplain] = useState(false);
  const pro = !!user?.features.includes("excel_export");
  const btn = "inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-surface-2";
  return (
    <div className="relative flex flex-wrap items-center gap-2 no-print">
      <a href={`${API_URL}/api/v1/reports/${encodeURIComponent(securityId)}/pdf`} className={btn} data-testid="download-pdf">
        PDF report
      </a>
      {pro ? (
        <a href={`/api/export/${encodeURIComponent(securityId)}`} className={btn} data-testid="export-excel">
          Export to Excel <ProBadge />
        </a>
      ) : (
        <button type="button" className={`${btn} text-muted`} data-testid="export-excel-locked" aria-expanded={explain}
          disabled={status === "loading"} onClick={() => setExplain((e) => !e)}>
          Export to Excel <ProBadge />
        </button>
      )}
      {explain && !pro && (
        <div role="status" className="absolute right-0 top-11 z-30 w-72 rounded-lg border border-line bg-surface p-3 text-xs shadow-lg">
          <p className="font-medium text-fg">The analyst workbook is part of AfriEdge Pro.</p>
          <p className="mt-1 text-muted">
            Thirteen sheets: statements, ratios, valuation and its assumptions, sensitivity, technicals, risks and every
            figure&apos;s source.{" "}
            {user ? "Your account is on the Free plan." : <><Link href="/login" className="underline">Sign in</Link> to check your plan.</>}
          </p>
        </div>
      )}
    </div>
  );
}
