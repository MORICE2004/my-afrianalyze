"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { SecuritySearch } from "@/components/SecuritySearch";
import { Change, Empty, Panel } from "@/components/ui/kit";
import { apiGet, type Quote } from "@/lib/api";
import { fmtDate, fmtMoney } from "@/lib/format";
import { toggleWatch, useSavedList } from "@/lib/local";

// The reader's watchlist, kept in this browser. Each row shows the latest stored close from the API.
export default function WatchlistPage() {
  const list = useSavedList("watchlist");
  const [quotes, setQuotes] = useState<Record<string, Quote | null>>({});

  useEffect(() => {
    let live = true;
    list.forEach((s) => {
      apiGet<Quote>(`/api/v1/securities/${encodeURIComponent(s.id)}/quote`).then((r) => {
        if (live) setQuotes((q) => ({ ...q, [s.id]: r.ok ? r.data : null }));
      });
    });
    return () => {
      live = false;
    };
  }, [list]);

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Watchlist</h1>
          <p className="mt-1 text-sm text-muted">Kept in this browser only. Add a company from its research page.</p>
        </div>
        <div className="w-full md:w-96"><SecuritySearch size="compact" /></div>
      </header>
      {list.length === 0 ? (
        <Empty title="Your watchlist is empty" testId="watchlist-empty">
          Open a company and choose “Add to watchlist”. The list stays on this device and is not shared with anyone.
        </Empty>
      ) : (
        <Panel testId="watchlist">
          <div className="-m-4 overflow-x-auto sm:-m-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-xs text-muted">
                  <th className="px-4 py-2.5 text-left font-medium sm:px-5">Company</th>
                  <th className="px-3 py-2.5 text-right font-medium">Last close</th>
                  <th className="px-3 py-2.5 text-right font-medium">Change</th>
                  <th className="px-3 py-2.5 text-right font-medium">Date</th>
                  <th className="px-4 py-2.5 sm:px-5"><span className="sr-only">Remove</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {list.map((s) => {
                  const q = quotes[s.id];
                  return (
                    <tr key={s.id}>
                      <td className="px-4 py-3 sm:px-5">
                        <Link href={`/report/${encodeURIComponent(s.id)}`} className="font-medium hover:underline">{s.name}</Link>
                        <span className="block font-mono text-xs text-muted">{s.id.split(":")[1]} · {s.currency}</span>
                      </td>
                      {q === undefined ? (
                        <td colSpan={3} className="px-3 py-3"><div className="skeleton ml-auto h-4 w-40" /></td>
                      ) : q && q.available ? (
                        <>
                          <td className="px-3 py-3 text-right">{fmtMoney(q.price, q.currency)}</td>
                          <td className="px-3 py-3 text-right"><Change value={q.change_pct} /></td>
                          <td className="px-3 py-3 text-right text-xs text-muted">{fmtDate(q.trade_date)}</td>
                        </>
                      ) : (
                        <td colSpan={3} className="px-3 py-3 text-right text-xs text-muted">{q ? q.public_reason : "Price unavailable right now."}</td>
                      )}
                      <td className="px-4 py-3 text-right sm:px-5">
                        <button type="button" onClick={() => toggleWatch(s)} className="text-xs text-muted hover:text-fg" aria-label={`Remove ${s.name}`}>Remove</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
