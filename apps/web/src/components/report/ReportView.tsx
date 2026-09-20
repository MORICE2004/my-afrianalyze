"use client";

import React, { useState } from "react";
import { ModelViewBadge } from "@/components/ModelViewBadge";
import EvidenceLineage from "@/components/research/EvidenceLineage";
import ValuationExplainer from "@/components/research/ValuationExplainer";
import { NotAvailable } from "@/components/ui/NotAvailable";
import { PartialMarker, StatusBadge, StatusLegend } from "@/components/ui/StatusBadge";
import { API_URL, type DataStatus, type Report, type ReviewState, type StatementRow } from "@/lib/api";
import { fmtDate, fmtPct, fmtPerShare, fmtSignedPct, fmtValue } from "@/lib/format";
import { ExternalSource, SourceLink } from "./SourceLink";

const TABS = ["Summary", "Financial statements", "Ratios", "Beta", "Valuation", "Scenarios", "Risks", "Sources"] as const;
type Tab = (typeof TABS)[number];

export function ReportView({ report }: { report: Report }) {
  const [tab, setTab] = useState<Tab>("Summary");
  const { security: sec, header } = report;

  return (
    <article className="flex flex-col gap-6 pb-12">
      <ReviewBanner review={report.review} />
      <header className="border-b-2 border-black pb-5 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-neutral-500">
            {sec.exchange} · {sec.sector} · {sec.currency}
            {sec.isin ? ` · ISIN ${sec.isin}` : ""}
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">{sec.name}</h1>
          <p className="font-mono text-lg">{sec.id}</p>
          <p className="text-sm text-neutral-700 mt-2" data-testid="data-as-of">
            Data as of the financial year ending{" "}
            {report.data_as_of.fiscal_year_end ? fmtDate(report.data_as_of.fiscal_year_end) : "unknown"}
            {report.data_as_of.latest_report && <> · {report.data_as_of.latest_report}</>}
            {report.data_as_of.published_on && <> (published {fmtDate(report.data_as_of.published_on)})</>}
          </p>
          <p className="text-xs text-neutral-500 mt-1">
            Ticker verified on the <ExternalSource href={sec.listing_url}>exchange listing</ExternalSource> on {fmtDate(sec.verified_at)}.
            Report built {fmtDate(report.generated_at)}.
          </p>
        </div>
        <div className="text-left lg:text-right" data-testid="price">
          {header.price.available ? (
            <>
              <div className="text-3xl font-mono">{sec.currency} {fmtPerShare(header.price.value)}</div>
              <div className="text-xs text-neutral-500">Last trade {header.price.trade_date}</div>
            </>
          ) : (
            <div className="max-w-sm">
              <div className="text-xl font-mono text-neutral-400">
                Price: not available {header.price.status && <StatusBadge status={header.price.status} />}
              </div>
              <div className="text-xs text-neutral-500">{header.price.reason}</div>
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <ModelViewBadge recommendation={header.recommendation} rule={report.recommendation_rule} />
        <HeaderStat label="12-month target price" testId="target">
          {header.target_price.available ? `${sec.currency} ${fmtPerShare(header.target_price.value)}` : <ShortReason reason={header.target_price.reason} status={header.target_price.status} />}
        </HeaderStat>
        <HeaderStat label="Fair value range" testId="fair-value-range">
          {header.fair_value_range.available
            ? `${fmtPerShare(header.fair_value_range.low)} – ${fmtPerShare(header.fair_value_range.high)}`
            : <ShortReason reason={header.fair_value_range.reason} status={header.fair_value_range.status} />}
        </HeaderStat>
        <HeaderStat label="Confidence" testId="confidence">
          <span>{header.confidence.level} ({header.confidence.score.toFixed(0)}/100)</span>
          <ul className="mt-1 text-[11px] text-neutral-500 font-sans">
            {header.confidence.notes.map((n) => <li key={n}>{n}</li>)}
          </ul>
        </HeaderStat>
      </div>

      <div className="flex flex-wrap items-center gap-3 no-print">
        <a
          href={`${API_URL}/api/v1/reports/${encodeURIComponent(sec.id)}/pdf`}
          className="bg-black text-white px-4 py-2 text-sm font-semibold"
          data-testid="download-pdf"
        >
          Download PDF report
        </a>
        <span className="text-xs text-neutral-500">Same content as this page, in a research-report layout.</span>
      </div>

      <nav aria-label="Report sections" className="flex flex-wrap gap-1 border-b border-neutral-300 no-print">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            aria-current={tab === t ? "page" : undefined}
            className={`px-3 py-2 text-sm -mb-px border-b-2 ${tab === t ? "border-black font-semibold" : "border-transparent text-neutral-600 hover:text-black"}`}
          >
            {t}
          </button>
        ))}
      </nav>

      <section aria-label={tab}>
        {tab === "Summary" && <Summary report={report} />}
        {tab === "Financial statements" && <Statements report={report} />}
        {tab === "Ratios" && <Ratios report={report} />}
        {tab === "Beta" && <Beta report={report} />}
        {tab === "Valuation" && <ValuationExplainer report={report} />}
        {tab === "Scenarios" && <Scenarios report={report} />}
        {tab === "Risks" && <Risks report={report} />}
        {tab === "Sources" && <EvidenceLineage report={report} />}
      </section>

      <aside className="border border-neutral-300 bg-white p-4 text-xs text-neutral-600" data-testid="disclaimer">
        <b>Disclaimer.</b> {report.disclaimer}
      </aside>
    </article>
  );
}

