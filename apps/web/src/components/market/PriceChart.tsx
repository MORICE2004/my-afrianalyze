"use client";

import { useReducedMotion } from "framer-motion";
import React, { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Change, Empty } from "@/components/ui/kit";
import { apiGet, type PriceSeries } from "@/lib/api";
import { fmtDate, fmtNumber, fmtShortDate } from "@/lib/format";

const RANGES = [
  { key: "1M", days: 31 }, { key: "3M", days: 92 }, { key: "6M", days: 183 },
  { key: "1Y", days: 366 }, { key: "5Y", days: 1830 },
] as const;

// The question it answers: how has the price moved over the period, on comparable (split-adjusted) closes?
export function PriceChart({ instrumentId, currency, label, height = 260, defaultRange = "1Y", testId }: {
  instrumentId: string; currency?: string; label: string; height?: number;
  defaultRange?: (typeof RANGES)[number]["key"]; testId?: string;
}) {
  const reduce = useReducedMotion();
  const [range, setRange] = useState<(typeof RANGES)[number]["key"]>(defaultRange);
  const [data, setData] = useState<PriceSeries | null>(null);
  const [error, setError] = useState<string | null>(null);
  const days = RANGES.find((r) => r.key === range)!.days;

  useEffect(() => {
    let live = true;
    apiGet<PriceSeries>(`/api/v1/prices/${encodeURIComponent(instrumentId)}?days=${days}`).then((res) => {
      if (!live) return;
      if (res.ok) {
        setData(res.data);
        setError(null);
      } else {
        setError("The price history is not available right now.");
      }
    });
    return () => {
      live = false;
    };
  }, [instrumentId, days]);

  const points = useMemo(
    () => (data && data.available ? data.points.map((p) => ({ date: p.date, close: Number(p.close) })) : []),
    [data],
  );
  const change = points.length > 1 ? points[points.length - 1].close / points[0].close - 1 : null;
  const dir = change === null ? "flat" : change >= 0 ? "pos" : "neg";
  const stroke = dir === "neg" ? "var(--neg)" : "var(--chart-1)";

  return (
    <figure data-testid={testId} aria-label={`${label} price chart`}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <figcaption className="text-sm text-muted">
          {points.length > 1 ? (
            <>Over {range}: <Change value={change} label={`${label} change over ${range}`} /></>
          ) : (
            <span>&nbsp;</span>
          )}
        </figcaption>
        <div role="group" aria-label="Chart range" className="inline-flex rounded-md border border-line p-0.5">
          {RANGES.map((r) => (
            <button key={r.key} type="button" onClick={() => setRange(r.key)} aria-pressed={range === r.key}
              className={`rounded px-2 py-1 text-xs transition-colors ${range === r.key ? "bg-selected text-on-selected" : "text-muted hover:text-fg"}`}>
              {r.key}
            </button>
          ))}
        </div>
      </div>
      {error ? (
        <Empty title="Price history unavailable">{error}</Empty>
      ) : data === null ? (
        <div className="skeleton w-full" style={{ height }} aria-hidden />
      ) : !data.available ? (
        <Empty title="Price history not shown">{data.public_reason}</Empty>
      ) : (
        <div style={{ height }} className="w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id={`fill-${instrumentId}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={stroke} stopOpacity={0.14} />
                  <stop offset="100%" stopColor={stroke} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
              <XAxis dataKey="date" tickFormatter={fmtShortDate} tick={{ fill: "var(--faint)", fontSize: 11 }}
                axisLine={false} tickLine={false} minTickGap={40} />
              <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--faint)", fontSize: 11 }} axisLine={false} tickLine={false}
                width={56} tickFormatter={(v) => fmtNumber(v)} />
              <Tooltip
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 8, fontSize: 12, color: "var(--fg)" }}
                labelFormatter={(d) => fmtDate(String(d))}
                formatter={(v) => [`${currency ? currency + " " : ""}${fmtNumber(Number(v), 2)}`, "Close"]}
              />
              <Area type="monotone" dataKey="close" stroke={stroke} strokeWidth={1.75} fill={`url(#fill-${instrumentId})`}
                isAnimationActive={!reduce} animationDuration={700} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
      {data && data.available && (
        <p className="mt-2 text-[11px] leading-relaxed text-faint">
          End-of-day closes{data.notes.length ? ", adjusted: " + data.notes.join(" ") : "."}
        </p>
      )}
    </figure>
  );
}
