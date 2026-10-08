"use client";

import React, { useEffect, useState } from "react";
import { ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import type { DataStatus } from "@/lib/api";
import { fmtPct, fmtPerShare } from "@/lib/format";

// Everything here is computed by the API (packages/analysis/portfolio_risk.py); this only formats.
type Num = number | string;
const n = (v: Num | null | undefined) => (v === null || v === undefined ? NaN : Number(v));
const pct = (v: Num | null | undefined, d = 1) => (Number.isNaN(n(v)) ? "–" : fmtPct(n(v), d));
type Unavail = { available: false; status: DataStatus; reason: string };

interface Stress {
  name: string; available: boolean; status?: DataStatus; reason?: string; portfolio_effect?: Num; portfolio_effect_pct?: Num;
  by_asset?: { security_id: string; effect: Num; effect_pct: Num }[]; by_sector?: Record<string, Num>; how?: string; measured_in?: string;
}
interface Analysis {
  available: boolean; status: string; reason?: string; market_value?: Num; notes?: string[];
  concentration?: { largest_weight: Num; herfindahl: Num; effective_holdings: Num | null };
  liquidity?: { holdings: { security_id: string; zero_volume_days: number; window_days: number; days_to_sell: Num | null; thin: boolean }[]; how: string };
  risk?: Unavail | { available: true; weeks: number; from: string; to: string; annualised_volatility: Num; return_last_52_weeks: Num | null;
    max_drawdown: Num; asset_volatility: Record<string, Num>; correlation: Record<string, Num>; thinly_traded: string[]; how: string };
  optimisation?: Unavail | { available: true; note: string;
    current: { weights: Record<string, Num>; volatility: Num; how: string };
    minimum_variance: { weights: Record<string, Num>; volatility: Num; how: string };
    risk_parity: { weights: Record<string, Num>; volatility: Num; how: string };
    mean_variance: Unavail };
  drift?: Unavail | { available: true; rows: { security_id: string; current: Num; target: Num; drift: Num; outside_tolerance: boolean; trade_shares: Num; trade_value: Num }[]; note: string };
  stress_tests?: Stress[];
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="text-xs font-mono uppercase tracking-widest text-neutral-500">{title}</h3>
      {children}
    </section>
  );
}

