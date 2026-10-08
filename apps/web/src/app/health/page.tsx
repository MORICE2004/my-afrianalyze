import type { Metadata } from "next";
import React from "react";
import { Empty, Panel, Pill } from "@/components/ui/kit";
import { apiGet, type Health, type RegistrySource } from "@/lib/api";
import { fmtDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Data sources",
  description: "Where AfriEdge's figures come from, and how recently each source was updated.",
};

// Readers' words for each source. The technical states (FAILED, NEVER_RUN, error text) are on the
// administration page only.
const STATE: Record<string, { label: string; tone: "good" | "warn" | "neutral" }> = {
  OK: { label: "Updated", tone: "good" },
  STALE: { label: "Delayed", tone: "warn" },
  PARTIAL: { label: "Partly updated", tone: "warn" },
  FAILED: { label: "Temporarily unavailable", tone: "warn" },
  NEVER_RUN: { label: "Not loaded yet", tone: "neutral" },
  COMING: { label: "Not yet connected", tone: "neutral" },
  NOT_BUILT: { label: "Not yet connected", tone: "neutral" },
};

const LICENCE: Record<string, string> = {
  PUBLIC: "Open data",
  RESTRICTED: "Exchange terms apply",
  LICENSE_REQUIRED: "Needs a licence",
  LICENSE_REVIEW_REQUIRED: "Terms under review",
};

function Row({ r }: { r: RegistrySource }) {
  const s = STATE[r.state] ?? { label: "Unknown", tone: "neutral" as const };
  return (
    <tr>
      <td className="py-3 pr-3">
        <div className="font-medium">{r.name}</div>
        <div className="text-xs text-muted">{r.datasets}</div>
      </td>
      <td className="px-3 py-3 text-xs text-muted">{r.country}</td>
      <td className="px-3 py-3"><Pill tone={s.tone}>{s.label}</Pill></td>
      <td className="px-3 py-3 text-xs text-muted">{r.last_success_at ? fmtDate(r.last_success_at) : "—"}</td>
      <td className="py-3 pl-3 text-xs text-muted">{LICENCE[r.licensing] ?? r.licensing}</td>
    </tr>
  );
}

export default async function DataSourcesPage() {
  const res = await apiGet<Health>("/health");
  if (!res.ok) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">Data sources</h1>
        <Empty title="The data service is not reachable">No figures are shown while it is offline. Please try again shortly.</Empty>
      </div>
    );
  }
  const h = res.data;
  const live = (h.registry ?? []).filter((r) => r.coverage === "V1");
  const planned = (h.registry ?? []).filter((r) => r.coverage !== "V1");
  const overall = h.status === "online" ? { label: "All sources up to date", tone: "good" as const }
    : h.status === "degraded" ? { label: "Some information is delayed", tone: "warn" as const }
    : { label: "Data service unavailable", tone: "warn" as const };
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Data sources</h1>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
          <span data-testid="health-status" data-status={h.status}><Pill tone={overall.tone}>{overall.label}</Pill></span>
          <span>Checked {fmtDate(h.checked_at)}</span>
        </p>
      </header>
      <Panel title="Used today" testId="source-registry">
        <div className="-my-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-line text-xs text-muted">
              <th className="py-2 pr-3 text-left font-medium">Source</th><th className="px-3 py-2 text-left font-medium">Country</th>
              <th className="px-3 py-2 text-left font-medium">Status</th><th className="px-3 py-2 text-left font-medium">Last updated</th>
              <th className="py-2 pl-3 text-left font-medium">Terms</th>
            </tr></thead>
            <tbody className="divide-y divide-line">{live.map((r) => <Row key={r.id} r={r} />)}</tbody>
          </table>
        </div>
      </Panel>
      {planned.length > 0 && (
        <Panel title="Planned">
          <p className="mb-3 text-sm text-muted">Listed so it is clear what is not connected yet. None of their data appears anywhere on the site.</p>
          <div className="-mb-3 overflow-x-auto">
            <table className="w-full text-sm"><tbody className="divide-y divide-line">{planned.map((r) => <Row key={r.id} r={r} />)}</tbody></table>
          </div>
        </Panel>
      )}
      <p className="text-xs text-muted">Prices are end-of-day figures published after each trading session. Company figures come from audited annual reports.</p>
    </div>
  );
}
