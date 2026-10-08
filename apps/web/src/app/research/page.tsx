import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { SecuritySearch } from "@/components/SecuritySearch";
import { Empty, Panel } from "@/components/ui/kit";
import { apiGet, type Security } from "@/lib/api";

export const metadata: Metadata = {
  title: "Research",
  description: "Search a listed company by name, ticker or ISIN and open its sourced research.",
};

export default async function ResearchPage() {
  const res = await apiGet<{ results: Security[]; count: number }>("/api/v1/securities?limit=200");
  const all = res.ok ? res.data.results : [];
  const researched = all.filter((s) => s.has_report);
  const byExchange = all.reduce<Record<string, Security[]>>((acc, s) => ((acc[s.exchange] ??= []).push(s), acc), {});

  return (
    <div className="space-y-8">
      <section className="mx-auto max-w-3xl pt-2 text-center sm:pt-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Research</h1>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted">
          Choose a company. AfriEdge checks its published reports, values it, and shows the evidence behind every figure.
        </p>
        <div className="mt-5 text-left"><SecuritySearch size="hero" autoFocus /></div>
      </section>

      {!res.ok ? (
        <Empty title="The company list is temporarily unavailable">The data service is not reachable right now. Please try again shortly.</Empty>
      ) : (
        <div className="grid items-start gap-5 lg:grid-cols-3">
          <Panel title="Full research available" className="lg:col-span-2" testId="research-coverage">
            {researched.length === 0 ? <p className="text-sm text-muted">No company has full research yet.</p> : (
              <ul className="-my-2 divide-y divide-line">
                {researched.map((s) => (
                  <li key={s.id}>
                    <Link href={`/report/${encodeURIComponent(s.id)}`} className="flex items-center justify-between gap-3 py-3 hover:text-fg">
                      <span className="min-w-0">
                        <span className="block truncate font-medium">{s.name}</span>
                        <span className="block text-xs text-muted"><span className="font-mono">{s.ticker}</span> · {s.exchange_name ?? s.exchange} · {s.sector}</span>
                      </span>
                      <span className="min-w-0 text-right text-xs text-muted">Statements, valuation, technicals, risks →</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-4 text-xs text-muted">
              Other listed companies open with their price history; their research follows once their annual reports have
              been collected and checked.
            </p>
          </Panel>
          <Panel title="Ask about a company">
            <p className="text-sm text-muted">
              The research assistant answers questions from a company&apos;s research only. It never computes or changes a
              figure, and says so when the research cannot answer.
            </p>
            <Link href="/research-chat" className="mt-3 inline-flex h-9 items-center rounded-md border border-line px-3 text-sm font-medium hover:bg-surface-2">
              Open the research assistant
            </Link>
          </Panel>
        </div>
      )}

      {res.ok && (
        <details className="group rounded-lg border border-line bg-surface" data-testid="browse-all">
          <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium sm:px-5">
            Browse all {all.length} listed companies
            <span className="text-xs text-muted group-open:hidden">Show</span>
            <span className="hidden text-xs text-muted group-open:inline">Hide</span>
          </summary>
          <div className="border-t border-line p-4 sm:p-5">
            {Object.entries(byExchange).map(([ex, list]) => (
              <div key={ex} className="mb-5 last:mb-0">
                <h2 className="mb-2 text-xs font-medium text-muted">{list[0].exchange_name ?? ex} · {list[0].currency}</h2>
                <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable table">
                  <table className="w-full text-sm">
                    <tbody className="divide-y divide-line">
                      {list.map((s) => (
                        <tr key={s.id}>
                          <td className="w-24 py-2 pr-3 font-mono text-xs">{s.ticker}</td>
                          <td className="py-2 pr-3"><Link href={`/report/${encodeURIComponent(s.id)}`} className="hover:underline">{s.name}</Link></td>
                          <td className="py-2 text-right text-xs text-muted">{s.has_report ? "Full research" : "Price only"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
