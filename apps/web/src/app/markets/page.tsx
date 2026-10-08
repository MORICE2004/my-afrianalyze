import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { PriceChart } from "@/components/market/PriceChart";
import { SecuritySearch } from "@/components/SecuritySearch";
import { Change, Empty, Panel, Pill } from "@/components/ui/kit";
import { apiGet, type IndexSummary, type MarketsOverview, type Mover } from "@/lib/api";
import { fmtCompact, fmtDate, fmtNumber, fmtPct } from "@/lib/format";

export const metadata: Metadata = {
  title: "Markets",
  description: "The Dar es Salaam Stock Exchange at the last session: index, value traded, breadth, movers and sector indices.",
};

function Movers({ title, rows, testId }: { title: string; rows: Mover[]; testId: string }) {
  return (
    <div data-testid={testId}>
      <h3 className="mb-1 text-xs font-medium text-muted">{title}</h3>
      {rows.length === 0 ? <p className="text-sm text-muted">None on this day.</p> : (
        <ul className="divide-y divide-line text-sm">
          {rows.map((m) => (
            <li key={m.security_id}>
              <Link href={`/report/${encodeURIComponent(m.security_id)}`} className="flex items-center justify-between gap-3 py-2 hover:text-fg">
                <span className="min-w-0 truncate">
                  <span className="font-mono font-medium">{m.security_id.replace("DSE:", "")}</span>
                  <span className="ml-2 text-muted">{m.name !== m.security_id.replace("DSE:", "") ? m.name : ""}</span>
                </span>
                <span className="shrink-0 text-right">
                  <span className="mr-3 text-muted">{fmtNumber(m.close, 2)}</span>
                  <Change value={m.change} label={`${m.security_id} change`} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Breadth({ b }: { b: NonNullable<MarketsOverview["movers"]["breadth"]> }) {
  const parts = [
    { n: b.up, label: "up", cls: "bg-pos" },
    { n: b.unchanged + b.no_trade, label: "flat or no trade", cls: "bg-line-strong" },
    { n: b.down, label: "down", cls: "bg-neg" },
  ];
  const total = parts.reduce((a, p) => a + p.n, 0) || 1;
  return (
    <div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-surface-2" role="img"
        aria-label={`${b.up} up, ${b.down} down, ${b.unchanged + b.no_trade} flat or without a trade`}>
        {parts.map((p) => p.n > 0 && <span key={p.label} className={p.cls} style={{ width: `${(p.n / total) * 100}%` }} />)}
      </div>
      <p className="mt-2 text-xs text-muted">
        <span className="text-pos">{b.up} up</span> · <span className="text-neg">{b.down} down</span> · {b.unchanged} unchanged · {b.no_trade} without a trade
        {b.not_updated ? ` · ${b.not_updated} not updated` : ""}
      </p>
    </div>
  );
}

function Sectors({ indices }: { indices: IndexSummary[] }) {
  const ok = indices.filter((i): i is Extract<IndexSummary, { available: true }> => i.available);
  const max = Math.max(0.0001, ...ok.map((i) => Math.abs(Number(i.change_ytd ?? 0))));
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" data-testid="sectors">
        <thead>
          <tr className="border-b border-line text-xs text-muted">
            <th className="py-2 pr-3 text-left font-medium">Sector index</th>
            <th className="px-3 py-2 text-right font-medium">Level</th>
            <th className="px-3 py-2 text-right font-medium">Day</th>
            <th className="px-3 py-2 text-right font-medium">1 month</th>
            <th className="px-3 py-2 text-right font-medium">1 year</th>
            <th className="w-[32%] py-2 pl-3 text-left font-medium">Year to date</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {indices.map((i) => i.available ? (
            <tr key={i.id}>
              <td className="py-2.5 pr-3">{i.name}<span className="ml-2 font-mono text-xs text-faint">{i.id.replace("DSE:", "")}</span></td>
              <td className="px-3 py-2.5 text-right">{fmtNumber(i.value, 2)}</td>
              <td className="px-3 py-2.5 text-right"><Change value={i.change_1d} /></td>
              <td className="px-3 py-2.5 text-right"><Change value={i.change_1m} digits={1} /></td>
              <td className="px-3 py-2.5 text-right"><Change value={i.change_1y} digits={1} /></td>
              <td className="py-2.5 pl-3">
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-surface-2">
                    <div className={`h-2 rounded-full ${Number(i.change_ytd) >= 0 ? "bg-pos" : "bg-neg"}`}
                      style={{ width: `${(Math.abs(Number(i.change_ytd ?? 0)) / max) * 100}%` }} />
                  </div>
                  <Change value={i.change_ytd} digits={1} className="w-20 text-right" />
                </div>
              </td>
            </tr>
          ) : (
            <tr key={i.id}><td className="py-2.5 pr-3">{i.name}</td><td colSpan={5} className="px-3 py-2.5 text-right text-xs text-muted">Not available</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function MarketsPage() {
  const res = await apiGet<MarketsOverview>("/api/v1/markets/overview");
  if (!res.ok) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">Markets</h1>
        <Empty title="Market data is temporarily unavailable">
          The data service is not reachable right now, so no market figures are shown. Please try again shortly.
        </Empty>
      </div>
    );
  }
  const o = res.data;
  const dse = o.markets.find((m) => m.exchange === "DSE")!;
  const others = o.markets.filter((m) => m.exchange !== "DSE");
  const idx = dse.index;
  const act = o.activity;
  const mv = o.movers;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Markets</h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
            <span className="font-medium text-fg">Dar es Salaam Stock Exchange</span>
            <span className="rounded border border-line px-1.5 py-0.5 font-mono text-xs">TZS</span>
            {o.session.latest_session ? (
              <Pill tone="neutral" hint={o.session.note}>End of day · session of {fmtDate(o.session.latest_session)}</Pill>
            ) : <Pill tone="neutral">End-of-day data</Pill>}
          </p>
        </div>
        <div className="w-full md:w-96"><SecuritySearch size="compact" /></div>
      </header>

      <div className="grid items-start gap-5 lg:grid-cols-3">
        <Panel title="DSE All Share Index" className="lg:col-span-2" testId="market-DSE">
          {idx.available ? (
            <>
              <div className="mb-4 flex flex-wrap items-end gap-x-8 gap-y-3">
                <div>
                  <div className="text-3xl font-semibold tracking-tight">{fmtNumber(idx.value, 2)}</div>
                  <div className="text-sm"><Change value={idx.change} label="Change on the day" /> <span className="text-xs text-muted">on {fmtDate(idx.trade_date)}</span></div>
                </div>
                <dl className="flex gap-6 text-sm">
                  <div><dt className="text-xs text-muted">1 month</dt><dd><Change value={idx.change_1m ?? null} digits={1} /></dd></div>
                  <div><dt className="text-xs text-muted">Year to date</dt><dd><Change value={idx.change_ytd ?? null} digits={1} /></dd></div>
                  <div><dt className="text-xs text-muted">1 year</dt><dd><Change value={idx.change_1y ?? null} digits={1} /></dd></div>
                </dl>
              </div>
              <PriceChart instrumentId="DSE:DSEI" label="DSE All Share Index" height={220} />
            </>
          ) : <Empty title="Index not shown">{idx.public_reason}</Empty>}
        </Panel>

        <Panel title="Market activity" testId="activity">
          {act.available ? (
            <div className="space-y-5">
              <dl className="grid grid-cols-2 gap-4">
                <div><dt className="text-xs text-muted">Value traded</dt><dd className="mt-1 text-xl font-semibold">TZS {fmtCompact(act.turnover)}</dd></div>
                <div><dt className="text-xs text-muted">Shares traded</dt><dd className="mt-1 text-xl font-semibold">{fmtCompact(act.volume)}</dd></div>
                <div><dt className="text-xs text-muted">Shares that traded</dt><dd className="mt-1 text-xl font-semibold">{act.securities_traded} <span className="text-sm font-normal text-muted">of {act.securities_stored}</span></dd></div>
                <div><dt className="text-xs text-muted">Market value</dt><dd className="mt-1 text-xl font-semibold">TZS {fmtCompact(act.market_cap)}</dd></div>
              </dl>
              {mv.breadth && <Breadth b={mv.breadth} />}
              <p className="text-[11px] leading-relaxed text-faint">{act.coverage}</p>
            </div>
          ) : <Empty title="Activity not shown">{act.public_reason ?? "Not available."}</Empty>}
        </Panel>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-3">
        <Panel title={`Movers${mv.trade_date ? ` on ${fmtDate(mv.trade_date)}` : ""}`} className="lg:col-span-1">
          {mv.available ? (
            <div className="space-y-5" data-testid="movers">
              <Movers title="Largest rises" rows={mv.gainers ?? []} testId="gainers" />
              <Movers title="Largest falls" rows={mv.losers ?? []} testId="losers" />
              <p className="text-[11px] leading-relaxed text-faint">{mv.note}</p>
            </div>
          ) : <Empty title="Movers not shown">{mv.reason}</Empty>}
        </Panel>
        <Panel title="Sectors" className="lg:col-span-2">
          {o.sectors.available && o.sectors.indices ? (
            <>
              <Sectors indices={o.sectors.indices} />
              <p className="mt-3 text-[11px] leading-relaxed text-faint">{o.sectors.basis}</p>
            </>
          ) : <Empty title="Sector indices not shown">{o.sectors.public_reason ?? o.sectors.reason}</Empty>}
        </Panel>
      </div>

      <section aria-labelledby="other-markets" className="space-y-3">
        <h2 id="other-markets" className="text-sm font-semibold">East African economies and markets</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {[dse, ...others].map((m) => (
            <Panel key={m.market} testId={m.exchange === "DSE" ? "economy-TZ" : `market-${m.exchange}`}
              title={<span>{m.name} <span className="ml-1 rounded border border-line px-1.5 py-0.5 font-mono text-xs font-normal">{m.currency}</span></span>}>
              <p className="text-sm text-muted">{m.exchange === "DSE" ? "Market shown above." : m.index.available ? null : m.index.public_reason}</p>
              {m.macro?.available && m.macro.rows && (
                <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm" data-testid={`macro-${m.market}`}>
                  {m.macro.rows.map((r) => (
                    <div key={r.indicator} className="flex justify-between gap-2 border-b border-line pb-1.5">
                      <dt className="text-muted">{r.label} <span className="text-faint">({r.year})</span></dt>
                      <dd className="font-medium">{r.unit === "decimal" ? fmtPct(Number(r.value), 1) : fmtNumber(r.value, 2)}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {m.macro?.attribution && <p className="mt-3 text-[11px] text-faint">{m.macro.attribution}</p>}
            </Panel>
          ))}
        </div>
      </section>
    </div>
  );
}
