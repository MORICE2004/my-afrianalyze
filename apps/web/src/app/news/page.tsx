import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { FeaturedStory, NewsCard, NewsTile } from "@/components/news/NewsCard";
import { SavedStories } from "@/components/news/SavedStories";
import { Empty } from "@/components/ui/kit";
import { apiGet, type NewsItem, type NewsList } from "@/lib/api";

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
  const q = one(sp.q).slice(0, 80);
  const qs = new URLSearchParams({ limit: "31", ...(country && { country }), ...(category && { category }), ...(q && { q }) });
  const res = await apiGet<NewsList>(`/api/v1/news?${qs}`);
  const href = (c: string) => {
    const p = new URLSearchParams({ ...(c && { country: c }), ...(category && { category }), ...(q && { q }) }).toString();
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
  // The API picks the lead by its stated rule (d.lead_rule), shown at the foot of the page.
  const lead = d.items.find((i) => i.id === d.lead_id);
  const rest = d.items.filter((i) => i !== lead).slice(0, 30);
  // The nine newest stories carry their visual; older ones are listed as compact rows, so the page stays readable.
  const tiles = rest.slice(0, 9);
  // Each library photo appears once on the page: every story takes the first of its suitable photos (its
  // institution's, then its country's city) not already used above it; when none is left, the topic graphic.
  const used = new Set<string>();
  const pick = (i: NewsItem) => {
    const p = i.image ? null : i.photos.find((x) => !used.has(x.url)) ?? null;
    if (p) used.add(p.url);
    return p;
  };
  const leadPhoto = lead ? pick(lead) : null;
  const showPhoto = new Map(tiles.map((t) => [t.id, pick(t)] as const));
  const more = rest.slice(9);
  const filtered = !!(country || category || q);

  return (
    <div className="pb-6">
      <header className="flex flex-col gap-4 border-b border-line pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-[1.75rem]">Economic &amp; market news</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted">Policy rates, inflation, currencies, banking and government borrowing in Tanzania, Kenya and Uganda.</p>
        </div>
        <form action="/news" className="flex flex-wrap items-center gap-2" role="search" aria-label="Filter news">
          {country && <input type="hidden" name="country" value={country} />}
          <label className="sr-only" htmlFor="news-q">Search headlines</label>
          <input id="news-q" name="q" defaultValue={q} placeholder="Search headlines" data-testid="news-search"
            className="h-9 w-full rounded-md border border-line bg-surface px-3 text-sm sm:w-56" />
          <label className="sr-only" htmlFor="news-topic">Topic</label>
          <select id="news-topic" name="category" defaultValue={category} data-testid="news-topic"
            className="h-9 rounded-md border border-line bg-surface px-2 text-sm text-fg">
            <option value="">All topics</option>
            {d.categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <button type="submit" className="h-9 rounded-md border border-line-strong px-3 text-sm font-medium hover:bg-surface-2">Apply</button>
        </form>
      </header>

      <nav aria-label="Country" className="mt-3 flex flex-wrap gap-1 text-sm">
        {COUNTRIES.map(([c, l]) => (
          <Link key={c} href={href(c)} aria-current={country === c ? "page" : undefined}
            className={`rounded-md px-2.5 py-1 transition-colors ${country === c ? "bg-surface-2 font-medium text-fg" : "text-muted hover:text-fg"}`}>{l}</Link>
        ))}
        {filtered && <Link href="/news" className="ml-auto rounded-md px-2.5 py-1 text-muted hover:text-fg">Clear filters</Link>}
      </nav>

      {d.notice && <p className="mt-3 text-sm text-muted" data-testid="news-notice">{d.notice}</p>}

      {d.items.length === 0 ? (
        <div className="mt-8"><Empty title="No stories match these filters" testId="news-empty" action={{ label: "Show all news", href: "/news" }}>
          Try another country, topic or search word.</Empty></div>
      ) : (
        <>
          {lead && <section aria-label="Lead story" className="mt-6 border-b border-line pb-10" data-testid="news-lead"><FeaturedStory item={lead} photo={leadPhoto} /></section>}
          {rest.length > 0 && (
            <section aria-labelledby="latest" className="mt-8">
              <h2 id="latest" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Latest</h2>
              <div className="mt-4 grid gap-x-8 gap-y-10 sm:grid-cols-2 xl:grid-cols-3" data-testid="news-grid">
                {tiles.map((i) => <NewsTile key={i.id} item={i} photo={showPhoto.get(i.id)} />)}
              </div>
            </section>
          )}
          {more.length > 0 && (
            <section aria-labelledby="more" className="mt-12">
              <h2 id="more" className="border-b border-line pb-2 text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">More stories</h2>
              <div className="grid gap-x-10 md:grid-cols-2" data-testid="news-more">
                {more.map((i) => <div key={i.id} className="border-b border-line"><NewsCard item={i} /></div>)}
              </div>
            </section>
          )}
        </>
      )}

      <SavedStories />

      <section className="mt-14 grid gap-8 border-t border-line pt-6 text-xs leading-relaxed text-muted md:grid-cols-3">
        <div>
          <h2 className="font-semibold text-fg">Sources</h2>
          <p className="mt-1" data-testid="news-sources">{d.sources.filter((s) => s.connected).map((s) => s.name).join(", ")}. Official publishers only for now; other publishers need a feed AfriEdge may use.</p>
        </div>
        <div>
          <h2 className="font-semibold text-fg">How relevance is set</h2>
          <p className="mt-1">{d.relevance_method} Lead story: {d.lead_rule.charAt(0).toLowerCase() + d.lead_rule.slice(1)}</p>
        </div>
        <div>
          <h2 className="font-semibold text-fg">Images and copyright</h2>
          <p className="mt-1">Headlines and links only; each story opens on the publisher&apos;s site. Publisher images appear only where their terms allow it. Otherwise a story shows an openly licensed photograph of the publishing institution or the city (credited, from Wikimedia Commons), or an AfriEdge topic graphic; neither is a picture of the event itself.</p>
        </div>
      </section>
    </div>
  );
}
