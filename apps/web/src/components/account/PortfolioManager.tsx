"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";
import { PortfolioAnalysis } from "@/components/account/PortfolioAnalysis";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState, ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type DataStatus } from "@/lib/api";
import { fmtDate, fmtPct, fmtPerShare } from "@/lib/format";

// Every figure here is calculated by the API from the stored close (Decimal, sent as a string). This
// component only formats; it never does financial arithmetic of its own.

type Price =
  | { available: true; value: string; date: string; status: DataStatus; source_document_id: number; attribution?: string }
  | { available: false; status: DataStatus; reason: string };

interface Holding {
  security_id: string; name: string; quantity: string; cost_per_share: string | null;
  price: Price; market_value?: string; weight?: string; cost_value?: string; gain?: string;
}

type TotalStatus = DataStatus | "PARTIAL" | "NO_DATA";

interface Portfolio {
  id: number; name: string; base_currency: string; created_at: string | null; holdings: Holding[];
  totals: { status: TotalStatus; market_value: string | null; priced_holdings: number;
            unpriced_holdings: string[]; stale_prices: string[]; largest_weight: string | null; note: string };
}

interface SecurityOption { id: string; name: string; currency: string }

type Load =
  | { state: "loading" }
  | { state: "signed_out" }
  | { state: "error"; message: string }
  | { state: "ready"; portfolios: Portfolio[] };

const TOTAL_WORD: Record<"PARTIAL" | "NO_DATA", string> = {
  PARTIAL: "Some holdings have no stored price; totals cover the priced ones only.",
  NO_DATA: "No holdings yet.",
};

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  const d = body?.detail;
  return Array.isArray(d) ? d.map((x: { msg: string }) => x.msg).join(". ") : d ?? `Request failed (${res.status})`;
}

export function PortfolioManager() {
  const router = useRouter();
  const [load, setLoad] = useState<Load>({ state: "loading" });
  const [email, setEmail] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      // Ask who is signed in first, so a signed-out visit makes no request that is bound to fail.
      const me = await fetch("/api/session/me");
      if (!me.ok) return setLoad({ state: "error", message: await readError(me) });
      const user = (await me.json()).user as { email: string } | null;
      if (!user) return setLoad({ state: "signed_out" });
      setEmail(user.email);
      const res = await fetch("/api/portfolios");
      if (res.status === 401) return setLoad({ state: "signed_out" });
      if (!res.ok) return setLoad({ state: "error", message: await readError(res) });
      setLoad({ state: "ready", portfolios: (await res.json()).portfolios });
    } catch {
      setLoad({ state: "error", message: "The site could not be reached." });
    }
  }, []);

  useEffect(() => {
    // Loading data on mount is what this effect is for; the state updates happen after the awaits.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  async function signOut() {
    await fetch("/api/session/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  async function remove(id: number) {
    if (!window.confirm("Delete this portfolio? This cannot be undone.")) return;
    const res = await fetch(`/api/portfolios/${id}`, { method: "DELETE" });
    if (!res.ok) window.alert(await readError(res));
    void refresh();
  }

  if (load.state === "loading") return <p className="text-sm text-neutral-500" aria-live="polite">Loading your portfolios…</p>;
  if (load.state === "error") return <ErrorState message={load.message} />;
  if (load.state === "signed_out")
    return (
      <EmptyState title="Sign in to see your portfolios">
        Portfolios belong to one account and are shown only to it.{" "}
        <Link href="/login" className="underline font-semibold">Sign in or create an account</Link>.
      </EmptyState>
    );

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <span className="text-neutral-600">Signed in{email ? ` as ${email}` : ""}.</span>
        <button type="button" onClick={signOut} className="border border-neutral-300 px-3 py-1.5 font-semibold">
          Sign out
        </button>
      </div>

      {load.portfolios.length === 0 ? (
        <EmptyState title="No saved portfolios">Create one below. Values come from the latest stored DSE close.</EmptyState>
      ) : (
        load.portfolios.map((p) => <PortfolioCard key={p.id} p={p} onDelete={() => remove(p.id)} />)
      )}

      <CreatePortfolio onCreated={refresh} />
    </div>
  );
}

