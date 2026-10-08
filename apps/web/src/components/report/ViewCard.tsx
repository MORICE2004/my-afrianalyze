"use client";

import React from "react";
import { Hint } from "@/components/ui/kit";
import type { Quote, Report } from "@/lib/api";
import { fmtPct, fmtPerShare, fmtSignedPct } from "@/lib/format";

type Rec = Report["header"]["recommendation"];

const TONE: Record<string, string> = {
  BUY: "text-pos", Undervalued: "text-pos", SELL: "text-neg", Overvalued: "text-neg",
  HOLD: "text-fg", "Fairly valued": "text-fg", Inconclusive: "text-muted",
};

function headline(rec: Rec): { word: string; sub: string; tone: string } {
  if (!rec.available) return { word: "No view", sub: "Not enough sourced evidence to form one.", tone: "text-muted" };
  if (rec.model_view === "Inconclusive") {
    return { word: "No view", tone: "text-muted",
      sub: "The result changes with the cost-of-equity method, so no view is given until that is settled." };
  }
  if (rec.trade_label) return { word: rec.trade_label, sub: `Model view: ${rec.model_view}`, tone: TONE[rec.trade_label] };
  return { word: rec.model_view, sub: "Model view", tone: TONE[rec.model_view] ?? "text-fg" };
}

// The investment result first: the view, the price against fair value, and how much to trust it.
// A missing view is shown as "No view" with its reason; it is never filled in.
export function ViewCard({ report, quote }: { report: Report; quote: Quote | null }) {
  const { header, valuation, security } = report;
  const rec = header.recommendation;
  const h = headline(rec);
  const fv = valuation.result;
  const zero = report.beta.zero_volume;
  const cur = security.currency;
  const inconclusive = rec.available && rec.model_view === "Inconclusive";
  return (
    <section aria-label="AfriEdge view" data-testid="model-view" className="rounded-xl border border-line bg-surface">
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl bg-line lg:grid-cols-[1.3fr_1fr_1fr_1fr_1fr]">
        <div className="col-span-2 bg-surface p-4 sm:p-5 lg:col-span-1">
          <div className="text-xs font-medium text-muted">AfriEdge view</div>
          <div className={`mt-1 text-2xl font-semibold tracking-tight ${h.tone}`} data-testid="view-word">{h.word}</div>
          <p className="mt-1 text-xs leading-relaxed text-muted" data-testid={rec.available && rec.inconclusive_reason ? "inconclusive-reason" : undefined}>
            {h.sub}
          </p>
          {rec.available && rec.inconclusive_reason && (
            <Hint content={rec.inconclusive_reason}>
              <button type="button" className="mt-1 text-xs text-muted underline decoration-dotted underline-offset-4">Why?</button>
            </Hint>
          )}
        </div>
        <Cell label="Price" testId="price">
          {quote && quote.available ? `${cur} ${fmtPerShare(quote.price)}` : header.price.available ? `${cur} ${fmtPerShare(header.price.value)}` : "Not shown"}
        </Cell>
        <Cell label="Fair value" testId="fair-value"
          sub={header.fair_value_range.available ? `Range ${fmtPerShare(header.fair_value_range.low)} – ${fmtPerShare(header.fair_value_range.high)}${inconclusive ? "; other methods differ (Valuation tab)" : ""}` : undefined}>
          {fv.available && fv.fair_value !== undefined ? `${cur} ${fmtPerShare(fv.fair_value)}` : "Not available"}
        </Cell>
        <Cell label="Upside to 12-month target" testId="upside"
          sub={header.target_price.available ? `Target ${cur} ${fmtPerShare(header.target_price.value)}${inconclusive ? ", configured method only" : ""}` : undefined}>
          {rec.available ? (
            // When the view is withheld, the upside is shown without colour: it holds under one method, not all.
            <span className={inconclusive ? "text-fg" : Number(rec.price_upside) >= 0 ? "text-pos" : "text-neg"}>{fmtSignedPct(Number(rec.price_upside))}</span>
          ) : "—"}
        </Cell>
        <Cell label="Confidence and liquidity" testId="confidence"
          sub={zero.available && zero.value !== undefined ? `No trade on ${fmtPct(Number(zero.value), 0)} of days` : undefined}>
          <Hint content={<ul className="space-y-1">{header.confidence.notes.map((n) => <li key={n}>{n}</li>)}</ul>}>
            <span tabIndex={0} className="cursor-help">{header.confidence.level}<span className="text-sm font-normal text-muted"> · {Number(header.confidence.score).toFixed(0)}/100</span></span>
          </Hint>
        </Cell>
      </div>
      <p className="border-t border-line px-4 py-2.5 text-[11px] leading-relaxed text-faint sm:px-5">
        A model output from a fixed rule: undervalued if the expected 12-month total return beats the cost of equity by
        more than {fmtPct(report.recommendation_rule.buy_margin)}, overvalued if it falls short by more than{" "}
        {fmtPct(report.recommendation_rule.sell_margin)}. A buy, hold or sell label appears only when the view holds under
        every cost-of-equity method. Not investment advice.
      </p>
    </section>
  );
}

