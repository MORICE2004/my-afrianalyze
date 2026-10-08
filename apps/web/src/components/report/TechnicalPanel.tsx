import React from "react";
import { NotAvailable } from "@/components/ui/NotAvailable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { DataStatus, Report } from "@/lib/api";
import { fmtPct, fmtPerShare } from "@/lib/format";

type Ind = Record<string, unknown> & { available: boolean; status: DataStatus; reason?: string; formula?: string; window?: number; zero_volume_days?: number };

// Exact decimals arrive as strings; every number is coerced here and only formatted, never computed with.
const n = (v: unknown) => Number(v);

const ROWS: { key: string; label: string; show: (i: Ind) => React.ReactNode }[] = [
  { key: "sma_20", label: "20-day average", show: (i) => <>TZS {fmtPerShare(n(i.value))} · price {String(i.price_vs)}</> },
  { key: "sma_50", label: "50-day average", show: (i) => <>TZS {fmtPerShare(n(i.value))} · price {String(i.price_vs)}</> },
  { key: "sma_200", label: "200-day average", show: (i) => <>TZS {fmtPerShare(n(i.value))} · price {String(i.price_vs)}</> },
  { key: "ema_20", label: "20-day exponential average", show: (i) => <>TZS {fmtPerShare(n(i.value))}</> },
  { key: "rsi_14", label: "RSI (14)", show: (i) => <>{n(i.value).toFixed(1)} · {String(i.zone)}</> },
  { key: "macd", label: "MACD (12, 26, 9)", show: (i) => <>line {n(i.line).toFixed(2)} · signal {n(i.signal).toFixed(2)} · line {String(i.line_vs_signal)} signal</> },
  { key: "bollinger", label: "Bollinger bands (20, 2)", show: (i) => <>{fmtPerShare(n(i.lower))} – {fmtPerShare(n(i.upper))}{i.percent_b != null && <> · %B {n(i.percent_b).toFixed(2)}</>}</> },
  { key: "obv", label: "On-balance volume (60 days)", show: (i) => <>{n(i.change) >= 0 ? "+" : ""}{n(i.change).toLocaleString("en-US", { maximumFractionDigits: 0 })} shares</> },
  { key: "range_52w", label: "52-week range", show: (i) => <>{fmtPerShare(n(i.low))} – {fmtPerShare(n(i.high))} · {fmtPct(n(i.from_high))} from the high</> },
  { key: "atr_14", label: "Average true range (14)", show: (i) => <>TZS {fmtPerShare(n(i.value))} · {fmtPct(n(i.percent_of_price))} of the price</> },
  { key: "adx_14", label: "ADX (14)", show: (i) => <>{n(i.value).toFixed(1)} · {String(i.trend_strength)} trend · +DI {n(i.plus_di).toFixed(1)} / −DI {n(i.minus_di).toFixed(1)}</> },
  { key: "vwap", label: "VWAP (20 days)", show: (i) => <>TZS {fmtPerShare(n(i.value))} · price {String(i.price_vs)}</> },
];

export function TechnicalPanel({ report }: { report: Report }) {
  const t = report.technical;
  if (!t.available) return <NotAvailable reason={t.reason ?? "Technical analysis is not available."} status={t.status} />;
  const ind = t.indicators as Record<string, Ind>;
  return (
    <div className="space-y-4" data-testid="technical">
      <p className="text-sm text-neutral-700">
        Last close TZS {fmtPerShare(n(t.last_close))} on {t.last_trade_date}
        {t.split_adjusted && " (earlier closes adjusted for the share split)"}. {t.liquidity.zero_volume_days} of the last{" "}
        {t.liquidity.window} trading days had no trade; an indicator is withheld when more than{" "}
        {fmtPct(n(t.liquidity.max_zero_volume_share), 0)} of its window had none.
        {t.stale && <> <StatusBadge status="STALE" /> The last close is {t.age_days} days old.</>}
      </p>
      <div className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-xs uppercase tracking-wider text-neutral-500">
            <tr><th className="text-left px-3 py-2">Indicator</th><th className="text-left px-3 py-2">Value</th><th className="text-left px-3 py-2">How</th></tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {ROWS.map(({ key, label, show }) => {
              const i = ind[key];
              if (!i) return null;
              return (
                <tr key={key}>
                  <td className="px-3 py-2 font-medium">{label}</td>
                  <td className="px-3 py-2">{i.available ? show(i) : <NotAvailable compact reason={i.reason ?? ""} status={i.status} />}</td>
                  <td className="px-3 py-2 text-xs text-neutral-500">
                    {i.available ? <>{i.formula} · {i.window} days, {i.zero_volume_days} without a trade</> : i.reason}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-neutral-500">{t.note} All arithmetic is deterministic Python on the closes, highs, lows and turnover the DSE publishes.</p>
    </div>
  );
}
