import type { Metadata } from "next";
import React from "react";
import { ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import { apiGet } from "@/lib/api";
import { fmtSignedPct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Regional markets",
  description: "DSE, NSE and USE index levels and market data, shown only when sourced data is loaded.",
};

type Overview = {
  markets: {
    market: string; name: string; exchange: string; currency: string; securities_in_master: number;
    index: { available: boolean; id: string; value?: number; trade_date?: string; change?: number; reason?: string };
  }[];
  commentary: { available: boolean; reason: string };
  movers: { available: boolean; reason: string };
};

export default async function MarketsPage() {
  const res = await apiGet<Overview>("/api/v1/markets/overview");
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold tracking-tight">Regional markets</h1>
      {!res.ok ? (
        <ErrorState message={res.error} />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {res.data.markets.map((m) => (
              <div key={m.market} className="border border-neutral-200 bg-white p-5" data-testid={`market-${m.exchange}`}>
                <div className="flex justify-between items-start">
                  <h2 className="text-xl font-bold">{m.exchange}</h2>
                  <span className="text-xs text-neutral-500">{m.name}</span>
                </div>
                <div className="mt-4 text-xs text-neutral-500 font-mono">{m.index.id}</div>
                {m.index.available && m.index.value !== undefined ? (
                  <div className="font-mono">
                    <div className="text-2xl">{m.index.value.toLocaleString()}</div>
                    <div className="text-sm">{fmtSignedPct(m.index.change ?? 0, 2)} · {m.index.trade_date}</div>
                  </div>
                ) : (
                  <NotAvailable reason={m.index.reason ?? ""} />
                )}
                <p className="mt-3 text-xs text-neutral-500">{m.securities_in_master} securities in the security master · {m.currency}</p>
              </div>
            ))}
          </div>
          <section>
            <h2 className="font-semibold mb-2">Top movers</h2>
            <NotAvailable reason={res.data.movers.reason} />
          </section>
          <section>
            <h2 className="font-semibold mb-2">Market commentary</h2>
            <NotAvailable reason={res.data.commentary.reason} />
          </section>
        </>
      )}
    </div>
  );
}
