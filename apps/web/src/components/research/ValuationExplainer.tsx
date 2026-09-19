import React from "react";
import { ExternalSource } from "@/components/report/SourceLink";
import { NotAvailable } from "@/components/ui/NotAvailable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Report } from "@/lib/api";
import { fmtPct, fmtPerShare } from "@/lib/format";

const INPUT_LABELS: Record<string, string> = {
  risk_free: "TZS government bond yield (risk-free, before adjustment)",
  default_spread: "Tanzania sovereign default spread",
  mature_erp: "Mature-market equity risk premium",
  country_risk_premium: "Tanzania country risk premium",
};

// Shows the full chain from sourced inputs to cost of equity to fair value.
export default function ValuationExplainer({ report }: { report: Report }) {
  const coe = report.cost_of_equity;
  const val = report.valuation;
  const cfg = val.config;

  return (
    <div className="space-y-8">
      <section>
        <h3 className="font-semibold text-neutral-900 mb-2">1. Cost of equity inputs (TZS)</h3>
        <div className="overflow-x-auto border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-xs uppercase tracking-wider text-neutral-500">
              <tr><th className="text-left px-3 py-2">Input</th><th className="text-right px-3 py-2">Value</th><th className="text-left px-3 py-2">Source</th></tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {Object.entries(coe.inputs).map(([k, v]) => (
                <tr key={k}>
                  <td className="px-3 py-2">{INPUT_LABELS[k] ?? k}</td>
                  <td className="px-3 py-2 text-right font-mono">{v ? fmtPct(v.value, 2) : <NotAvailable compact reason="Input not loaded" />}</td>
                  <td className="px-3 py-2 text-xs text-neutral-600">
                    {v ? (
                      <>
                        {v.status && <><StatusBadge status={v.status} title={v.status === "STALE" ? `${v.age_days} days old, older than the limit in config/valuation.json` : undefined} />{" "}</>}
                        <ExternalSource href={v.source_url}>{v.source_name}</ExternalSource> · as of {v.as_of}
                        {v.age_days !== undefined ? ` (${v.age_days} days ago)` : ""}{v.label ? ` · ${v.label}` : ""}
                      </>
                    ) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-neutral-600">
          Method: {coe.method.subtract_default_spread ? "the TZS bond yield already contains Tanzania's default risk, so the default spread is subtracted to get a TZS risk-free rate; " : ""}
          {coe.method.crp_scaling === "beta"
            ? "cost of equity = risk-free + beta × (mature ERP + country risk premium)."
            : "cost of equity = risk-free + beta × mature ERP + country risk premium."}
        </p>
        <div className="mt-3">
          {coe.result.available ? (
            <ol className="font-mono text-sm space-y-1">
              {coe.result.steps?.map((s) => (
                <li key={s.label} className="flex justify-between max-w-lg"><span>{s.label}</span><span>{fmtPct(s.value, 2)}</span></li>
              ))}
            </ol>
          ) : (
            <NotAvailable reason={`Cost of equity: ${coe.result.reason}`} status={coe.result.status} />
          )}
        </div>
      </section>

      <section>
        <h3 className="font-semibold text-neutral-900 mb-2">2. Base-case drivers from {report.security.name}&apos;s own history</h3>
        <div className="overflow-x-auto border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-xs uppercase tracking-wider text-neutral-500">
              <tr><th className="text-left px-3 py-2">Driver</th><th className="text-right px-3 py-2">Value</th><th className="text-left px-3 py-2">How it is computed</th></tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {Object.entries(val.base_drivers).map(([k, d]) => (
                <tr key={k}>
                  <td className="px-3 py-2">{k.replace(/_/g, " ")}</td>
                  <td className="px-3 py-2 text-right font-mono">{d.available && d.value !== undefined ? fmtPct(d.value) : <NotAvailable compact reason={d.reason ?? ""} />}</td>
                  <td className="px-3 py-2 text-xs text-neutral-600">
                    {d.basis}
                    {d.inputs && <span className="block text-neutral-500">{Object.entries(d.inputs).map(([ik, iv]) => `${ik}: ${typeof iv === "number" ? (Math.abs(iv) < 5 ? fmtPct(iv, 2) : iv.toLocaleString()) : iv}`).join(" · ")}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="font-semibold text-neutral-900 mb-2">3. Methods and weights</h3>
        <ul className="text-sm text-neutral-700 space-y-1">
          <li><b>Residual income</b> (weight {fmtPct(cfg.method_weights.residual_income, 0)}): book value today + present value of (net income − cost of equity × opening book value) for {cfg.horizon_years} years + terminal value.</li>
          <li><b>Justified P/B</b> (weight {fmtPct(cfg.method_weights.justified_pb, 0)}): (ROE − g) / (CoE − g) × book value per share, using the mean projected ROE.</li>
          <li><b>Dividend discount</b> (weight {fmtPct(cfg.method_weights.ddm, 0)}): present value of projected dividends + terminal value.</li>
          <li><b>Terminal growth g</b> = {fmtPct(cfg.terminal_growth.value)} — {cfg.terminal_growth.note}</li>
          <li><b>12-month target</b> = Σ probability × (blended fair value × (1 + CoE) − next-year dividend).</li>
        </ul>
        <div className="mt-3">
          {val.result.available && val.result.fair_value !== undefined ? (
            <p className="font-mono text-sm">Probability-weighted fair value: TZS {fmtPerShare(val.result.fair_value)} per share</p>
          ) : (
            <NotAvailable reason={`Valuation: ${val.result.reason}`} status={val.result.status} />
          )}
        </div>
      </section>

      <section>
        <h3 className="font-semibold text-neutral-900 mb-2">4. Sensitivity to beta</h3>
        <p className="text-xs text-neutral-600 mb-2">
          Beta has not been measured, so these rows show how the valuation would change for a range of betas
          ({coe.method.sensitivity_betas.join(", ")}). They are a sensitivity, not a forecast or a target.
        </p>
        {val.sensitivity.available && val.sensitivity.rows ? (
          <div className="overflow-x-auto border border-neutral-200 bg-white">
            <table className="w-full text-sm font-mono" data-testid="valuation-sensitivity">
              <thead className="bg-neutral-50 text-xs uppercase tracking-wider text-neutral-500 font-sans">
                <tr>
                  <th className="text-right px-3 py-2">Beta</th>
                  <th className="text-right px-3 py-2">Cost of equity</th>
                  <th className="text-right px-3 py-2">Fair value (TZS)</th>
                  <th className="text-right px-3 py-2">Scenario range (TZS)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {val.sensitivity.rows.map((r) => (
                  <tr key={r.beta}>
                    <td className="px-3 py-2 text-right">{r.beta.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right">{fmtPct(r.cost_of_equity, 2)}</td>
                    <td className="px-3 py-2 text-right">{fmtPerShare(r.fair_value)}</td>
                    <td className="px-3 py-2 text-right">{fmtPerShare(r.range_low)} – {fmtPerShare(r.range_high)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <NotAvailable reason={val.sensitivity.reason ?? "Sensitivity not available"} />
        )}
      </section>
      <p className="text-xs text-neutral-500 italic">
        All valuation arithmetic is deterministic Python. No language model computes any figure on this page.
      </p>
    </div>
  );
}
