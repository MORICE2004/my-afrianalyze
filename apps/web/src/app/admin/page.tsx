"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Empty, Panel } from "@/components/ui/kit";
import type { Health, RegistrySource } from "@/lib/api";
import { fmtDate } from "@/lib/format";

type Provider = { id: string; name: string; state: string; state_reason: string; licensing: string; coverage: string[]; note: string; credential_env: string | null };
type Recon = { instrument_id: string; trade_date: string; currency: string; provider_a: string; close_a: string; provider_b: string; close_b: string; difference_pct: string; status: string; checked_at: string };
type NewsSource = { id: string; name: string; tier: number; state: string; status: string | null; fresh: boolean | null;
  last_success_at: string | null; last_attempt_at: string | null; detail: string | null; terms_note: string | null };
type AdminHealth = Health & { news_sources: NewsSource[]; providers: Provider[]; priority_setting: string | null; reconciliations: Recon[]; refresh_schedule: string };

// The administrator's states for a source (launch directive item 25). Readers never see these words.
function adminState(r: RegistrySource): string {
  if (r.state === "OK") return "HEALTHY";
  if (r.state === "STALE") return "STALE";
  if (r.state === "PARTIAL" || r.state === "FAILED") return "DEGRADED";
  if (["LICENSE_REQUIRED", "LICENSE_REVIEW_REQUIRED"].includes(r.licensing)) return "LICENSE_REVIEW_REQUIRED";
  return "BLOCKED";
}

const CLS: Record<string, string> = {
  HEALTHY: "bg-pos-bg text-pos", READY: "bg-pos-bg text-pos", DEGRADED: "bg-warn-bg text-warn", STALE: "bg-warn-bg text-warn",
  BLOCKED: "bg-neg-bg text-neg", NOT_CONFIGURED: "bg-surface-2 text-muted", LICENSE_REVIEW_REQUIRED: "bg-warn-bg text-warn",
  MATCH: "bg-pos-bg text-pos", CONFLICTING_SOURCE: "bg-neg-bg text-neg",
};

function Word({ s }: { s: string }) {
  return <span className={`whitespace-nowrap rounded px-1.5 py-0.5 font-mono text-[11px] ${CLS[s] ?? "bg-surface-2 text-muted"}`}>{s}</span>;
}

