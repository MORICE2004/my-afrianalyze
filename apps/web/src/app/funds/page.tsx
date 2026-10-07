import type { Metadata } from "next";
import React from "react";
import { ExternalSource } from "@/components/report/SourceLink";
import { ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import { apiGet } from "@/lib/api";

export const metadata: Metadata = {
  title: "Unit trusts",
  description: "Tanzanian unit trusts, from their manager's own pages. Figures are shown only when their use is cleared.",
};

type Fund = {
  id: string; name: string; manager_name: string; currency: string; product_page: string; reports_page: string;
  licensing: string; figures: Record<string, { available: boolean; status?: string; reason?: string; value?: string }>;
};

export default async function FundsPage() {
  const res = await apiGet<{ funds: Fund[]; note: string }>("/api/v1/funds");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Unit trusts (Tanzania)</h1>
      {!res.ok ? <ErrorState message={res.error} /> : (
        <>
          <p className="text-sm text-neutral-700">
            The funds below are listed by their manager. Their prices (NAV), performance, fees and holdings are published
            by the manager, but its site states no terms for reusing them, so AfriEdge does not show them yet. No figure
            here is estimated.
          </p>
          <div className="overflow-x-auto border border-neutral-200 bg-white">
            <table className="w-full text-sm" data-testid="funds">
              <thead className="bg-neutral-50 text-xs text-neutral-500">
                <tr><th className="text-left px-3 py-2">Fund</th><th className="text-left px-3 py-2">Manager</th>
                  <th className="text-left px-3 py-2">NAV per unit</th><th className="text-left px-3 py-2">Manager&apos;s pages</th></tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {res.data.funds.map((f) => (
                  <tr key={f.id}>
                    <td className="px-3 py-2 font-medium">{f.name} <span className="text-xs text-neutral-500">{f.currency}</span></td>
                    <td className="px-3 py-2 text-xs">{f.manager_name}</td>
                    <td className="px-3 py-2">
                      {f.figures.nav_per_unit?.available ? f.figures.nav_per_unit.value
                        : <NotAvailable compact reason={f.figures.nav_per_unit?.reason ?? ""} />}
                      <span className="block text-[11px] font-mono text-neutral-500">{f.licensing}</span>
                    </td>
                    <td className="px-3 py-2 text-xs space-x-2">
                      <ExternalSource href={f.product_page}>Product</ExternalSource>
                      <ExternalSource href={f.reports_page}>Reports</ExternalSource>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
