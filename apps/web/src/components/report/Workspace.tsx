"use client";

import * as Tabs from "@radix-ui/react-tabs";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import React, { useCallback, useEffect, useReducer, useState } from "react";
import { QuoteFreshness } from "@/components/market/Freshness";
import { PriceChart } from "@/components/market/PriceChart";
import EvidenceLineage from "@/components/research/EvidenceLineage";
import ValuationExplainer from "@/components/research/ValuationExplainer";
import { Change, Empty, Panel, Skeleton } from "@/components/ui/kit";
import { API_URL, type Quote, type Report, type ResearchStage, type Security, type StreamEvent } from "@/lib/api";
import { fmtCompact, fmtDate, fmtPct, fmtPerShare, fmtShortDate } from "@/lib/format";
import { rememberViewed, toggleWatch, useSavedList } from "@/lib/local";
import { ExportButtons } from "./ExportButtons";
import { ResearchRunPanel } from "./ResearchRunPanel";
import { Beta, DataQuality, Ratios, ReviewBanner, RISK_TITLES, Risks, Scenarios, Statements, TrendChart, WhatMoved } from "./sections";
import { TechnicalPanel } from "./TechnicalPanel";
import { ExternalSource } from "./SourceLink";
import { ValuationRange, ViewCard } from "./ViewCard";

// What a reader sees for each stage the research engine reports (packages/research/engine.py). A stage is shown
// as done only when the API has sent it: nothing here runs on a timer.
const STEPS: { key: string; label: string }[] = [
  { key: "company", label: "Finding the company" },
  { key: "price", label: "Retrieving the latest price" },
  { key: "sources", label: "Checking the annual reports" },
  { key: "documents", label: "Verifying the documents" },
  { key: "extraction", label: "Reading the financial statements" },
  { key: "validation", label: "Validating the figures" },
  { key: "calculations", label: "Calculating financial metrics" },
  { key: "valuation", label: "Running the valuation" },
  { key: "technical", label: "Analysing market behaviour" },
  { key: "risk", label: "Collecting the risks" },
  { key: "synthesis", label: "Preparing the research" },
];

const TABS = ["Overview", "Financials", "Valuation", "Technical", "Risk", "Evidence", "Research"] as const;
type Tab = (typeof TABS)[number];
// The stage each tab's content depends on, for the small readiness marks while the research runs.
const TAB_STAGE: Record<Tab, string> = {
  Overview: "price", Financials: "calculations", Valuation: "valuation", Technical: "technical",
  Risk: "risk", Evidence: "validation", Research: "synthesis",
};

type Done = { state: string; label?: string; detail?: string; duration_ms: number; recorded?: boolean; executed_at?: string | null };
type State = {
  status: "running" | "done" | "error";
  done: Record<string, Done>;
  stages: ResearchStage[];
  quote: Quote | null;
  report: Report | null;
  unavailable: { status: string; reason: string } | null;
  totalMs: number | null;
};
type Action = { type: "event"; ev: StreamEvent } | { type: "fail" } | { type: "reset" };

const INITIAL: State = { status: "running", done: {}, stages: [], quote: null, report: null, unavailable: null, totalMs: null };

function reduce(s: State, a: Action): State {
  if (a.type === "reset") return INITIAL;
  if (a.type === "fail") return { ...s, status: "error" };
  const ev = a.ev;
  switch (ev.event) {
    case "step":
      return { ...s, done: { ...s.done, [ev.step]: { state: ev.state, label: ev.label, duration_ms: ev.duration_ms } } };
    case "quote":
      return { ...s, quote: ev.data };
    case "stage":
      return { ...s, stages: [...s.stages, ev.data],
        done: { ...s.done, [ev.data.stage]: { state: ev.data.state, detail: ev.data.detail, duration_ms: ev.data.duration_ms,
          recorded: ev.data.recorded, executed_at: ev.data.executed_at } } };
    case "report":
      return { ...s, report: ev.data };
    case "unavailable":
      return { ...s, unavailable: { status: ev.status, reason: ev.reason } };
    case "done":
      return { ...s, status: "done", totalMs: ev.total_ms };
    default:
      return s;
  }
}