function ReviewBanner({ review }: { review: ReviewState }) {
  if (review.status === "published") {
    return (
      <p className="text-xs text-neutral-600" data-testid="review-banner">
        Reviewed and published by {review.reviewer}
        {review.reviewed_at ? ` on ${fmtDate(review.reviewed_at)}` : ""} · research run {review.run_id}
      </p>
    );
  }
  return (
    <div role="status" className="border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900" data-testid="review-banner">
      <b>Draft, not reviewed.</b>{" "}
      {review.run_id
        ? <>Research run <span className="font-mono">{review.run_id}</span> ({review.status.replace("_", " ")}) </>
        : "This report "}
      has not been approved by a named reviewer. Do not rely on it or share it as research.
    </div>
  );
}

// Phones have no hover tooltips, so the reason is also printed (clamped to three lines).
function ShortReason({ reason, status }: { reason: string; status?: DataStatus }) {
  return (
    <>
      <NotAvailable compact reason={reason} status={status} />
      <p className="mt-1 text-[11px] leading-snug text-neutral-500 font-sans line-clamp-3" title={reason}>{reason}</p>
    </>
  );
}

function HeaderStat({ label, children, testId }: { label: string; children: React.ReactNode; testId: string }) {
  return (
    <div className="border border-neutral-200 bg-white p-4" data-testid={testId}>
      <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-2">{label}</div>
      <div className="text-lg font-mono">{children}</div>
    </div>
  );
}

function Summary({ report }: { report: Report }) {
  const notes = report.statements.flatMap((s) => s.rows).filter((r) => r.note);
  const failed = report.checks.filter((c) => !c.passed).length;
  const conflicts = report.conflicts.filter((c) => !["RESTATEMENT", "SOURCE_INCONSISTENCY", "METHOD_OUTLIER"].includes(c.kind)).length;
  const sourceIssues = report.conflicts.filter((c) => c.kind === "SOURCE_INCONSISTENCY");
  const counts = report.status_counts;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-3">
        <h2 className="font-semibold">What moved in {report.years.at(-1)}</h2>
        <ul className="space-y-2 text-sm text-neutral-800">
          {notes.slice(0, 12).map((r) => <li key={r.item_code}>{r.note!.text}</li>)}
        </ul>
        <p className="text-xs text-neutral-500">
          Notes are generated by fixed rules from the extracted figures. Numbers in them are computed, not written by a model.
        </p>
      </div>
      <div className="space-y-4">
        <div className="border border-neutral-200 bg-white p-4 text-sm">
          <h2 className="font-semibold mb-2">Data quality</h2>
          <p>{report.checks.length - failed} of {report.checks.length} tie checks passed.</p>
          <p>{conflicts} open extraction conflicts.</p>
          {sourceIssues.length > 0 && (
            <p>
              {sourceIssues.length} figure{sourceIssues.length > 1 ? "s" : ""} that do not add up inside the source
              document ({[...new Set(sourceIssues.map((c) => `FY${c.fiscal_year}`))].join(", ")}): shown as CONFLICTING
              SOURCE and not used in any calculation.
            </p>
          )}
          <p className="mt-2 text-xs text-neutral-500">Figures in the statement tables (FY{report.years[0]} to FY{report.years.at(-1)}):</p>
          <ul className="text-xs text-neutral-600 space-y-0.5" data-testid="status-counts">
            <li>{counts.verified} figures VERIFIED (two methods agree)</li>
            <li>{counts.partially_verified} PARTIALLY VERIFIED (one method)</li>
            <li>{counts.conflicting_source} CONFLICTING SOURCE</li>
            <li>{counts.insufficient_data} INSUFFICIENT DATA (not reported)</li>
          </ul>
          <p className="mt-2">Fiscal years covered: {report.years.join(", ")}.</p>
        </div>
        <div className="border border-neutral-200 bg-white p-4 text-sm">
          <h2 className="font-semibold mb-2">Not yet available</h2>
          {report.gaps.length ? (
            <ul className="list-disc pl-5 space-y-1">{report.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
          ) : <p>Nothing missing.</p>}
        </div>
      </div>
    </div>
  );
}

