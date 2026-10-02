import type { Metadata } from "next";
import React from "react";
import { ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type Health, type RegistrySource, type RegistryState } from "@/lib/api";
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
          {res.data.registry && <SourceRegistry rows={res.data.registry} />}
        </>
      )}
    </div>
  );
}

const STATE_CLS: Record<RegistryState, string> = {
  OK: "bg-green-100 text-green-900", STALE: "bg-amber-100 text-amber-900", PARTIAL: "bg-amber-100 text-amber-900",
  FAILED: "bg-red-100 text-red-900", NEVER_RUN: "bg-neutral-100 text-neutral-700",
  COMING: "bg-neutral-100 text-neutral-700", NOT_BUILT: "bg-neutral-100 text-neutral-700",
};

// Every source AfriEdge covers or plans to cover. A source marked COMING has no loader yet, so it has no
// "last success" to show; that is the point of listing it.
function SourceRegistry({ rows }: { rows: RegistrySource[] }) {
  return (
    <section className="space-y-3" data-testid="source-registry">
      <h2 className="text-lg font-semibold">All sources</h2>
      <p className="text-sm text-neutral-600">
        Tanzania is live. Kenya, Uganda and the global macro sources are planned: they are shown here so it is clear
        what is not integrated yet, and none of their data appears anywhere on the site.
      </p>
      <div className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-xs text-neutral-500">
            <tr>
              <th className="text-left px-3 py-2">Source</th><th className="text-left px-3 py-2">State</th>
              <th className="text-left px-3 py-2">Last success</th><th className="text-left px-3 py-2">Last failure</th>
              <th className="text-left px-3 py-2">Licensing</th><th className="text-left px-3 py-2">Loader</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="px-3 py-2"><div className="font-medium">{r.name}</div>
                  <div className="text-xs text-neutral-500">{r.country} · {r.datasets}</div></td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 text-xs font-semibold ${STATE_CLS[r.state]}`}>{r.state.replace("_", " ")}</span></td>
                <td className="px-3 py-2 text-xs">{r.last_success_at ? fmtDate(r.last_success_at) : "None"}</td>
                <td className="px-3 py-2 text-xs">{r.last_failure_at ? fmtDate(r.last_failure_at) : "None recorded"}</td>
                <td className="px-3 py-2 text-xs"><span className="font-mono">{r.licensing}</span>
                  {r.licensing_note && <div className="text-neutral-500">{r.licensing_note}</div>}</td>
                <td className="px-3 py-2 text-xs">{r.parser_state === "IMPLEMENTED" ? "Built" : "Not built"}
                  {r.probe && <div className="text-neutral-500">Probe {r.probe.checked_at}: {r.probe.result}{r.probe.detail ? ` (${r.probe.detail})` : ""}</div>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