function Cell({ label, children, sub, testId }: { label: string; children: React.ReactNode; sub?: string; testId?: string }) {
  return (
    <div className="bg-surface p-4 sm:p-5" data-testid={testId}>
      <div className="text-xs font-medium text-muted">{label}</div>
      <div className="mt-1 text-xl font-semibold">{children}</div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

// Every fair value the model produces on one scale, with today's price, so the spread of outcomes is visible.
export function ValuationRange({ report, quote }: { report: Report; quote: Quote | null }) {
  const fv = report.valuation.result;
  if (!fv.available || fv.fair_value === undefined) return null;
  const cur = report.security.currency;
  const price = quote && quote.available ? Number(quote.price) : report.header.price.available ? Number(report.header.price.value) : null;
  const marks: { label: string; value: number; kind: "scenario" | "method" | "fair" }[] = [];
  Object.entries(fv.scenarios ?? {}).forEach(([n, s]) => marks.push({ label: `${n[0].toUpperCase()}${n.slice(1)} scenario`, value: Number(s.fair_value), kind: "scenario" }));
  (report.cost_of_equity.alternatives ?? []).forEach((a) => a.fair_value !== undefined && marks.push({ label: a.treatment, value: Number(a.fair_value), kind: "method" }));
  marks.push({ label: "Fair value (configured method)", value: Number(fv.fair_value), kind: "fair" });
  const values = [...marks.map((m) => m.value), ...(price ? [price] : [])];
  const lo = Math.min(...values) * 0.92;
  const hi = Math.max(...values) * 1.05;
  const pos = (v: number) => `${((v - lo) / (hi - lo)) * 100}%`;
  return (
    <figure data-testid="valuation-range" className="space-y-3">
      <figcaption className="text-sm text-muted">Where today&apos;s price sits against every fair value the model produces ({cur} per share).</figcaption>
      <div className="relative h-10">
        <div className="absolute inset-x-0 top-1/2 h-px bg-line-strong" />
        {fv.fair_value_range && (
          <div className="absolute top-1/2 h-2 -translate-y-1/2 rounded bg-surface-2 ring-1 ring-line-strong"
            style={{ left: pos(Number(fv.fair_value_range.low)), width: `calc(${pos(Number(fv.fair_value_range.high))} - ${pos(Number(fv.fair_value_range.low))})` }} />
        )}
        {marks.map((m) => (
          <span key={m.label} title={`${m.label}: ${fmtPerShare(m.value)}`}
            className={`absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full ${m.kind === "fair" ? "h-3.5 w-3.5 bg-fg" : m.kind === "method" ? "h-2.5 w-2.5 border-2 border-fg bg-surface" : "h-2.5 w-2.5 bg-muted"}`}
            style={{ left: pos(m.value) }} />
        ))}
        {price && <span className="absolute top-0 h-full w-0.5 -translate-x-1/2 bg-neg" style={{ left: pos(price) }} title={`Price ${fmtPerShare(price)}`} />}
      </div>
      <ul className="grid gap-x-6 gap-y-1 text-xs sm:grid-cols-2">
        {price && <li className="flex justify-between"><span><span className="mr-2 inline-block h-3 w-0.5 bg-neg align-middle" />Price today</span><span>{fmtPerShare(price)}</span></li>}
        {marks.map((m) => (
          <li key={m.label} className="flex justify-between gap-3">
            <span className="truncate">
              <span className={`mr-2 inline-block rounded-full align-middle ${m.kind === "fair" ? "h-2.5 w-2.5 bg-fg" : m.kind === "method" ? "h-2 w-2 border-2 border-fg" : "h-2 w-2 bg-muted"}`} />
              {m.label}
            </span>
            <span className="shrink-0">{fmtPerShare(m.value)}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}
