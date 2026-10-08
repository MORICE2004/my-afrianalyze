import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { FeaturedStory, NewsCard, timeBucket } from "@/components/news/NewsCard";
import { Empty } from "@/components/ui/kit";
import { apiGet, type NewsList } from "@/lib/api";

export const metadata: Metadata = {
  title: "Economic & market news",
  description: "Central-bank, inflation, currency and banking news that can move East African markets, each linked to its source.",
};

const COUNTRIES = [["", "All"], ["TZ", "Tanzania"], ["KE", "Kenya"], ["UG", "Uganda"]] as const;

export default async function NewsPage({ searchParams }: PageProps<"/news">) {
  const sp = await searchParams;
  const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? "";
  const country = /^(TZ|KE|UG)$/.test(one(sp.country)) ? one(sp.country) : "";
  const category = one(sp.category).slice(0, 40);
  const qs = new URLSearchParams({ limit: "30", ...(country && { country }), ...(category && { category }) });
  const res = await apiGet<NewsList>(`/api/v1/news?${qs}`);
  const href = (c: string, cat: string) => {
    const p = new URLSearchParams({ ...(c && { country: c }), ...(cat && { category: cat }) }).toString();
    return p ? `/news?${p}` : "/news";
  };

  if (!res.ok) {
    return (
      <Empty title="News is temporarily unavailable" testId="news-unavailable" action={{ label: "Try again", href: "/news" }}>
        We couldn&apos;t load stories right now. Markets and research pages are unaffected.
      </Empty>
    );
  }
  const d = res.data;
  const now = new Date();
  // The lead is the newest high-relevance story of the last three weeks (one with a publisher image first).
  const recentHigh = d.items.filter((i) => i.relevance === "HIGH" && now.getTime() - new Date(i.published_at).getTime() < 21 * 864e5);
  const lead = recentHigh.find((i) => i.image && i.image.width >= 1000) ?? recentHigh[0];
  const rest = d.items.filter((i) => i !== lead);
  const groups = (["Today", "This week", "Earlier"] as const).map((b) => [b, rest.filter((i) => timeBucket(i.published_at, now) === b)] as const);

  return (
    <div className="grid gap-10 lg:grid-cols-[1fr_17rem]">
      <div className="min-w-0">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight">Economic &amp; market news</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Policy rates, inflation, currencies, banking and government borrowing in Tanzania, Kenya and Uganda: what
            happened, and why it may matter to East African markets.
          </p>
        </header>

        <nav aria-label="Filter news" className="mt-5 flex flex-wrap items-center gap-x-1 gap-y-2 border-b border-line pb-3 text-sm">
          {COUNTRIES.map(([c, l]) => (
            <Link key={c} href={href(c, category)} aria-current={country === c ? "page" : undefined}
              className={`rounded-md px-2.5 py-1 ${country === c ? "bg-surface-2 font-medium text-fg" : "text-muted hover:text-fg"}`}>{l}</Link>
          ))}
          <span aria-hidden className="mx-2 h-4 w-px bg-line" />
          <select aria-label="Topic" defaultValue={category} form="news-topic" name="category"
            className="h-8 rounded-md border border-line bg-surface px-2 text-sm text-fg" data-testid="news-topic">
            <option value="">All topics</option>
            {d.categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <form id="news-topic" action="/news" className="contents">
            {country && <input type="hidden" name="country" value={country} />}
            <button type="submit" className="h-8 rounded-md px-2 text-sm text-muted hover:text-fg">Apply</button>
          </form>
        </nav>

        {d.notice && <p className="mt-3 text-sm text-muted" data-testid="news-notice">{d.notice}</p>}

        {d.items.length === 0 ? (
          <div className="mt-6"><Empty title="No stories match these filters" action={{ label: "Show all news", href: "/news" }}>
            Try another country or topic.</Empty></div>
        ) : (
          <>
            {lead && (
              <section aria-label="Most relevant now" className="mt-6 border-b border-line pb-8" data-testid="news-lead">
                <FeaturedStory item={lead} />
              </section>
            )}
            {groups.map(([label, items]) => items.length > 0 && (
              <section key={label} aria-label={label} className="mt-6">
                <h2 className="border-b border-line pb-2 text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">{label}</h2>
                <div className="divide-y divide-line">{items.map((i) => <NewsCard key={i.id} item={i} />)}</div>
              </section>
            ))}
          </>
        )}
      </div>

      <aside className="space-y-6 text-sm lg:pt-1">
        <section className="border-t border-line pt-3">
          <h2 className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Sources</h2>
          <ul className="mt-2 space-y-1.5" data-testid="news-sources">
            {d.sources.filter((s) => s.connected).map((s) => (
              <li key={s.name} className="flex justify-between gap-2"><span>{s.name}</span><span className="text-xs text-faint">Official</span></li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">
            Other publishers ({d.sources.filter((s) => !s.connected).map((s) => s.name).join(", ")}) are not shown yet: each
            needs a feed AfriEdge is permitted to use.
          </p>
        </section>
        <section className="border-t border-line pt-3">
          <h2 className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">How relevance is set</h2>
          <p className="mt-2 text-xs leading-relaxed text-muted">{d.relevance_method}</p>
          <p className="mt-2 text-xs leading-relaxed text-muted">{d.terms}</p>
        </section>
      </aside>
    </div>
  );
}
