import Link from "next/link";
import React from "react";
import { Change } from "@/components/ui/kit";
import type { MarketsOverview } from "@/lib/api";
import { fmtCompact, fmtDate, fmtNumber } from "@/lib/format";

// The DSE in one row: index, its move, value traded and breadth, with the session date. Server-rendered.
export function MarketSnapshot({ data }: { data: MarketsOverview }) {
  const dse = data.markets.find((m) => m.exchange === "DSE");
  const idx = dse?.index;
  const act = data.activity;
  const b = data.movers.breadth;
  return (
    <section aria-label="DSE today" data-testid="market-snapshot" className="rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3 sm:px-5">
        <h2 className="text-sm font-semibold">Dar es Salaam Stock Exchange <span className="font-normal text-muted">· TZS</span></h2>
        <span className="text-xs text-muted">
          {data.session.latest_session ? `End of day · session of ${fmtDate(data.session.latest_session)}` : "End-of-day data"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4 p-4 sm:p-5 lg:grid-cols-4">
        <div>
          <div className="text-xs text-muted">DSE All Share Index</div>
          {idx && idx.available ? (
            <>
              <div className="mt-1 text-xl font-semibold">{fmtNumber(idx.value, 2)}</div>
              <div className="text-sm"><Change value={idx.change} label="DSEI one-day change" /> <span className="text-xs text-muted">today</span></div>
            </>
          ) : <div className="mt-1 text-sm text-muted">{idx && !idx.available ? idx.public_reason : "Not available"}</div>}
        </div>
        <div>
          <div className="text-xs text-muted">Year to date</div>
          {idx && idx.available && idx.change_ytd != null ? (
            <div className="mt-1 text-xl font-semibold"><Change value={idx.change_ytd} digits={1} label="DSEI year to date" /></div>
          ) : <div className="mt-1 text-sm text-muted">—</div>}
        </div>
        <div>
          <div className="text-xs text-muted">Value traded</div>
          {act.available ? (
            <>
              <div className="mt-1 text-xl font-semibold">TZS {fmtCompact(act.turnover)}</div>
              <div className="text-xs text-muted">{act.securities_traded} of {act.securities_stored} tracked shares traded</div>
            </>
          ) : <div className="mt-1 text-sm text-muted">{act.public_reason ?? "Not available"}</div>}
        </div>
        <div>
          <div className="text-xs text-muted">Breadth</div>
          {b ? (
            <div className="mt-1 text-xl font-semibold">
              <span className="text-pos">{b.up}</span><span className="text-faint"> / </span><span className="text-neg">{b.down}</span>
              <span className="ml-1 text-xs font-normal text-muted">up / down · {b.unchanged + b.no_trade} flat</span>
            </div>
          ) : <div className="mt-1 text-sm text-muted">—</div>}
        </div>
      </div>
      <div className="border-t border-line px-4 py-2.5 text-right sm:px-5">
        <Link href="/markets" className="text-xs font-medium text-muted hover:text-fg">Open markets →</Link>
      </div>
    </section>
  );
}
