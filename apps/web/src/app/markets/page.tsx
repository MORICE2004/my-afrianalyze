import type { Metadata } from "next";
import React from "react";
import { ErrorState, NotAvailable } from "@/components/ui/NotAvailable";
import { apiGet } from "@/lib/api";
import { fmtSignedPct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Regional markets",
  description: "DSE index, breadth and movers from end-of-day exchange data; NSE and USE shown as not yet integrated.",
};

type Overview = {
  markets: {
    market: string; name: string; exchange: string; currency: string; securities_in_master: number;
    index: { available: boolean; id: string; value?: number; trade_date?: string; change?: number; reason?: string; attribution?: string };
  }[];
  commentary: { available: boolean; reason: string };
  // Decimals arrive as strings; coerce with Number() before formatting.
  movers: {
    available: boolean; reason?: string; trade_date?: string; coverage?: string; attribution?: string; note?: string;
    breadth?: { up: number; down: number; unchanged: number; no_trade: number; not_updated: number };
    gainers?: Mover[]; losers?: Mover[];
  };
};
type Mover = { security_id: string; name: string; close: number | string; change: number | string; volume: number | string };

function MoverList({ title, rows }: { title: string; rows: Mover[] }) {
  return (
    <div>
      <h3 className="text-xs font-mono uppercase tracking-widest text-neutral-500 mb-1">{title}</h3>
      {rows.length === 0 ? <p className="text-sm text-neutral-500">None on this day.</p> : (
        <ul className="text-sm divide-y divide-neutral-100">
          {rows.map((m) => (
            <li key={m.security_id} className="flex justify-between gap-3 py-1">
              <span className="truncate">{m.security_id.replace("DSE:", "")} <span className="text-neutral-500">{m.name !== m.security_id.replace("DSE:", "") ? m.name : ""}</span></span>
              <span className="font-mono shrink-0">{fmtSignedPct(Number(m.change), 2)} · {Number(m.close).toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

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
                    <div className="text-2xl">{Number(m.index.value).toLocaleString("en-US", { minimumFractionDigits: 2 })}</div>
                    <div className="text-sm">{fmtSignedPct(Number(m.index.change ?? 0), 2)} · {m.index.trade_date}</div>
                    {m.index.attribution && <div className="mt-1 text-xs text-neutral-500">{m.index.attribution}</div>}
                  </div>
                ) : (
                  <NotAvailable reason={m.index.reason ?? ""} />
                )}
                <p className="mt-3 text-xs text-neutral-500">{m.securities_in_master} {m.securities_in_master === 1 ? "security" : "securities"} in the security master · {m.currency}</p>
              </div>
            ))}
          </div>
          <section>
            <h2 className="font-semibold mb-2">DSE movers{res.data.movers.trade_date ? ` on ${res.data.movers.trade_date}` : ""}</h2>
            {res.data.movers.available && res.data.movers.breadth ? (
              <div className="border border-neutral-200 bg-white p-5 space-y-4" data-testid="movers">
                <p className="text-sm">
                  {res.data.movers.breadth.up} up · {res.data.movers.breadth.down} down · {res.data.movers.breadth.unchanged} unchanged ·{" "}
                  {res.data.movers.breadth.no_trade} did not trade{res.data.movers.breadth.not_updated ? ` · ${res.data.movers.breadth.not_updated} not updated` : ""}.{" "}
                  <span className="text-neutral-500">{res.data.movers.coverage}.</span>
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <MoverList title="Largest rises" rows={res.data.movers.gainers ?? []} />
                  <MoverList title="Largest falls" rows={res.data.movers.losers ?? []} />
                </div>
                <p className="text-xs text-neutral-500">{res.data.movers.note} {res.data.movers.attribution}</p>
              </div>
            ) : (
              <NotAvailable reason={res.data.movers.reason ?? ""} />
            )}
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
