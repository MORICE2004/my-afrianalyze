"use client";

import React, { useState } from "react";
import { EmptyState, ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import { apiPost } from "@/lib/api";

const MARKETS = [
  { code: "TZ", label: "Tanzania (DSE)", currency: "TZS" },
  { code: "KE", label: "Kenya (NSE)", currency: "KES" },
  { code: "UG", label: "Uganda (USE)", currency: "UGX" },
] as const;
const RISK = [
  { val: "Conservative", desc: "Capital preservation first" },
  { val: "Moderate", desc: "Balance of growth and stability" },
  { val: "Aggressive", desc: "Long-term growth, higher volatility" },
] as const;

type Proposal = {
  available: boolean;
  reason?: string;
  universe?: { id: string; name: string; has_licensed_price: boolean }[];
  checks_that_will_apply?: string[];
};

export default function PortfolioBuilderPage() {
  const [step, setStep] = useState(0);
  const [market, setMarket] = useState<(typeof MARKETS)[number]["code"] | "">("");
  const [capital, setCapital] = useState("");
  const [risk, setRisk] = useState<(typeof RISK)[number]["val"] | "">("");
  const [horizon, setHorizon] = useState(5);
  const [result, setResult] = useState<Proposal | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const m = MARKETS.find((x) => x.code === market);
  const capitalValue = Number(capital.replace(/,/g, ""));
  const canNext = [market !== "", capitalValue > 0, risk !== "", horizon >= 1][step];

  const submit = async () => {
    if (!m || !risk) return;
    setBusy(true);
    setError("");
    const res = await apiPost<Proposal>("/api/v1/portfolio/proposals", {
      market: m.code, capital: capitalValue, currency: m.currency, risk_profile: risk, horizon_years: horizon,
    });
    setBusy(false);
    if (res.ok) setResult(res.data);
    else setError(res.error);
  };

  if (result) {
    return (
      <div className="space-y-6" data-testid="proposal-result">
        <h1 className="text-2xl font-bold">Portfolio proposal</h1>
        <p className="text-sm text-neutral-600">
          {m?.label} · {m?.currency} {capitalValue.toLocaleString()} · {risk} · {horizon} years
        </p>
        {result.available ? (
          <p>Proposal ready.</p>
        ) : (
          <>
            <NotAvailable reason={result.reason ?? ""} />
            {result.universe && (
              <div className="border border-neutral-200 bg-white p-4 text-sm">
                <h2 className="font-semibold mb-2">Securities in this market (security master)</h2>
                <ul className="space-y-1">
                  {result.universe.map((u) => (
                    <li key={u.id}><span className="font-mono">{u.id}</span> {u.name} — {u.has_licensed_price ? "priced" : "no licensed price"}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.checks_that_will_apply && (
              <div className="text-sm">
                <h2 className="font-semibold mb-1">Checks a proposal will pass once prices are available</h2>
                <ul className="list-disc pl-5">{result.checks_that_will_apply.map((c) => <li key={c}>{c}</li>)}</ul>
              </div>
            )}
          </>
        )}
        <button type="button" className="border border-neutral-300 px-4 py-2 text-sm" onClick={() => { setResult(null); setStep(0); }}>
          Start again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Portfolio builder</h1>
      <ol className="flex gap-2 text-xs uppercase tracking-wider text-neutral-500">
        {["Market", "Capital", "Risk", "Horizon"].map((s, i) => (
          <li key={s} className={i === step ? "font-bold text-black" : ""}>{i + 1}. {s}</li>
        ))}
      </ol>

      {step === 0 && (
        <fieldset className="space-y-2">
          <legend className="text-lg font-medium mb-2">Which market will you invest in?</legend>
          {MARKETS.map((x) => (
            <label key={x.code} className={`flex items-center gap-3 border px-4 py-3 cursor-pointer ${market === x.code ? "border-black bg-white" : "border-neutral-300"}`}>
              <input type="radio" name="market" value={x.code} checked={market === x.code} onChange={() => setMarket(x.code)} />
              {x.label} <span className="text-xs text-neutral-500">capital in {x.currency}</span>
            </label>
          ))}
        </fieldset>
      )}

      {step === 1 && m && (
        <div>
          <label htmlFor="capital" className="text-lg font-medium block mb-2">How much will you invest, in {m.currency}?</label>
          <div className="flex items-center border border-neutral-300 bg-white">
            <span className="px-3 text-neutral-500 font-mono" data-testid="capital-currency">{m.currency}</span>
            <input id="capital" inputMode="numeric" value={capital} onChange={(e) => setCapital(e.target.value)}
              className="flex-1 px-3 py-3 font-mono text-lg outline-none" placeholder="Amount" />
          </div>
        </div>
      )}

      {step === 2 && (
        <fieldset className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <legend className="text-lg font-medium mb-2">Risk profile</legend>
          {RISK.map((r) => (
            <button key={r.val} type="button" onClick={() => setRisk(r.val)} aria-pressed={risk === r.val}
              className={`border p-4 text-left ${risk === r.val ? "border-black bg-black text-white" : "border-neutral-300 bg-white"}`}>
              <div className="font-medium">{r.val}</div>
              <div className="text-xs opacity-80">{r.desc}</div>
            </button>
          ))}
        </fieldset>
      )}

      {step === 3 && (
        <div>
          <label htmlFor="horizon" className="text-lg font-medium block mb-2">Horizon: {horizon} years</label>
          <input id="horizon" type="range" min={1} max={30} value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} className="w-full" />
        </div>
      )}

      {error && <ErrorState message={error} />}

      <div className="flex justify-between">
        <button type="button" disabled={step === 0} onClick={() => setStep((s) => s - 1)} className="px-4 py-2 text-sm border border-neutral-300 disabled:opacity-30">Back</button>
        {step < 3 ? (
          <button type="button" disabled={!canNext} onClick={() => setStep((s) => s + 1)} className="px-4 py-2 text-sm bg-black text-white disabled:opacity-30">Continue</button>
        ) : (
          <button type="button" disabled={busy} onClick={submit} className="px-4 py-2 text-sm bg-black text-white disabled:opacity-30">{busy ? "Checking…" : "Build proposal"}</button>
        )}
      </div>
      {step === 0 && !market && <EmptyState title="Start with the market">The currency and the list of eligible securities depend on it.</EmptyState>}
    </div>
  );
}
