import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { RelevanceLabel } from "@/components/news/NewsCard";
import { newsTime } from "@/lib/newsTime";
import { Empty } from "@/components/ui/kit";
import { apiGet, type NewsDetail } from "@/lib/api";
import { fmtDate, fmtNumber, fmtPct } from "@/lib/format";

const COUNTRY: Record<string, string> = { TZ: "Tanzania", KE: "Kenya", UG: "Uganda" };

async function load(id: string) {
  return /^[0-9a-f]{40}$/.test(id) ? apiGet<NewsDetail>(`/api/v1/news/${id}`) : null;
}

export async function generateMetadata({ params }: PageProps<"/news/[id]">): Promise<Metadata> {
  const res = await load((await params).id);
  return { title: res && res.ok ? res.data.title : "Story", robots: { index: false } };
}

function indicatorValue(v: string, unit: string) {
  if (unit === "decimal") return fmtPct(Number(v));
  return fmtNumber(Number(v), 2);
}

// A story in AfriEdge's context: the publisher's headline and link, then the indicators, markets and companies it
// may touch. The link to each is a stated rule, not a prediction.
export default async function NewsStory({ params }: PageProps<"/news/[id]">) {
  const res = await load((await params).id);
  if (!res || !res.ok) {
    return (
      <Empty title="Story not found" action={{ label: "Back to news", href: "/news" }}>
        It may have been removed from the news cache. Every story links to its publisher, where the original stays available.
      </Empty>
    );
  }
  const n = res.data;
  return (
    <article className="mx-auto max-w-3xl pb-10" data-testid="news-story">
      <Link href="/news" className="text-xs text-muted hover:text-fg">← News</Link>
      <div className="mt-4 flex flex-wrap items-center gap-x-2 text-[11px] text-muted">
        <span className="font-semibold uppercase tracking-wide text-fg">{n.source.name}</span>
        {n.source.tier_label && <span className="text-faint">{n.source.tier_label}</span>}
        <span aria-hidden>·</span><time dateTime={n.published_at}>Published {newsTime(n.published_at)}</time>
        <span aria-hidden>·</span><span>Retrieved {fmtDate(n.retrieved_at)}</span>
      </div>
      <h1 className="mt-2 text-2xl font-semibold leading-tight tracking-tight" lang={n.language}>{n.title}</h1>
      <div className="mt-2 flex flex-wrap gap-x-3 text-sm text-muted">
        <span>{n.countries.map((c) => COUNTRY[c] ?? c).join(", ") || "Region not identified"}</span>
        {n.categories.length > 0 && <><span aria-hidden>·</span><span>{n.categories.join(", ")}</span></>}
      </div>
      {n.summary && <p className="mt-4 text-[15px] leading-relaxed">{n.summary} <span className="text-xs text-muted">({n.source.name})</span></p>}
      <a href={n.url} target="_blank" rel="noreferrer" data-testid="read-source"
        className="mt-5 inline-flex h-9 items-center rounded-md bg-selected px-4 text-sm font-medium text-on-selected hover:opacity-90">
        Read on {n.source.name} <span aria-hidden className="ml-1">↗</span>
      </a>

      <section className="mt-10 border-t border-line pt-4" aria-labelledby="why">
        <h2 id="why" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Why it may matter to East African markets</h2>
        <div className="mt-2"><RelevanceLabel value={n.relevance} /></div>
        <p className="mt-2 text-sm leading-relaxed">{n.why_it_matters ?? "AfriEdge has not assessed this story: its headline names no economic variable that AfriEdge tracks for Tanzania, Kenya or Uganda."}</p>
        <p className="mt-2 text-xs text-muted">{n.caution}</p>
      </section>

      {n.indicators.length > 0 && (
        <section className="mt-8 border-t border-line pt-4" aria-labelledby="ind">
          <h2 id="ind" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Related indicators</h2>
          <table className="mt-2 w-full text-sm" data-testid="news-indicators">
            <tbody className="divide-y divide-line">
              {n.indicators.map((i) => (
                <tr key={i.series_id}>
                  <td className="py-2 pr-3">{i.label}</td>
                  {i.available ? (
                    <>
                      <td className="py-2 pr-3 text-right font-medium tabular-nums">{indicatorValue(i.value, i.unit)}</td>
                      <td className="py-2 text-right text-xs text-muted">
                        {fmtDate(i.date)} · <a href={i.source_url.startsWith("http") ? i.source_url.split(" ")[0] : undefined} target="_blank" rel="noreferrer" className="underline underline-offset-4">source</a>
                      </td>
                    </>
                  ) : <td colSpan={2} className="py-2 text-right text-xs text-muted">{i.reason}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {n.markets.length > 0 && (
        <section className="mt-8 border-t border-line pt-4" aria-labelledby="mk">
          <h2 id="mk" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Related markets</h2>
          <ul className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm">
            {n.markets.map((m) => (
              <li key={m.exchange}>
                {m.exchange === "DSE" ? <Link href="/markets" className="underline underline-offset-4">{m.exchange}</Link> : m.exchange} · {COUNTRY[m.country]} · <span className="font-mono text-xs">{m.currency}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8 border-t border-line pt-4" aria-labelledby="co">
        <h2 id="co" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Related companies</h2>
        {n.related_companies.length === 0 ? (
          <p className="mt-2 text-sm text-muted">None. A company is linked only when the headline names it, or by a stated sector rule.</p>
        ) : (
          <ul className="mt-2 divide-y divide-line" data-testid="news-companies">
            {n.related_companies.map((c) => (
              <li key={c.security_id} className="flex flex-wrap items-baseline justify-between gap-2 py-2.5 text-sm">
                <Link href={`/report/${encodeURIComponent(c.security_id)}`} className="font-medium hover:underline underline-offset-4">
                  {c.name} <span className="font-mono text-xs text-muted">{c.ticker} · {c.exchange} · {c.currency}</span>
                </Link>
                <span className="text-xs text-muted">{c.why}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