export default function AdminPage() {
  const [data, setData] = useState<AdminHealth | null>(null);
  const [error, setError] = useState<{ status: number; detail: string } | null>(null);

  useEffect(() => {
    fetch("/api/admin/data-health", { cache: "no-store" })
      .then(async (r) => (r.ok ? setData(await r.json()) : setError({ status: r.status, detail: (await r.json().catch(() => ({})))?.detail ?? "" })))
      .catch(() => setError({ status: 503, detail: "The data service is not reachable." }));
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">Data administration</h1>
        <Empty title={error.status === 401 ? "Sign in to continue" : error.status === 403 ? "Administrators only" : "Not available"} testId="admin-refused">
          {error.status === 401 ? <Link href="/login" className="underline">Sign in</Link> : error.detail}
        </Empty>
      </div>
    );
  }
  if (!data) return <div className="space-y-4"><div className="skeleton h-8 w-64" /><div className="skeleton h-64" /></div>;

  const rows = new Map(data.sources.map((s) => [s.source, s]));
  return (
    <div className="space-y-6" data-testid="admin">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Data administration</h1>
        <p className="mt-1 text-sm text-muted">Checked {fmtDate(data.checked_at)} · database {data.database.ok ? "reachable" : "unreachable"} · {data.summary} · refresh: {data.refresh_schedule}</p>
      </header>

      <Panel title="Sources">
        <div className="-m-4 overflow-x-auto sm:-m-5">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-line text-xs text-muted">
              {["Source", "State", "Last success", "Last failure", "Licensing", "Detail"].map((h) => <th key={h} className="px-3 py-2 text-left font-medium first:pl-5">{h}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-line">
              {(data.registry ?? []).map((r) => (
                <tr key={r.id} className="align-top">
                  <td className="py-2.5 pl-5 pr-3"><div className="font-medium">{r.name}</div><div className="text-xs text-muted">{r.country} · loader {r.parser_state === "IMPLEMENTED" ? "built" : "not built"}</div></td>
                  <td className="px-3 py-2.5"><Word s={adminState(r)} /></td>
                  <td className="px-3 py-2.5 text-xs">{r.last_success_at ? fmtDate(r.last_success_at) : "never"}</td>
                  <td className="px-3 py-2.5 text-xs">{r.last_failure_at ? fmtDate(r.last_failure_at) : "none"}</td>
                  <td className="px-3 py-2.5 text-xs"><span className="font-mono">{r.licensing}</span><div className="text-muted">{r.licensing_note}</div></td>
                  <td className="px-3 py-2.5 text-xs text-muted">{r.probe ? `Probe ${r.probe.checked_at}: ${r.probe.result}` : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Loader records">
        <div className="-m-4 overflow-x-auto sm:-m-5">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-line text-xs text-muted">
              {["Record", "Status", "Fresh", "Last success", "Age / limit", "Detail"].map((h) => <th key={h} className="px-3 py-2 text-left font-medium first:pl-5">{h}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-line">
              {[...rows.values()].map((s) => (
                <tr key={s.source} className="align-top">
                  <td className="py-2.5 pl-5 pr-3 font-mono text-xs">{s.source}</td>
                  <td className="px-3 py-2.5 font-mono text-xs">{s.status}</td>
                  <td className="px-3 py-2.5 text-xs">{s.fresh ? "yes" : "no"}</td>
                  <td className="px-3 py-2.5 text-xs">{s.last_success_at ? fmtDate(s.last_success_at) : "never"}</td>
                  <td className="px-3 py-2.5 text-xs">{s.age_hours ?? "—"} h / {s.max_age_hours} h</td>
                  <td className="px-3 py-2.5 text-xs text-muted">{s.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid items-start gap-5 lg:grid-cols-2">
        <Panel title="Market-data providers">
          <p className="mb-3 text-xs text-muted">Priority: {data.priority_setting ?? "default order (config/market_data.json)"}. A provider is used only when it is READY.</p>
          <ul className="space-y-3 text-sm">
            {data.providers.map((p, i) => (
              <li key={p.id} className="border-l-2 border-line pl-3">
                <div className="flex flex-wrap items-center gap-2"><span className="text-xs text-muted">{i + 1}.</span><span className="font-medium">{p.name}</span><Word s={p.state} /><span className="font-mono text-[11px] text-muted">{p.licensing}</span></div>
                <div className="text-xs text-muted">{p.coverage.join(", ")}{p.state_reason ? ` · ${p.state_reason}` : ""}</div>
                <div className="mt-1 text-xs text-muted">{p.note}</div>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Provider reconciliation">
          {data.reconciliations.length === 0 ? (
            <p className="text-sm text-muted">No comparisons recorded: only one provider is usable. Run <span className="font-mono">python -m pipelines.reconcile_prices</span> once a second provider is configured.</p>
          ) : (
            <ul className="divide-y divide-line text-xs">
              {data.reconciliations.map((r) => (
                <li key={`${r.instrument_id}-${r.trade_date}-${r.checked_at}`} className="flex flex-wrap justify-between gap-2 py-2">
                  <span>{r.instrument_id} {r.trade_date}</span>
                  <span>{r.provider_a} {r.close_a} vs {r.provider_b} {r.close_b} ({(Number(r.difference_pct) * 100).toFixed(2)}%)</span>
                  <Word s={r.status} />
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <Panel title="News sources" testId="admin-news">
        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable table">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-muted"><th className="py-2 pr-3 font-medium">Source</th><th className="py-2 pr-3 font-medium">Tier</th><th className="py-2 pr-3 font-medium">State</th><th className="py-2 pr-3 font-medium">Last success</th><th className="py-2 font-medium">Detail / terms</th></tr></thead>
            <tbody className="divide-y divide-line">
              {(data.news_sources ?? []).map((n) => (
                <tr key={n.id} className="align-top">
                  <td className="py-2 pr-3 font-medium">{n.name}</td>
                  <td className="py-2 pr-3">{n.tier}</td>
                  <td className="py-2 pr-3"><Word s={n.state !== "CONNECTED" ? n.state : n.status === "failed" ? "ERROR" : n.fresh ? "OK" : "STALE"} /></td>
                  <td className="py-2 pr-3 text-xs text-muted">{n.last_success_at ? new Date(n.last_success_at).toLocaleString("en-GB") : "never"}</td>
                  <td className="py-2 text-xs text-muted">{n.detail ? <span className="block text-fg">{n.detail}</span> : null}{n.terms_note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
