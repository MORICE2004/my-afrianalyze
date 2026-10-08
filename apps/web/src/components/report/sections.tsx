"use client";

import { useReducedMotion } from "framer-motion";
import React, { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { NotAvailable } from "@/components/ui/NotAvailable";
import { PartialMarker, StatusBadge, StatusLegend } from "@/components/ui/StatusBadge";
import type { DataStatus, Report, ReviewState, StatementRow } from "@/lib/api";
import { fmtDate, fmtPct, fmtPerShare, fmtSignedPct, fmtValue } from "@/lib/format";
import { EvidenceCell } from "./Evidence";
import { SourceLink } from "./SourceLink";

const th = "px-3 py-2 text-xs font-medium text-muted";

export function ReviewBanner({ review }: { review: ReviewState }) {
  if (review.status === "published") {
    return (
      <p className="text-xs text-muted" data-testid="review-banner">
        Reviewed and published by {review.reviewer}
        {review.reviewed_at ? ` on ${fmtDate(review.reviewed_at)}` : ""} · research run {review.run_id}
      </p>
    );
  }
  return (
    <div role="status" className="rounded-lg border border-warn/30 bg-warn-bg px-4 py-2.5 text-sm text-warn" data-testid="review-banner">
      <b>Draft, not reviewed.</b>{" "}
      {review.run_id ? <>Research run <span className="font-mono">{review.run_id}</span> ({review.status.replace("_", " ")}) </> : "This research "}
      has not been approved by a named reviewer. Do not rely on it or share it as research.
    </div>
  );
}

// ------------------------------------------------------------------ trends

function rowByCode(report: Report, codes: string[]): StatementRow | undefined {
  for (const code of codes) {
    for (const st of report.statements) {
      const r = st.rows.find((x) => x.item_code === code);
      if (r) return r;
    }
  }
  return undefined;
}

// One question per chart: how has this line moved across the years we have sourced?
export function TrendChart({ report, title, codes, ratio, testId }: {
  report: Report; title: string; codes?: string[]; ratio?: string; testId?: string;
}) {
  const reduce = useReducedMotion();
  const years = report.years.map(String);
  let points: { year: string; value: number }[] = [];
  let unit: "millions" | "pct" = "millions";
  if (codes) {
    const row = rowByCode(report, codes);
    points = years.flatMap((y) => {
      const c = row?.cells[y];
      return c && c.available ? [{ year: `FY${y}`, value: Number(c.value) / 1000 }] : [];
    });
  } else if (ratio) {
    unit = "pct";
    const r = report.ratios.find((x) => x.code === ratio);
    points = years.flatMap((y) => {
      const v = r?.values[y];
      return v && v.available ? [{ year: `FY${y}`, value: Number(v.value) * 100 }] : [];
    });
  }
  return (
    <figure data-testid={testId} className="min-w-0">
      <figcaption className="mb-2 text-xs font-medium text-muted">
        {title} <span className="font-normal text-faint">{unit === "pct" ? "(%)" : `(${report.security.currency} bn)`}</span>
      </figcaption>
      {points.length < 2 ? (
        <p className="text-xs text-muted">Fewer than two sourced years: no trend to show.</p>
      ) : (
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={points} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: "var(--faint)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "var(--faint)", fontSize: 10 }} axisLine={false} tickLine={false} width={36} />
              <Tooltip cursor={{ fill: "var(--surface-2)" }}
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 8, fontSize: 12, color: "var(--fg)" }}
                formatter={(v) => [unit === "pct" ? `${Number(v).toFixed(1)}%` : `${Number(v).toLocaleString("en-US", { maximumFractionDigits: 1 })} bn`, title]} />
              <Bar dataKey="value" radius={[3, 3, 0, 0]} isAnimationActive={!reduce} animationDuration={600}>
                {/* The latest year in full colour, earlier years quieter: the eye goes to the newest figure. */}
                {points.map((p, i) => <Cell key={p.year} fill={i === points.length - 1 ? "var(--chart-1)" : "var(--chart-2)"} fillOpacity={i === points.length - 1 ? 1 : 0.45} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </figure>
  );
}

// ------------------------------------------------------------------ notes and data quality

export function WhatMoved({ report, limit = 8 }: { report: Report; limit?: number }) {
  const notes = report.statements.flatMap((s) => s.rows).filter((r) => r.note);
  if (!notes.length) return <p className="text-sm text-muted">No year-on-year notes could be generated from the sourced figures.</p>;
  return (
    <>
      <ul className="space-y-2 text-sm leading-relaxed">
        {notes.slice(0, limit).map((r) => <li key={r.item_code} className="border-l-2 border-line pl-3">{r.note!.text}</li>)}
      </ul>
      <p className="mt-3 text-xs text-faint">Written by fixed rules from the extracted figures; no number here is written by a model.</p>
    </>
  );
}

export function DataQuality({ report }: { report: Report }) {
  const failed = report.checks.filter((c) => !c.passed).length;
  const conflicts = report.conflicts.filter((c) => !["RESTATEMENT", "SOURCE_INCONSISTENCY", "METHOD_OUTLIER"].includes(c.kind)).length;
  const sourceIssues = report.conflicts.filter((c) => c.kind === "SOURCE_INCONSISTENCY");
  const counts = report.status_counts;
  return (
    <div className="space-y-3 text-sm">
      <dl className="grid grid-cols-2 gap-3">
        <div><dt className="text-xs text-muted">Tie checks passed</dt><dd className="text-lg font-semibold">{report.checks.length - failed} / {report.checks.length}</dd></div>
        <div><dt className="text-xs text-muted">Open extraction conflicts</dt><dd className="text-lg font-semibold">{conflicts}</dd></div>
      </dl>
      {sourceIssues.length > 0 && (
        <p className="text-xs text-muted">
          {sourceIssues.length} figure{sourceIssues.length > 1 ? "s" : ""} do not add up inside the source document
          ({[...new Set(sourceIssues.map((c) => `FY${c.fiscal_year}`))].join(", ")}); they are shown as conflicting and
          are not used in any calculation.
        </p>
      )}
      <ul className="space-y-0.5 text-xs text-muted" data-testid="status-counts">
        <li>{counts.verified} figures VERIFIED (two methods agree)</li>
        <li>{counts.partially_verified} PARTIALLY VERIFIED (one method)</li>
        <li>{counts.conflicting_source} CONFLICTING SOURCE</li>
        <li>{counts.insufficient_data} INSUFFICIENT DATA (not reported)</li>
      </ul>
      <p className="text-xs text-muted">Fiscal years covered: {report.years.join(", ")}.</p>
    </div>
  );
}

// ------------------------------------------------------------------ statements and ratios

type Mode = "value" | "yoy" | "common";

export function Statements({ report }: { report: Report }) {
  const [mode, setMode] = useState<Mode>("value");
  const years = report.years.map(String);
  const latest = years[years.length - 1];
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div role="group" aria-label="Show" className="inline-flex rounded-md border border-line p-0.5">
          {([["value", "Values"], ["yoy", "Year-on-year"], ["common", "Common size"]] as const).map(([m, l]) => (
            <button key={m} type="button" onClick={() => setMode(m)} aria-pressed={mode === m}
              className={`rounded px-2.5 py-1 ${mode === m ? "bg-selected text-on-selected" : "text-muted hover:text-fg"}`}>{l}</button>
          ))}
        </div>
        <span className="text-muted">{report.security.currency} millions unless stated. Click a value to see its source.</span>
      </div>
      <StatusLegend />
      {report.statements.map((st) => (
        <div key={st.code}>
          <h3 className="mb-2 text-sm font-semibold">{st.title}</h3>
          <div className="overflow-x-auto rounded-lg border border-line" tabIndex={0} role="region" aria-label="Scrollable table">
            <table className="w-full text-sm" data-testid={`statement-${st.code}`}>
              <thead className="bg-surface-2/70">
                <tr className="border-b border-line">
                  <th className={`${th} sticky left-0 z-10 min-w-[14rem] bg-surface-2 text-left`}>Line item</th>
                  {years.map((y) => <th key={y} className={`${th} text-right ${y === latest ? "text-fg" : ""}`}>FY{y}</th>)}
                  <th className={`${th} text-right`}>CAGR</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {st.rows.map((row) => <StatementLine key={row.item_code} row={row} years={years} latest={latest} mode={mode} currency={report.security.currency} />)}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatementLine({ row, years, latest, mode, currency }: { row: StatementRow; years: string[]; latest: string; mode: Mode; currency: string }) {
  const [open, setOpen] = useState(false);
  const byYear = new Map(row.analysis?.rows.map((r) => [String(r.fiscal_year), r]));
  return (
    <>
      <tr className="hover:bg-surface-2/50">
        <td className="sticky left-0 z-10 bg-surface px-3 py-2 text-left">
          {row.note ? (
            <button type="button" className="text-left underline decoration-line-strong decoration-dotted underline-offset-4" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
              {row.label}
            </button>
          ) : row.label}
          {row.unit === "TZS_per_share" && <span className="ml-1 text-xs text-muted">(per share)</span>}
          {row.derived && <span className="block text-[11px] text-faint">Derived: {row.derived}</span>}
        </td>
        {years.map((y) => {
          const cell = row.cells[y];
          const hl = y === latest ? "bg-surface-2/40 font-medium" : "";
          if (!cell || !cell.available) {
            return <td key={y} className={`px-3 py-2 text-right ${hl}`}><NotAvailable compact reason={cell?.reason ?? "Not extracted"} status={cell?.status} /></td>;
          }
          const a = byYear.get(y);
          let content: React.ReactNode = fmtValue(cell.value, row.unit);
          if (mode === "yoy") content = a?.yoy.available ? fmtSignedPct(a.yoy.value) : <NotAvailable compact reason={a?.yoy.available === false ? a.yoy.reason : "n/a"} />;
          if (mode === "common") content = a?.common_size && a.common_size.available ? fmtPct(a.common_size.value) : "—";
          return (
            <td key={y} className={`whitespace-nowrap px-3 py-2 text-right ${hl}`}>
              {cell.source ? (
                <EvidenceCell source={cell.source} method={cell.method} status={cell.status as DataStatus | undefined}
                  period={cell.period_end} currency={cell.currency ?? currency} asReported={cell.label_as_reported} column={cell.column}>
                  {content}
                </EvidenceCell>
              ) : content}
              {cell.status === "PARTIALLY_VERIFIED" && <PartialMarker />}
              {cell.restated && cell.restated.length > 0 && <span title={cell.restated[0].detail} className="ml-1 text-warn">*</span>}
            </td>
          );
        })}
        <td className="px-3 py-2 text-right text-muted">
          {row.analysis?.cagr.available ? fmtPct(row.analysis.cagr.value) : <NotAvailable compact reason={row.analysis?.cagr.available === false ? row.analysis.cagr.reason : "No data"} />}
        </td>
      </tr>
      {open && row.note && (
        <tr><td colSpan={years.length + 2} className="bg-surface-2/50 px-3 pb-3 pt-1 text-sm text-muted">{row.note.text}</td></tr>
      )}
    </>
  );
}

export function Ratios({ report, codes, testId = "ratios" }: { report: Report; codes?: string[]; testId?: string }) {
  const years = report.years.map(String);
  const latest = years[years.length - 1];
  const rows = codes ? report.ratios.filter((r) => codes.includes(r.code)) : report.ratios;
  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-line" tabIndex={0} role="region" aria-label="Scrollable table">
        <table className="w-full text-sm" data-testid={testId}>
          <thead className="bg-surface-2/70">
            <tr className="border-b border-line"><th className={`${th} text-left`}>Ratio</th>{years.map((y) => <th key={y} className={`${th} text-right ${y === latest ? "text-fg" : ""}`}>FY{y}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((r) => {
              const formula = Object.values(r.values).find((v) => v.available);
              return (
                <tr key={r.code}>
                  <td className="px-3 py-2">
                    {r.label}
                    {formula && formula.available && <span className="block text-[11px] text-faint">{formula.formula}</span>}
                  </td>
                  {years.map((y) => {
                    const v = r.values[y];
                    return (
                      <td key={y} className={`px-3 py-2 text-right ${y === latest ? "bg-surface-2/40 font-medium" : ""}`} title={v.available ? JSON.stringify(v.inputs) : v.reason}>
                        {v.available ? fmtPct(v.value) : <NotAvailable compact reason={v.reason} status={v.status} />}
                        {v.available && v.status === "PARTIALLY_VERIFIED" && <PartialMarker />}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">
        Averages use opening and closing balances. Capital adequacy is on the{" "}
        {report.capital_basis === "bank" ? "bank-only" : "group (consolidated)"} basis {report.security.name} reports to the Bank of Tanzania.
        Hover a value to see its inputs.
      </p>
    </div>
  );
}

// ------------------------------------------------------------------ beta, scenarios, risks

const BETA_LABELS: Record<string, string> = {
  raw_daily: "Raw daily OLS", weekly: "Weekly OLS", monthly: "Monthly OLS", dimson: "Dimson (lags and leads)",
  scholes_williams: "Scholes-Williams", bottom_up: "Bottom-up from regional bank peers", industry: "Industry average (comparable banks)",
};

export function Beta({ report }: { report: Report }) {
  const b = report.beta;
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        DSE shares do not trade every day, which pulls a plain daily beta toward zero. Every method is shown against{" "}
        {b.benchmark}; the valuation uses the one the rule below selects.
      </p>
      {b.adjustments?.length > 0 && (
        <div className="rounded-lg border border-line bg-surface-2/50 px-3 py-2 text-sm" data-testid="price-adjustments">
          <span className="font-medium">Price history adjusted.</span>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-muted">{b.adjustments.map((a) => <li key={a}>{a}</li>)}</ul>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-line" tabIndex={0} role="region" aria-label="Scrollable table">
        <table className="w-full text-sm" data-testid="beta-table">
          <thead className="bg-surface-2/70">
            <tr><th className={`${th} text-left`}>Method</th><th className={`${th} text-right`}>Beta</th><th className={`${th} text-right`}>Std error</th><th className={`${th} text-right`}>R²</th><th className={`${th} text-right`}>Observations</th></tr>
          </thead>
          <tbody className="divide-y divide-line">
            {Object.entries(b.estimates).map(([k, e]) => (
              <tr key={k} className={b.selected.method === k ? "bg-surface-2/50 font-medium" : ""}>
                <td className="px-3 py-2">{BETA_LABELS[k] ?? k}{b.selected.method === k && <span className="ml-2 text-xs text-muted">used</span>}</td>
                {e.available ? (
                  <>
                    <td className="px-3 py-2 text-right">{Number(e.beta).toFixed(3)}</td>
                    <td className="px-3 py-2 text-right">{e.std_error == null ? "—" : Number(e.std_error).toFixed(3)}</td>
                    <td className="px-3 py-2 text-right">{e.r_squared == null ? "—" : Number(e.r_squared).toFixed(3)}</td>
                    <td className="px-3 py-2 text-right">{e.observations}</td>
                  </>
                ) : <td colSpan={4} className="px-3 py-2 text-right text-xs text-muted">Not available: {e.reason}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm">
        Days without a trade:{" "}
        {b.zero_volume.available && b.zero_volume.value !== undefined
          ? `${fmtPct(b.zero_volume.value)} (${b.zero_volume.zero_volume_days} of ${b.zero_volume.index_trading_days})`
          : <NotAvailable compact reason={b.zero_volume.reason ?? ""} />}
      </p>
      <div className="rounded-lg border border-line p-4 text-sm">
        <h4 className="mb-1 font-medium">Beta used in valuation</h4>
        {b.selected.available ? <p className="text-muted">{Number(b.selected.beta).toFixed(3)}: {b.selected.reason}</p> : <NotAvailable reason={b.selected.reason ?? ""} />}
      </div>
    </div>
  );
}

const DRIVER_LABELS: Record<string, string> = {
  loan_growth: "Loan growth", nim: "Net interest margin", cost_of_risk: "Cost of risk",
  cost_to_income: "Cost-to-income", payout: "Dividend payout",
};

export function Scenarios({ report }: { report: Report }) {
  const cfg = report.valuation.config;
  const base = report.valuation.base_drivers;
  const res = report.valuation.result;
  const names = Object.keys(cfg.scenarios);
  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-line" tabIndex={0} role="region" aria-label="Scrollable table">
        <table className="w-full text-sm" data-testid="scenarios">
          <thead className="bg-surface-2/70">
            <tr>
              <th className={`${th} text-left`}>Driver</th>
              {names.map((n) => <th key={n} className={`${th} text-right capitalize`}>{n} ({fmtPct(cfg.scenarios[n].probability, 0)})</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {Object.keys(DRIVER_LABELS).map((d) => (
              <tr key={d}>
                <td className="px-3 py-2">{DRIVER_LABELS[d]}</td>
                {names.map((n) => {
                  const shock = cfg.scenarios[n].shocks[d] ?? 0;
                  const b = base[d];
                  return (
                    <td key={n} className="px-3 py-2 text-right">
                      {b?.available && b.value !== undefined ? fmtPct(Number(b.value) + shock) : "n/a"}
                      <span className="block text-[11px] text-faint">base {shock >= 0 ? "+" : ""}{(shock * 100).toFixed(1)} pp</span>
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr className="font-semibold">
              <td className="px-3 py-2">Fair value ({report.security.currency} per share)</td>
              {names.map((n) => (
                <td key={n} className="px-3 py-2 text-right">
                  {res.available && res.scenarios ? fmtPerShare(res.scenarios[n].fair_value) : <NotAvailable compact reason={res.reason ?? ""} />}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <ul className="space-y-1 text-xs text-muted">
        {names.map((n) => <li key={n}><b className="capitalize text-fg">{n}:</b> {cfg.scenarios[n].narrative_rule}</li>)}
      </ul>
      {!res.available && <NotAvailable reason={`Scenario values and the probability-weighted target: ${res.reason}`} />}
      <NotAvailable reason={`Peer cross-check (P/E and P/B against East African listed banks): ${report.peers.reason}`} />
    </div>
  );
}

export const RISK_TITLES: Record<string, string> = {
  macro_currency: "Macro and currency", regulatory: "Regulatory (Bank of Tanzania)",
  credit_concentration: "Credit concentration", governance_ownership: "Governance and ownership", esg: "ESG",
};

export function Risks({ report }: { report: Report }) {
  return (
    <div className="space-y-6" data-testid="risks">
      {Object.keys(RISK_TITLES).map((g) => {
        const items = report.risks.filter((r) => r.category === g);
        return (
          <div key={g}>
            <h3 className="mb-2 text-sm font-semibold">{RISK_TITLES[g]}</h3>
            {items.length === 0 ? <p className="text-sm text-muted">No statement from the company&apos;s documents is recorded for this category yet.</p> : (
              <ul className="space-y-3">
                {items.map((r) => (
                  <li key={r.id} className="border-l-2 border-line pl-3 text-sm">
                    <div className="font-medium">{r.title}</div>
                    <blockquote className="mt-0.5 text-muted">“{r.quote}”</blockquote>
                    <div className="mt-1 text-xs"><SourceLink source={r.source}>{r.source.title}, page {r.source.page}</SourceLink></div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}

export { StatusBadge };