function PortfolioCard({ p, onDelete }: { p: Portfolio; onDelete: () => void }) {
  const t = p.totals;
  const [analyse, setAnalyse] = useState(false);
  return (
    <section className="border border-neutral-200 bg-white" data-testid="portfolio-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 px-4 py-3">
        <div>
          <h2 className="font-semibold">{p.name}</h2>
          <p className="text-xs text-neutral-500">{p.base_currency}{p.created_at ? ` · created ${fmtDate(p.created_at)}` : ""}</p>
        </div>
        <div className="flex items-center gap-3">
          {t.status === "PARTIAL" || t.status === "NO_DATA"
            ? <span className="text-xs font-semibold uppercase text-amber-800 bg-amber-50 px-2 py-1">{t.status.replace("_", " ")}</span>
            : <StatusBadge status={t.status} />}
          <button type="button" onClick={() => setAnalyse((x) => !x)} className="text-xs underline" aria-expanded={analyse}>
            {analyse ? "Hide analysis" : "Analyse"}
          </button>
          <button type="button" onClick={onDelete} className="text-xs text-red-700 underline">Delete</button>
        </div>
      </header>
      {p.holdings.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="px-4 py-2">Security</th><th className="px-4 py-2 text-right">Quantity</th>
                <th className="px-4 py-2 text-right">Last close (TZS)</th><th className="px-4 py-2 text-right">Value (TZS)</th>
                <th className="px-4 py-2 text-right">Weight</th><th className="px-4 py-2 text-right">Gain (TZS)</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {p.holdings.map((h) => (
                <tr key={h.security_id} className="border-t border-neutral-100">
                  <td className="px-4 py-2 font-sans">
                    <Link href={`/report/${encodeURIComponent(h.security_id)}`} className="underline">{h.security_id}</Link>
                  </td>
                  <td className="px-4 py-2 text-right">{Number(h.quantity).toLocaleString("en-US")}</td>
                  <td className="px-4 py-2 text-right">
                    {h.price.available ? (
                      <span title={`Close on ${h.price.date}`}>
                        {fmtPerShare(h.price.value)} <span className="text-xs text-neutral-500 font-sans">{fmtDate(h.price.date)}</span>
                        {h.price.status !== "VERIFIED" && <> <StatusBadge status={h.price.status} /></>}
                      </span>
                    ) : (
                      <span className="font-sans"><StatusBadge status={h.price.status} title={h.price.reason} /></span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">{h.market_value ? fmtPerShare(h.market_value) : "–"}</td>
                  <td className="px-4 py-2 text-right">{h.weight ? fmtPct(Number(h.weight)) : "–"}</td>
                  <td className="px-4 py-2 text-right">{h.gain ? fmtPerShare(h.gain) : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {analyse && <div className="border-t border-neutral-200 px-4 py-4"><PortfolioAnalysis id={p.id} /></div>}
      <footer className="border-t border-neutral-200 px-4 py-3 text-xs text-neutral-600 space-y-1">
        {t.market_value && <p className="text-sm text-neutral-900">Total value: <span className="font-mono">TZS {fmtPerShare(t.market_value)}</span>
          {t.largest_weight && <> · largest holding {fmtPct(Number(t.largest_weight))}</>}</p>}
        {(t.status === "PARTIAL" || t.status === "NO_DATA") && <p>{TOTAL_WORD[t.status]}</p>}
        {t.stale_prices.length > 0 && <p>Stale prices: {t.stale_prices.join(", ")}. The last stored close is older than its freshness limit.</p>}
        <p>{t.note}</p>
        {(() => {
          const a = p.holdings.find((h) => h.price.available && h.price.attribution);
          return a && a.price.available ? <p>{a.price.attribution}</p> : null;
        })()}
      </footer>
    </section>
  );
}

function CreatePortfolio({ onCreated }: { onCreated: () => void }) {
  const [options, setOptions] = useState<SecurityOption[] | null>(null);
  const [name, setName] = useState("");
  const [rows, setRows] = useState([{ security_id: "", quantity: "", cost_per_share: "" }]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Portfolios are TZS-only for now (no FX conversion), so offer the TZS securities only.
    apiGet<{ results: SecurityOption[] }>("/api/v1/securities").then((r) =>
      setOptions(r.ok ? r.data.results.filter((s) => s.currency === "TZS") : []));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const holdings = rows.filter((r) => r.security_id && r.quantity).map((r) => ({
      security_id: r.security_id, quantity: r.quantity, ...(r.cost_per_share ? { cost_per_share: r.cost_per_share } : {}),
    }));
    const res = await fetch("/api/portfolios", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, base_currency: "TZS", holdings }),
    }).catch(() => null);
    setBusy(false);
    if (!res) return setError("The site could not be reached. Nothing was saved.");
    if (!res.ok) return setError(await readError(res));
    setName("");
    setRows([{ security_id: "", quantity: "", cost_per_share: "" }]);
    onCreated();
  }

  return (
    <form onSubmit={submit} className="border border-neutral-200 bg-white p-4 space-y-3" data-testid="create-portfolio">
      <h2 className="font-semibold">New portfolio (TZS)</h2>
      <input required maxLength={120} placeholder="Name" value={name} onChange={(e) => setName(e.target.value)}
        className="block w-full border border-neutral-300 px-3 py-2 text-sm" aria-label="Portfolio name" />
      {rows.map((r, i) => (
        <div key={i} className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <select value={r.security_id} aria-label={`Security ${i + 1}`}
            onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, security_id: e.target.value } : x)))}
            className="border border-neutral-300 px-2 py-2 text-sm">
            <option value="">{options === null ? "Loading securities…" : "Choose a security"}</option>
            {options?.map((o) => <option key={o.id} value={o.id}>{o.id} · {o.name}</option>)}
          </select>
          <input inputMode="decimal" placeholder="Quantity (shares)" value={r.quantity} aria-label={`Quantity ${i + 1}`}
            onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, quantity: e.target.value } : x)))}
            className="border border-neutral-300 px-3 py-2 text-sm font-mono" />
          <input inputMode="decimal" placeholder="Cost per share, optional" value={r.cost_per_share} aria-label={`Cost per share ${i + 1}`}
            onChange={(e) => setRows(rows.map((x, j) => (j === i ? { ...x, cost_per_share: e.target.value } : x)))}
            className="border border-neutral-300 px-3 py-2 text-sm font-mono" />
        </div>
      ))}
      <p className="text-xs text-neutral-500">Cost per share must be on today&apos;s share basis (after any split, e.g. NMB&apos;s 1:10 in August 2026).</p>
      <div className="flex flex-wrap gap-3">
        <button type="button" onClick={() => setRows([...rows, { security_id: "", quantity: "", cost_per_share: "" }])}
          className="border border-neutral-300 px-3 py-1.5 text-sm">Add holding</button>
        <button type="submit" disabled={busy} className="bg-black text-white px-4 py-1.5 text-sm font-semibold disabled:opacity-50">
          {busy ? "Saving…" : "Save portfolio"}
        </button>
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    </form>
  );
}
