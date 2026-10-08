"use client";

import React from "react";
import { ProBadge } from "@/components/ui/kit";
import { useToast } from "@/components/ui/Toast";
import { useAccount } from "@/lib/account";

// Exports exist only for accounts whose plan includes them (Pro: the PDF report and the Excel workbook). Every
// other reader has a view-only page with no export control. The API enforces the same rule on every request.
export function ExportButtons({ securityId }: { securityId: string }) {
  const { user } = useAccount();
  const toast = useToast();
  if (!user?.features.includes("excel_export")) return null;
  const id = encodeURIComponent(securityId);
  const btn = "inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium transition-colors hover:bg-surface-2";
  return (
    <div className="flex flex-wrap items-center gap-2 no-print" data-testid="exports">
      <ProBadge />
      <a href={`/api/export/${id}?format=pdf`} className={btn} data-testid="download-pdf" onClick={() => toast("Preparing the PDF report…")}>PDF report</a>
      <a href={`/api/export/${id}`} className={btn} data-testid="export-excel" onClick={() => toast("Exporting the research workbook…")}>Export to Excel</a>
    </div>
  );
}