export function PortfolioAnalysis({ id }: { id: number }) {
  const [a, setA] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/portfolios/${id}/analysis`).then(async (r) => {
      const body = await r.json().catch(() => null);
      if (r.ok) setA(body as Analysis);
      else setError(body?.detail ?? `Request failed (${r.status})`);
    }).catch(() => setError("The site could not be reached."));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!a) return <p className="text-sm text-neutral-500" aria-live="polite">Analysing…</p>;
  if (!a.available) return <NotAvailable reason={a.reason ?? ""} status={a.status as DataStatus} />;

  return (
    <div className="space-y-6 text-sm" data-testid="portfolio-analysis">
      {a.notes?.map((t) => <p key={t} className="text-xs text-neutral-600">{t}</p>)}

      <Block title="Risk">
        {a.risk && a.risk.available ? (
          <>
            <p>
              Volatility {pct(a.risk.annualised_volatility)} a year · largest fall from a peak {pct(a.risk.max_drawdown)} ·
              change over the last 52 weeks {pct(a.risk.return_last_52_weeks)} ({a.risk.weeks} weeks, {a.risk.from} to {a.risk.to}).
            </p>
            <p className="text-xs text-neutral-600">
              By holding: {Object.entries(a.risk.asset_volatility).map(([k, v]) => `${k} ${pct(v)}`).join(" · ")}.
              {Object.keys(a.risk.correlation).length > 0 && <> Correlation: {Object.entries(a.risk.correlation).map(([k, v]) => `${k.replace("|", " / ")} ${n(v).toFixed(2)}`).join(" · ")}.</>}
              {a.risk.thinly_traded.length > 0 && <> Thinly traded: {a.risk.thinly_traded.join(", ")}.</>} {a.risk.how}
            </p>
          </>
        ) : a.risk && <NotAvailable reason={a.risk.reason} status={a.risk.status} />}
      </Block>

      {a.concentration && (
        <Block title="Concentration and liquidity">
          <p>
            Largest holding {pct(a.concentration.largest_weight)} · equivalent to {n(a.concentration.effective_holdings).toFixed(1)} equal holdings.
          </p>
          {a.liquidity && (
            <p className="text-xs text-neutral-600">
              {a.liquidity.holdings.map((h) => `${h.security_id}: ${h.days_to_sell === null ? "no volume data" : `${n(h.days_to_sell).toFixed(1)} days to sell`}, ${h.zero_volume_days} of ${h.window_days} days without a trade`).join(" · ")}. {a.liquidity.how}.
            </p>
          )}
        </Block>
      )}

      <Block title="Stress tests">
        <div className="overflow-x-auto border border-neutral-200" tabIndex={0} role="region" aria-label="Scrollable table">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-xs text-neutral-500"><tr><th className="text-left px-3 py-2">Scenario</th><th className="text-right px-3 py-2">Effect</th><th className="text-left px-3 py-2">How</th></tr></thead>
            <tbody className="divide-y divide-neutral-100">
              {a.stress_tests?.map((s) => (
                <tr key={s.name}>
                  <td className="px-3 py-2">{s.name}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {s.available ? <>{pct(s.portfolio_effect_pct)}<span className="block text-xs text-neutral-500">TZS {fmtPerShare(n(s.portfolio_effect))}{s.measured_in ? ` (${s.measured_in})` : ""}</span></> : <NotAvailable compact reason={s.reason ?? ""} status={s.status} />}
                  </td>
                  <td className="px-3 py-2 text-xs text-neutral-600">
                    {s.available ? <>{s.how}{s.by_asset && <span className="block">{s.by_asset.map((x) => `${x.security_id} ${pct(x.effect_pct)}`).join(" · ")}</span>}</> : s.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Block>

      <Block title="Other ways to weight these holdings">
        {a.optimisation && a.optimisation.available ? (
          <div className="space-y-1">
            {(["current", "minimum_variance", "risk_parity"] as const).map((k) => {
              const o = (a.optimisation as Extract<Analysis["optimisation"], { available: true }>)[k];
              return (
                <p key={k}>
                  <span className="font-semibold">{k === "current" ? "Today" : k === "minimum_variance" ? "Minimum variance" : "Risk parity"}:</span>{" "}
                  {Object.entries(o.weights).map(([s, w]) => `${s} ${pct(w)}`).join(" · ")} → volatility {pct(o.volatility)}
                  <span className="block text-xs text-neutral-500">{o.how}</span>
                </p>
              );
            })}
            <p className="text-xs text-neutral-600">Mean-variance: {a.optimisation.mean_variance.reason} {a.optimisation.note}</p>
          </div>
        ) : a.optimisation && <NotAvailable reason={a.optimisation.reason} status={a.optimisation.status} />}
      </Block>

      <Block title="Drift from your target">
        {a.drift && a.drift.available ? (
          <>
            <ul className="space-y-1">
              {a.drift.rows.map((r) => (
                <li key={r.security_id}>
                  {r.security_id}: {pct(r.current)} now, target {pct(r.target)}{r.outside_tolerance && " (outside tolerance)"} · to rebalance:{" "}
                  {n(r.trade_shares) === 0 ? "no trade" : `${n(r.trade_shares) > 0 ? "buy" : "sell"} ${Math.abs(n(r.trade_shares)).toLocaleString("en-US")} shares (TZS ${fmtPerShare(Math.abs(n(r.trade_value)))})`}
                </li>
              ))}
            </ul>
            <p className="text-xs text-neutral-600">{a.drift.note}</p>
          </>
        ) : a.drift && <p className="text-xs text-neutral-600">{a.drift.reason} Set target weights when you save the portfolio to see drift and rebalancing trades.</p>}
      </Block>
      <p className="text-xs text-neutral-500">Deterministic calculations on stored DSE closes. A description of the past, not advice.</p>
    </div>
  );
}