function useResearch(securityId: string, attempt: number) {
  const [state, dispatch] = useReducer(reduce, INITIAL);
  useEffect(() => {
    const ctrl = new AbortController();
    dispatch({ type: "reset" });
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/research/${encodeURIComponent(securityId)}/stream`, { signal: ctrl.signal, cache: "no-store" });
        if (!res.ok || !res.body) {
          if (res.status === 429) {
            dispatch({ type: "event", ev: { event: "unavailable", status: "BUSY", reason: "Too many research requests from this connection. Please try again in a minute." } });
            dispatch({ type: "event", ev: { event: "done", total_ms: 0 } });
            return;
          }
          throw new Error(String(res.status));
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let finished = false;
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          let nl: number;
          while ((nl = buf.indexOf("\n")) >= 0) {
            const line = buf.slice(0, nl).trim();
            buf = buf.slice(nl + 1);
            if (!line) continue;
            const ev = JSON.parse(line) as StreamEvent;
            if (ev.event === "done") finished = true;
            dispatch({ type: "event", ev });
          }
        }
        if (!finished) dispatch({ type: "event", ev: { event: "done", total_ms: 0 } });
      } catch (e) {
        if ((e as Error).name !== "AbortError") dispatch({ type: "fail" });
      }
    })();
    return () => ctrl.abort();
  }, [securityId, attempt]);
  return state;
}

export function Workspace({ security }: { security: Security }) {
  const [attempt, setAttempt] = useState(0);
  const s = useResearch(security.id, attempt);
  const reduceMotion = useReducedMotion();
  const [tab, setTab] = useState<Tab>("Overview");
  const watch = useSavedList("watchlist");
  const watched = watch.some((w) => w.id === security.id);

  useEffect(() => {
    rememberViewed({ id: security.id, name: security.name, currency: security.currency });
  }, [security.id, security.name, security.currency]);

  const fade = useCallback((delay = 0) => (reduceMotion ? {} : {
    initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 },
    transition: { duration: 0.28, ease: [0.2, 0, 0, 1] as const, delay },
  }), [reduceMotion]);

  const q = s.quote;
  const report = s.report;
  return (
    <article className="space-y-5 pb-10">
      {/* Header: known from the security master before any research arrives. */}
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
            <Link href="/research" className="hover:text-fg">Research</Link><span aria-hidden>/</span>
            <span>{security.exchange_name ?? security.exchange}</span>
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">{security.name}</h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-mono font-medium">{security.ticker}</span>
            <span className="text-faint">·</span><span className="text-muted">{security.exchange}</span>
            <span className="rounded border border-line px-1.5 py-0.5 font-mono text-xs" data-testid="currency" title="All prices and figures for this company are in this currency">{security.currency}</span>
            {security.sector && security.sector !== "Unclassified" && <span className="text-muted">{security.sector}</span>}
            {security.isin && <span className="text-xs text-faint">ISIN {security.isin}</span>}
            <button type="button" onClick={() => toggleWatch({ id: security.id, name: security.name, currency: security.currency })}
              aria-pressed={watched} data-testid="watch-toggle"
              className={`ml-1 inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs ${watched ? "border-fg text-fg" : "border-line text-muted hover:text-fg"}`}>
              <span aria-hidden>{watched ? "★" : "☆"}</span>{watched ? "On watchlist" : "Add to watchlist"}
            </button>
          </div>
        </div>
        <div className="lg:text-right" data-testid="quote-header">
          {q === null ? (
            <div className="space-y-2 lg:ml-auto lg:w-56" aria-label="Loading price"><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-40" /></div>
          ) : q.available ? (
            <motion.div {...fade()}>
              <div className="flex items-baseline gap-3 lg:justify-end">
                <span className="text-3xl font-semibold tracking-tight">{q.currency} {fmtPerShare(q.price)}</span>
                <Change value={q.change_pct} className="text-base font-medium" label="Change on the day" />
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted lg:justify-end">
                <QuoteFreshness quote={q} />
                <span>Close {fmtDate(q.trade_date)}</span>
                {!q.traded && q.last_traded_date && <span>· no trade that day; last traded {fmtShortDate(q.last_traded_date)}</span>}
                {q.market_cap && <span>· Market cap {q.currency} {fmtCompact(q.market_cap)}</span>}
              </div>
            </motion.div>
          ) : (
            <div className="flex items-center gap-2 lg:justify-end"><QuoteFreshness quote={q} /></div>
          )}
        </div>
      </header>

      {report && <motion.div {...fade()}><ReviewBanner review={report.review} /></motion.div>}

      <Progress state={s} onRetry={() => setAttempt((a) => a + 1)} />

      {s.unavailable && s.unavailable.status !== "NOT_FOUND" && !report && (
        <Empty title={s.unavailable.status === "INSUFFICIENT_DATA" ? "Research not available yet" : s.unavailable.status === "IN_REVIEW" ? "Research in review" : "Research unavailable"} testId="research-unavailable">
          {s.unavailable.reason}
        </Empty>
      )}

      {/* With no research, the price history is still worth showing on its own. */}
      {!report && s.status === "done" && q?.available && (
        <Panel title="Price"><PriceChart instrumentId={security.id} currency={security.currency} label={security.name} /></Panel>
      )}

      <AnimatePresence>
        {report && (
          <motion.div key="research" {...fade(0.05)} className="space-y-5">
            <ViewCard report={report} quote={q} />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted" data-testid="data-as-of">
                Financials to {report.data_as_of.fiscal_year_end ? fmtDate(report.data_as_of.fiscal_year_end) : "an unknown date"}
                {report.data_as_of.latest_report && <> · {report.data_as_of.latest_report}</>}
                {report.data_as_of.published_on && <> (published {fmtDate(report.data_as_of.published_on)})</>}
                {" · "}ticker checked on the <ExternalSource href={security.listing_url}>exchange listing</ExternalSource> {fmtDate(security.verified_at)}
              </p>
              <ExportButtons securityId={security.id} />
            </div>

            <Tabs.Root value={tab} onValueChange={(v) => setTab(v as Tab)}>
              <Tabs.List aria-label="Research sections" className="no-print -mx-4 flex overflow-x-auto border-b border-line px-4 sm:mx-0 sm:px-0">
                {TABS.map((t) => (
                  <Tabs.Trigger key={t} value={t}
                    className="relative shrink-0 px-3 py-2.5 text-sm text-muted transition-colors hover:text-fg data-[state=active]:font-medium data-[state=active]:text-fg">
                    {t}
                    {tab === t && !reduceMotion && <motion.span layoutId="tab-underline" className="absolute inset-x-2 -bottom-px h-0.5 bg-fg" />}
                    {tab === t && reduceMotion && <span className="absolute inset-x-2 -bottom-px h-0.5 bg-fg" />}
                  </Tabs.Trigger>
                ))}
              </Tabs.List>
              <Tabs.Content value="Overview" className="pt-5 outline-none"><Overview report={report} quote={q} /></Tabs.Content>
              <Tabs.Content value="Financials" className="space-y-8 pt-5 outline-none">
                <div className="grid gap-4 md:grid-cols-3">
                  <TrendChart report={report} title="Profit for the year" codes={["profit_for_year", "profit_attributable_owners"]} />
                  <TrendChart report={report} title="Operating income" codes={["total_operating_income", "operating_income_pre_impairment"]} />
                  <TrendChart report={report} title="Return on equity" ratio="roe" />
                </div>
                <Statements report={report} />
                <section><h3 className="mb-2 text-sm font-semibold">Ratios and bank metrics</h3><Ratios report={report} /></section>
              </Tabs.Content>
              <Tabs.Content value="Valuation" className="space-y-8 pt-5 outline-none">
                <Panel title="Valuation range"><ValuationRange report={report} quote={q} /></Panel>
                <ValuationExplainer report={report} />
                <section><h3 className="mb-2 text-sm font-semibold">Scenarios</h3><Scenarios report={report} /></section>
                <section><h3 className="mb-2 text-sm font-semibold">Beta</h3><Beta report={report} /></section>
              </Tabs.Content>
              <Tabs.Content value="Technical" className="space-y-6 pt-5 outline-none">
                <Panel title="Price history"><PriceChart instrumentId={security.id} currency={security.currency} label={security.name} defaultRange="6M" /></Panel>
                <TechnicalPanel report={report} />
              </Tabs.Content>
              <Tabs.Content value="Risk" className="space-y-6 pt-5 outline-none">
                <MarketRisk report={report} />
                <Risks report={report} />
              </Tabs.Content>
              <Tabs.Content value="Evidence" className="space-y-6 pt-5 outline-none">
                <Panel title="Data quality"><DataQuality report={report} /></Panel>
                <EvidenceLineage report={report} />
              </Tabs.Content>
              <Tabs.Content value="Research" className="space-y-6 pt-5 outline-none">
                <ResearchDetail report={report} state={s} />
                <ResearchRunPanel securityId={security.id} />
              </Tabs.Content>
            </Tabs.Root>

            <aside className="rounded-lg border border-line px-4 py-3 text-xs text-muted" data-testid="disclaimer">
              <b className="text-fg">Disclaimer.</b> {report.disclaimer}
            </aside>
          </motion.div>
        )}
      </AnimatePresence>
      <span className="sr-only" aria-live="polite">{s.status === "done" && report ? "Research loaded." : ""}</span>
      <TabReadiness state={s} />
    </article>
  );
}

// ------------------------------------------------------------------ progress

function mark(state: string | undefined) {
  if (!state) return { icon: "", cls: "border-line" };
  if (state === "COMPLETED") return { icon: "✓", cls: "border-fg bg-fg text-on-selected" };
  if (state === "PARTIAL") return { icon: "!", cls: "border-warn bg-warn-bg text-warn" };
  if (state === "FAILED" || state === "BLOCKED") return { icon: "×", cls: "border-neg bg-neg-bg text-neg" };
  return { icon: "–", cls: "border-line-strong text-muted" };
}

const PLAIN: Record<string, string> = {
  COMPLETED: "Done", PARTIAL: "Done, with gaps noted", INSUFFICIENT_DATA: "Not enough data", FAILED: "Failed",
  BLOCKED: "Blocked", SKIPPED: "Not part of this step",
};

function Progress({ state, onRetry }: { state: State; onRetry: () => void }) {
  const [open, setOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const received = STEPS.filter((st) => state.done[st.key]);
  const next = STEPS.find((st) => !state.done[st.key]);
  const partial = received.filter((st) => state.done[st.key].state !== "COMPLETED").length;
  const recorded = state.stages.find((st) => st.recorded);

  if (state.status === "error") {
    return (
      <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-sm">
        <span>The research could not be loaded. The data service may be unavailable.</span>
        <button type="button" onClick={onRetry} className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-surface-2">Try again</button>
      </div>
    );
  }
  const running = state.status === "running";
  const stopped = !!state.unavailable && !state.report;
  return (
    <section aria-label="Research progress" data-testid="research-progress" data-status={state.status}
      className="rounded-xl border border-line bg-surface">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={running || open}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm sm:px-5">
        <span className="flex items-center gap-2">
          {running ? (
            <span className="relative flex h-2.5 w-2.5" aria-hidden>
              {!reduceMotion && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-fg opacity-30" />}
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-fg" />
            </span>
          ) : <span className={`flex h-4 w-4 items-center justify-center rounded-full border text-[10px] ${mark(stopped ? "INSUFFICIENT_DATA" : "COMPLETED").cls}`} aria-hidden>{stopped ? "–" : "✓"}</span>}
          <span className="font-medium">
            {running ? (next ? `${next.label}…` : "Finishing…") : stopped ? "Research stopped" : "Research prepared"}
          </span>
          {!running && (
            <span className="text-muted">
              {recorded ? `· recorded when the research ran${recorded.executed_at ? ` on ${fmtDate(recorded.executed_at)}` : ""}` :
                state.totalMs ? `· ${state.totalMs < 1000 ? `${Math.round(state.totalMs)} ms` : `${(state.totalMs / 1000).toFixed(1)} s`}` : ""}
              {partial > 0 && ` · ${partial} step${partial > 1 ? "s" : ""} with gaps noted`}
            </span>
          )}
        </span>
        {!running && <span className="text-xs text-muted">{open ? "Hide steps" : "Show steps"}</span>}
      </button>
      <AnimatePresence initial={false}>
        {(running || open) && (
          <motion.ol key="steps"
            initial={reduceMotion ? false : { height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={reduceMotion ? undefined : { height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
            className="grid gap-x-6 gap-y-1.5 overflow-hidden border-t border-line px-4 py-3 text-sm sm:grid-cols-2 sm:px-5">
            {STEPS.map((st) => {
              const d = state.done[st.key];
              const m = mark(d?.state);
              const isNext = running && next?.key === st.key;
              return (
                <li key={st.key} className="flex items-start gap-2.5" data-step={st.key} data-state={d?.state ?? "PENDING"}>
                  <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[10px] ${m.cls} ${isNext && !reduceMotion ? "animate-pulse" : ""}`} aria-hidden>{m.icon}</span>
                  <span className="min-w-0">
                    <span className={d ? "text-fg" : "text-faint"}>{st.label}</span>
                    {d && (
                      <span className="ml-2 text-xs text-muted">
                        {PLAIN[d.state] ?? d.state.replace(/_/g, " ").toLowerCase()}
                        {!d.recorded && ` · ${d.duration_ms < 1 ? "<1" : Math.round(d.duration_ms)} ms`}
                      </span>
                    )}
                    {d?.detail && d.state !== "COMPLETED" && <span className="block text-xs text-muted">{d.detail}</span>}
                  </span>
                </li>
              );
            })}
          </motion.ol>
        )}
      </AnimatePresence>
    </section>
  );
}