type Mode = "value" | "yoy" | "common";

function Statements({ report }: { report: Report }) {
  const [mode, setMode] = useState<Mode>("value");
  const years = report.years.map(String);
  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-neutral-500">Show:</span>
        {([["value", "Values"], ["yoy", "YoY change"], ["common", "Common size"]] as const).map(([m, l]) => (
          <button key={m} type="button" onClick={() => setMode(m)}
            className={`border px-3 py-1 ${mode === m ? "bg-black text-white border-black" : "border-neutral-300"}`}>{l}</button>
        ))}
        <span className="text-neutral-500">Click any value to open the source page. Values in TZS millions unless stated.</span>
      </div>
      <StatusLegend />
      {report.statements.map((st) => (
        <div key={st.code}>
          <h2 className="font-bold uppercase tracking-tight border-b-2 border-black pb-2 mb-2">{st.title}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono" data-testid={`statement-${st.code}`}>
              <thead>
                <tr className="text-neutral-500 border-b border-neutral-300 bg-neutral-50 text-xs">
                  <th className="text-left font-sans px-3 py-2 min-w-[16rem]">Line item</th>
                  {years.map((y) => <th key={y} className="text-right px-3 py-2">FY{y}</th>)}
                  <th className="text-right px-3 py-2">CAGR</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {st.rows.map((row) => <StatementLine key={row.item_code} row={row} years={years} mode={mode} />)}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatementLine({ row, years, mode }: { row: StatementRow; years: string[]; mode: Mode }) {
  const [open, setOpen] = useState(false);
  const byYear = new Map(row.analysis?.rows.map((r) => [String(r.fiscal_year), r]));
  return (
    <>
      <tr className="hover:bg-neutral-50">
        <td className="font-sans px-3 py-2 text-left">
          {row.note ? (
            <button type="button" className="text-left underline decoration-dotted" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
              {row.label}
            </button>
          ) : row.label}
          {row.unit === "TZS_per_share" && <span className="ml-1 text-xs text-neutral-500">(TZS per share)</span>}
          {row.derived && <span className="block text-[11px] text-neutral-500">Derived: {row.derived}</span>}
        </td>
        {years.map((y) => {
          const cell = row.cells[y];
          if (!cell || !cell.available) {
            return <td key={y} className="px-3 py-2 text-right"><NotAvailable compact reason={cell?.reason ?? "Not extracted"} status={cell?.status} /></td>;
          }
          const a = byYear.get(y);
          let content: React.ReactNode = fmtValue(cell.value, row.unit);
          if (mode === "yoy") content = a?.yoy.available ? fmtSignedPct(a.yoy.value) : <NotAvailable compact reason={a?.yoy.available === false ? a.yoy.reason : "n/a"} />;
          if (mode === "common") content = a?.common_size && a.common_size.available ? fmtPct(a.common_size.value) : "—";
          return (
            <td key={y} className="px-3 py-2 text-right whitespace-nowrap">
              {cell.source ? <SourceLink source={cell.source} method={cell.method}>{content}</SourceLink> : content}
              {cell.status === "PARTIALLY_VERIFIED" && <PartialMarker />}
              {cell.restated && cell.restated.length > 0 && <span title={cell.restated[0].detail} className="ml-1 text-amber-600">*</span>}
            </td>
          );
        })}
        <td className="px-3 py-2 text-right">
          {row.analysis?.cagr.available ? fmtPct(row.analysis.cagr.value) : <NotAvailable compact reason={row.analysis?.cagr.available === false ? row.analysis.cagr.reason : "No data"} />}
        </td>
      </tr>
      {open && row.note && (
        <tr><td colSpan={years.length + 2} className="px-3 pb-3 font-sans text-sm text-neutral-700 bg-neutral-50">{row.note.text}</td></tr>
      )}
    </>
  );
}

function Ratios({ report }: { report: Report }) {
  const years = report.years.map(String);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" data-testid="ratios">
        <thead className="bg-neutral-50 text-xs text-neutral-500">
          <tr><th className="text-left px-3 py-2">Ratio</th>{years.map((y) => <th key={y} className="text-right px-3 py-2">FY{y}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-neutral-100 font-mono">
          {report.ratios.map((r) => {
            const formula = Object.values(r.values).find((v) => v.available);
            return (
              <tr key={r.code}>
                <td className="px-3 py-2 font-sans">
                  {r.label}
                  {formula && formula.available && <span className="block text-[11px] text-neutral-500">{formula.formula}</span>}
                </td>
                {years.map((y) => {
                  const v = r.values[y];
                  return (
                    <td key={y} className="px-3 py-2 text-right" title={v.available ? JSON.stringify(v.inputs) : v.reason}>
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
      <div className="mt-2"><StatusLegend /></div>
      <p className="mt-2 text-xs text-neutral-500">
        Averages use opening and closing balances. Capital adequacy is on the{" "}
        {report.capital_basis === "bank" ? "bank-only" : "group (consolidated)"} basis {report.security.name} reports to the Bank of Tanzania.
        Hover a value to see its inputs.
      </p>
    </div>
  );
}

const BETA_LABELS: Record<string, string> = {
  raw_daily: "(a) Raw daily OLS",
  weekly: "(b) Weekly OLS",
  monthly: "(b) Monthly OLS",
  dimson: "(c) Dimson (lags and leads)",
  scholes_williams: "(d) Scholes-Williams",
  bottom_up: "(e) Bottom-up from regional bank peers",
};

function Beta({ report }: { report: Report }) {
  const b = report.beta;
  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-700">
        DSE shares do not trade every day, which biases a plain daily beta toward zero. All methods are shown side by side
        against {b.benchmark}; the valuation uses the one chosen by the rule below.
      </p>
      {b.adjustments?.length > 0 && (
        <div className="border border-amber-200 bg-amber-50 px-3 py-2 text-sm" data-testid="price-adjustments">
          <span className="font-medium">Price history adjusted.</span>
          <ul className="list-disc pl-5 mt-1 space-y-1">
            {b.adjustments.map((a) => <li key={a}>{a}</li>)}
          </ul>
        </div>
      )}
      <div className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm" data-testid="beta-table">
          <thead className="bg-neutral-50 text-xs text-neutral-500">
            <tr><th className="text-left px-3 py-2">Method</th><th className="text-right px-3 py-2">Beta</th><th className="text-right px-3 py-2">Std error</th><th className="text-right px-3 py-2">R²</th><th className="text-right px-3 py-2">Observations</th></tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {Object.entries(b.estimates).map(([k, e]) => (
              <tr key={k}>
                <td className="px-3 py-2">{BETA_LABELS[k] ?? k}</td>
                {e.available ? (
                  <>
                    <td className="px-3 py-2 text-right font-mono">{e.beta?.toFixed(3)}</td>
                    <td className="px-3 py-2 text-right font-mono">{e.std_error == null ? "—" : e.std_error.toFixed(3)}</td>
                    <td className="px-3 py-2 text-right font-mono">{e.r_squared == null ? "—" : e.r_squared.toFixed(3)}</td>
                    <td className="px-3 py-2 text-right font-mono">{e.observations}</td>
                  </>
                ) : (
                  <td colSpan={4} className="px-3 py-2 text-right text-xs text-neutral-500">Not available: {e.reason}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm">
        Share of zero-volume days:{" "}
        {b.zero_volume.available && b.zero_volume.value !== undefined
          ? `${fmtPct(b.zero_volume.value)} (${b.zero_volume.zero_volume_days} of ${b.zero_volume.index_trading_days})`
          : <NotAvailable compact reason={b.zero_volume.reason ?? ""} />}
      </p>
      <div className="border border-neutral-200 bg-white p-4 text-sm">
        <h3 className="font-semibold mb-1">Beta used in valuation</h3>
        {b.selected.available ? <p>{b.selected.beta?.toFixed(3)} — {b.selected.reason}</p> : <NotAvailable reason={b.selected.reason ?? ""} />}
        <pre className="mt-3 text-[11px] text-neutral-600 whitespace-pre-wrap">Selection rule (config/valuation.json): {JSON.stringify(b.rule, null, 1)}</pre>
      </div>
    </div>
  );
}

const DRIVER_LABELS: Record<string, string> = {
  loan_growth: "Loan growth", nim: "Net interest margin", cost_of_risk: "Cost of risk",
  cost_to_income: "Cost-to-income", payout: "Dividend payout",
};

function Scenarios({ report }: { report: Report }) {
  const cfg = report.valuation.config;
  const base = report.valuation.base_drivers;
  const res = report.valuation.result;
  const names = Object.keys(cfg.scenarios);
  return (
    <div className="space-y-4">
      <div className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm" data-testid="scenarios">
          <thead className="bg-neutral-50 text-xs text-neutral-500">
            <tr>
              <th className="text-left px-3 py-2">Driver</th>
              {names.map((n) => <th key={n} className="text-right px-3 py-2 capitalize">{n} ({fmtPct(cfg.scenarios[n].probability, 0)})</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100 font-mono">
            {Object.keys(DRIVER_LABELS).map((d) => (
              <tr key={d}>
                <td className="px-3 py-2 font-sans">{DRIVER_LABELS[d]}</td>
                {names.map((n) => {
                  const shock = cfg.scenarios[n].shocks[d] ?? 0;
                  const b = base[d];
                  return (
                    <td key={n} className="px-3 py-2 text-right">
                      {b?.available && b.value !== undefined ? fmtPct(b.value + shock) : "n/a"}
                      <span className="block text-[11px] text-neutral-500">base {shock >= 0 ? "+" : ""}{(shock * 100).toFixed(1)} pp</span>
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr className="font-semibold">
              <td className="px-3 py-2 font-sans">Fair value (TZS per share)</td>
              {names.map((n) => (
                <td key={n} className="px-3 py-2 text-right">
                  {res.available && res.scenarios ? fmtPerShare(res.scenarios[n].fair_value) : <NotAvailable compact reason={res.reason ?? ""} />}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <ul className="text-xs text-neutral-600 space-y-1">
        {names.map((n) => <li key={n}><b className="capitalize">{n}:</b> {cfg.scenarios[n].narrative_rule}</li>)}
      </ul>
      {!res.available && <NotAvailable reason={`Scenario values and the probability-weighted target: ${res.reason}`} />}
      <NotAvailable reason={`Peer cross-check (P/E and P/B against East African listed banks): ${report.peers.reason}`} />
    </div>
  );
}

const RISK_TITLES: Record<string, string> = {
  macro_currency: "Macro and currency", regulatory: "Regulatory (Bank of Tanzania)",
  credit_concentration: "Credit concentration", governance_ownership: "Governance and ownership", esg: "ESG",
};

function Risks({ report }: { report: Report }) {
  const groups = Object.keys(RISK_TITLES);
  return (
    <div className="space-y-6" data-testid="risks">
      {groups.map((g) => {
        const items = report.risks.filter((r) => r.category === g);
        return (
          <div key={g}>
            <h3 className="font-semibold mb-2">{RISK_TITLES[g]}</h3>
            {items.length === 0 ? <NotAvailable reason="No sourced statement loaded for this category." /> : (
              <ul className="space-y-3">
                {items.map((r) => (
                  <li key={r.id} className="border-l-2 border-neutral-300 pl-3 text-sm">
                    <div className="font-medium">{r.title}</div>
                    <blockquote className="text-neutral-700 italic">“{r.quote}”</blockquote>
                    <SourceLink source={r.source}>{r.source.title}, page {r.source.page}</SourceLink>
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
