import type { Metadata } from "next";
import React from "react";
import { ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type Health } from "@/lib/api";
import { fmtDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Data health",
  description: "Live status of the database and each data source, including stale and blocked sources.",
};

const BADGE: Record<string, string> = {
  online: "bg-green-100 text-green-900", degraded: "bg-amber-100 text-amber-900", offline: "bg-red-100 text-red-900",
};

export default async function HealthPage() {
  const res = await apiGet<Health>("/health");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Data health</h1>
      {!res.ok ? (
        <>
          <p><span className={`px-2 py-1 text-sm font-semibold ${BADGE.offline}`}>Offline</span></p>
          <ErrorState message={res.error} />
        </>
      ) : (
        <>
          <p>
            <span className={`px-2 py-1 text-sm font-semibold capitalize ${BADGE[res.data.status]}`} data-testid="health-status">
              {res.data.status}
            </span>
            <span className="ml-3 text-sm text-neutral-600">
              Checked {fmtDate(res.data.checked_at)} · database {res.data.database.ok ? "reachable" : "unreachable"} · {res.data.summary}
            </span>
          </p>
          <div className="overflow-x-auto border border-neutral-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-xs text-neutral-500">
                <tr><th className="text-left px-3 py-2">Source</th><th className="text-left px-3 py-2">Status</th><th className="text-left px-3 py-2">Last success</th><th className="text-left px-3 py-2">Detail</th></tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {res.data.sources.map((s) => (
                  <tr key={s.source}>
                    <td className="px-3 py-2 font-mono">{s.source}</td>
                    <td className="px-3 py-2">{s.fresh ? "Fresh" : s.status === "blocked" ? "Blocked" : s.status === "ok" ? "Stale" : "Failed or stale"}</td>
                    <td className="px-3 py-2 text-xs">{s.last_success_at ? `${fmtDate(s.last_success_at)} (${s.age_hours} h ago; limit ${s.max_age_hours} h)` : "Never"}</td>
                    <td className="px-3 py-2 text-xs text-neutral-600">{s.detail}</td>
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