// Screen readers hear which tabs are ready while the research runs; sighted readers see the progress list.
function TabReadiness({ state }: { state: State }) {
  if (state.status !== "running") return null;
  const ready = TABS.filter((t) => state.done[TAB_STAGE[t]]);
  return <span className="sr-only" aria-live="polite">{ready.length ? `Ready: ${ready.join(", ")}` : ""}</span>;
}

// ------------------------------------------------------------------ tab contents

const KEY_RATIOS = ["roe", "nim", "cost_to_income", "npl_ratio", "car", "dividend_payout"];

function Overview({ report, quote }: { report: Report; quote: Quote | null }) {
  const latest = String(report.years[report.years.length - 1]);
  const prev = String(report.years[report.years.length - 2]);
  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <div className="space-y-5 lg:col-span-2">
        <Panel title="Price">
          <PriceChart instrumentId={report.security.id} currency={report.security.currency} label={report.security.name} testId="overview-chart" />
          {quote && quote.available && quote.attribution && (
            <p className="mt-1 text-[11px] text-faint" data-testid="price-attribution">{quote.attribution}</p>
          )}
        </Panel>
        <Panel title={`What moved in FY${latest}`}><WhatMoved report={report} limit={6} /></Panel>
        <div className="grid gap-4 rounded-xl border border-line bg-surface p-4 sm:grid-cols-3 sm:p-5">
          <TrendChart report={report} title="Profit for the year" codes={["profit_for_year", "profit_attributable_owners"]} testId="trend-profit" />
          <TrendChart report={report} title="Operating income" codes={["total_operating_income", "operating_income_pre_impairment"]} />
          <TrendChart report={report} title="Return on equity" ratio="roe" />
        </div>
      </div>
      <div className="space-y-5">
        <Panel title={`Key figures, FY${latest}`} testId="key-ratios">
          <dl className="divide-y divide-line text-sm">
            {KEY_RATIOS.map((code) => {
              const r = report.ratios.find((x) => x.code === code);
              if (!r) return null;
              const v = r.values[latest];
              const p = r.values[prev];
              return (
                <div key={code} className="flex items-center justify-between gap-3 py-2">
                  <dt className="text-muted">{r.label}</dt>
                  <dd className="text-right font-medium">
                    {v?.available ? fmtPct(v.value) : <span className="text-xs font-normal text-muted">not available</span>}
                    {v?.available && p?.available && (
                      <span className="block text-[11px] font-normal text-faint">FY{prev}: {fmtPct(p.value)}</span>
                    )}
                  </dd>
                </div>
              );
            })}
          </dl>
        </Panel>
        <Panel title="Key risks">
          {report.risks.length === 0 ? <p className="text-sm text-muted">No risks from the company&apos;s documents are recorded yet.</p> : (
            <ul className="space-y-2 text-sm">
              {report.risks.slice(0, 4).map((r) => (
                <li key={r.id}><span className="font-medium">{r.title}</span><span className="block text-xs text-muted">{RISK_TITLES[r.category] ?? r.category} · page {r.source.page}</span></li>
              ))}
            </ul>
          )}
        </Panel>
        <Panel title="Data quality"><DataQuality report={report} /></Panel>
        {report.gaps.length > 0 && (
          <Panel title="Not yet available">
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted">{report.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
          </Panel>
        )}
      </div>
    </div>
  );
}

