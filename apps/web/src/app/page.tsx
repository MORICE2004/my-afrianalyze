import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { MarketSnapshot } from "@/components/market/MarketSnapshot";
import { SavedLists } from "@/components/market/SavedLists";
import { SecuritySearch } from "@/components/SecuritySearch";
import { Change, Empty } from "@/components/ui/kit";
import { apiGet, type MarketsOverview, type Quote, type Security } from "@/lib/api";
import { fmtMoney } from "@/lib/format";

export const metadata: Metadata = {
  // The layout's "%s | AfriEdge" template applies to child routes, not to the page beside it, so the home
  // page names the brand itself.
  title: { absolute: "AfriEdge | Research listed African companies" },
  description:
    "Search a listed company and get sourced research: statements, valuation, technicals and risks, each figure linked to its source.",
};

export default async function DashboardPage() {
  const [overview, covered] = await Promise.all([
    apiGet<MarketsOverview>("/api/v1/markets/overview"),
    apiGet<{ results: Security[] }>("/api/v1/securities?limit=200"),
  ]);
  const researched = covered.ok ? covered.data.results.filter((s) => s.has_report) : [];
  const quotes = await Promise.all(researched.map((s) => apiGet<Quote>(`/api/v1/securities/${encodeURIComponent(s.id)}/quote`)));

  return (
    <div className="space-y-8">
      <section className="mx-auto max-w-3xl pt-4 text-center sm:pt-10">
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Research a listed company</h1>
        <p className="mx-auto mt-3 max-w-xl text-sm text-muted sm:text-base">
          Search by name, ticker or ISIN. AfriEdge reads the annual reports, checks the figures, values the company and
          shows where every number came from.
        </p>
        <div className="mt-6 text-left">
          <SecuritySearch size="hero" />
        </div>
      </section>

      {overview.ok ? <MarketSnapshot data={overview.data} /> : (
        <Empty title="Market data is temporarily unavailable" testId="snapshot-unavailable">
          The data service is not reachable right now. Research pages will load again as soon as it is.
        </Empty>
      )}

      <SavedLists />

      {researched.length > 0 && (
        <section aria-labelledby="coverage" className="rounded-xl border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-4 py-3 sm:px-5">
            <h2 id="coverage" className="text-sm font-semibold">Full research available</h2>
            <Link href="/research" className="text-xs text-muted hover:text-fg">All companies →</Link>
          </div>
          <ul className="divide-y divide-line">
            {researched.map((s, i) => {
              const q = quotes[i];
              const quote = q.ok && q.data.available ? q.data : null;
              return (
                <li key={s.id}>
                  <Link href={`/report/${encodeURIComponent(s.id)}`} data-testid={`covered-${s.ticker}`}
                    className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-2/60 sm:px-5">
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{s.name}</span>
                      <span className="block text-xs text-muted"><span className="font-mono">{s.ticker}</span> · {s.exchange} · {s.sector}</span>
                    </span>
                    <span className="shrink-0 text-right">
                      {quote ? (
                        <>
                          <span className="block text-sm font-medium">{fmtMoney(quote.price, quote.currency)}</span>
                          <span className="block text-xs"><Change value={quote.change_pct} label={`${s.ticker} change`} /></span>
                        </>
                      ) : <span className="text-xs text-muted">{s.currency}</span>}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
