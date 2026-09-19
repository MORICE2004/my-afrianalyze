import type { Metadata } from "next";
import React from "react";
import { ExternalSource } from "@/components/report/SourceLink";
import { ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import { YieldCurveChart } from "@/components/YieldCurveChart";
import { apiGet } from "@/lib/api";
import { fmtPct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Tanzania fixed income",
  description: "Bank of Tanzania Treasury bond auction yields, policy rate and inflation, each with its source.",
};

type Obs = {
  available: boolean; value?: number; as_of?: string; age_days?: number; label?: string;
  source_name?: string; source_url?: string; reason?: string; attributes?: Record<string, unknown>;
};
type FI = {
  curve: (Obs & { tenor_years: number; stale: boolean })[];
  spread_2y_10y: { available: boolean; value?: number; formula?: string; dates?: string[]; reason?: string };
  policy_rate: Obs;
  inflation: Obs;
  real_yield_10y: { available: boolean; value?: number; formula?: string; reason?: string };
  note: string;
};

function Rate({ title, o, testId }: { title: string; o: Obs; testId: string }) {
  return (
    <div className="border border-neutral-200 bg-white p-5" data-testid={testId}>
      <div className="text-sm text-neutral-500">{title}</div>
      {o.available && o.value !== undefined ? (
        <>
          <div className="text-3xl font-mono">{fmtPct(o.value, 2)}</div>
          <div className="text-xs text-neutral-500 mt-1">
            {o.label} · as of {o.as_of}
            {o.age_days !== undefined && o.age_days > 100 && <span className="block text-amber-700">Older than 100 days; a newer figure may exist.</span>}
          </div>
          {o.source_url && <div className="text-xs mt-1"><ExternalSource href={o.source_url}>{o.source_name}</ExternalSource></div>}
        </>
      ) : <NotAvailable reason={o.reason ?? ""} />}
    </div>
  );
}

export default async function FixedIncomePage() {
  const res = await apiGet<FI>("/api/v1/fixed-income/TZ");
  if (!res.ok) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Tanzania fixed income</h1>
        <ErrorState message={res.error} />
      </div>
    );
  }
  const d = res.data;
  const points = d.curve.filter((p) => p.available && p.value !== undefined);
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">Tanzania fixed income (TZS)</h1>
      <p className="text-sm text-neutral-600">{d.note}</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Rate title="Central Bank Rate" o={d.policy_rate} testId="policy-rate" />
        <Rate title="Headline inflation (year on year)" o={d.inflation} testId="inflation" />
        <div className="border border-neutral-200 bg-white p-5" data-testid="real-yield">
          <div className="text-sm text-neutral-500">Real yield, 10-year</div>
          {d.real_yield_10y.available && d.real_yield_10y.value !== undefined ? (
            <><div className="text-3xl font-mono">{fmtPct(d.real_yield_10y.value, 2)}</div>
              <div className="text-xs text-neutral-500 mt-1">{d.real_yield_10y.formula}</div></>
          ) : <NotAvailable reason={d.real_yield_10y.reason ?? ""} />}
        </div>
      </div>

      <section className="border border-neutral-200 bg-white p-5">
        <h2 className="font-semibold">Auction yield by tenor</h2>
        <p className="text-xs text-neutral-500 mb-3">
          2Y–10Y spread: {d.spread_2y_10y.available && d.spread_2y_10y.value !== undefined
            ? `${(d.spread_2y_10y.value * 10000).toFixed(0)} bps (${d.spread_2y_10y.formula})`
            : d.spread_2y_10y.reason}
        </p>
        {points.length ? <YieldCurveChart points={points.map((p) => ({ tenor: `${p.tenor_years}Y`, yield: p.value! * 100 }))} />
          : <NotAvailable reason="No auction results loaded." />}
      </section>

      <section className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm" data-testid="bond-table">
          <thead className="bg-neutral-50 text-xs text-neutral-500">
            <tr><th className="text-left px-3 py-2">Tenor</th><th className="text-right px-3 py-2">Weighted avg YTM</th><th className="text-left px-3 py-2">Auction</th><th className="text-left px-3 py-2">Source</th></tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {d.curve.map((p) => (
              <tr key={p.tenor_years} className={p.stale ? "text-neutral-400" : ""}>
                <td className="px-3 py-2">{p.tenor_years} years</td>
                <td className="px-3 py-2 text-right font-mono">{p.value !== undefined ? fmtPct(p.value, 2) : "—"}</td>
                <td className="px-3 py-2 text-xs">{p.label} · {p.as_of}{p.stale ? " · more than a year old" : ""}</td>
                <td className="px-3 py-2 text-xs">{p.source_url && <ExternalSource href={p.source_url}>{p.source_name}</ExternalSource>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