function MarketRisk({ report }: { report: Report }) {
  const z = report.beta.zero_volume;
  const b = report.beta.selected;
  return (
    <Panel title="Market risk">
      <dl className="grid gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs text-muted">Days without a trade</dt>
          <dd className="mt-1 text-lg font-semibold">{z.available && z.value !== undefined ? fmtPct(Number(z.value)) : "—"}</dd>
          <dd className="text-xs text-muted">A thinly traded share can be hard to buy or sell at the quoted price.</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Beta used in the valuation</dt>
          <dd className="mt-1 text-lg font-semibold">{b.available ? Number(b.beta).toFixed(2) : "—"}</dd>
          <dd className="text-xs text-muted">Sensitivity to the market, from {b.method === "industry" ? "the average of comparable banks" : b.method}.</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Sourced company risks</dt>
          <dd className="mt-1 text-lg font-semibold">{report.risks.length}</dd>
          <dd className="text-xs text-muted">Each quoted from the company&apos;s own reports, below.</dd>
        </div>
      </dl>
    </Panel>
  );
}

function ResearchDetail({ report, state }: { report: Report; state: State }) {
  return (
    <Panel title="How this research was produced" testId="research-detail">
      <ol className="space-y-2 text-sm">
        {state.stages.map((st) => (
          <li key={st.stage} className="grid gap-1 sm:grid-cols-[180px_1fr]">
            <span className="font-medium capitalize">{st.stage.replace("_", " ")}{st.critical && <span className="text-xs font-normal text-muted"> · required</span>}</span>
            <span className="text-muted">{PLAIN[st.state] ?? st.state}: {st.detail}</span>
          </li>
        ))}
      </ol>
      <p className="mt-4 text-xs text-muted">
        Questions about {report.security.name}? The <Link href="/research-chat" className="underline">research assistant</Link> answers
        from this research only and never changes a figure.
      </p>
    </Panel>
  );
}
