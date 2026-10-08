import Link from "next/link";
import React from "react";
import type { NewsItem, Relevance } from "@/lib/api";

const COUNTRY: Record<string, string> = { TZ: "Tanzania", KE: "Kenya", UG: "Uganda" };
const TZ = "Africa/Dar_es_Salaam";

// Labels come from actual timestamps in East Africa Time. Nothing is ever called "breaking".
export function timeBucket(iso: string, now = new Date()): "Today" | "This week" | "Earlier" {
  const day = (d: Date) => d.toLocaleDateString("en-CA", { timeZone: TZ });
  if (day(new Date(iso)) === day(now)) return "Today";
  return now.getTime() - new Date(iso).getTime() < 7 * 864e5 ? "This week" : "Earlier";
}

export function newsTime(iso: string, now = new Date()): string {
  const d = new Date(iso);
  if (timeBucket(iso, now) === "Today") return `${d.toLocaleTimeString("en-GB", { timeZone: TZ, hour: "2-digit", minute: "2-digit" })} EAT`;
  return d.toLocaleDateString("en-GB", { timeZone: TZ, day: "numeric", month: "short", year: "numeric" });
}

const REL: Record<Relevance, string> = { HIGH: "High", MEDIUM: "Medium", LOW: "Low", NOT_ASSESSED: "Not assessed" };

export function RelevanceLabel({ value, reason }: { value: Relevance; reason?: string }) {
  const strong = value === "HIGH";
  return (
    <span title={reason} data-testid="relevance" data-value={value}
      className={`inline-flex items-center gap-1 text-[11px] ${value === "NOT_ASSESSED" ? "text-faint" : strong ? "font-medium text-fg" : "text-muted"}`}>
      {value !== "NOT_ASSESSED" && (
        <span aria-hidden className="inline-flex gap-px">
          {[1, 2, 3].map((i) => <span key={i} className={`h-2.5 w-[3px] rounded-sm ${i <= ({ HIGH: 3, MEDIUM: 2, LOW: 1 } as const)[value] ? "bg-current" : "bg-line-strong"}`} />)}
        </span>
      )}
      {value === "NOT_ASSESSED" ? "Impact not assessed" : `${REL[value]} relevance`}
    </span>
  );
}

// The picture area of a story, always the same shape. The publisher's own preview image when it has one that is
// large enough; otherwise a plain typographic plate naming the publisher and topic. Never a stock photo, never an
// image AfriEdge made to look like news.
export function NewsVisual({ item, ratio = "aspect-[16/9]", large = false }: { item: NewsItem; ratio?: string; large?: boolean }) {
  // A large slot needs a large image; a smaller one would look soft, so the plate is used instead.
  if (item.image && (!large || item.image.width >= 1000)) {
    return (
      <figure className={`relative overflow-hidden rounded-md bg-surface-2 ${ratio}`}>
        {/* eslint-disable-next-line @next/next/no-img-element -- the publisher's own image, linked rather than copied */}
        <img src={item.image.url} alt="" loading={large ? "eager" : "lazy"} decoding="async" referrerPolicy="no-referrer"
          width={item.image.width} height={item.image.height} className="absolute inset-0 h-full w-full object-cover" data-testid="news-image" />
        <figcaption className="absolute bottom-0 right-0 bg-black/55 px-1.5 py-0.5 text-[10px] text-white">Image: {item.image.credit}</figcaption>
      </figure>
    );
  }
  return (
    <div aria-hidden data-testid="news-plate"
      className={`relative flex flex-col justify-between overflow-hidden rounded-md bg-[#1b1d20] p-4 text-white ring-1 ring-inset ring-white/10 ${ratio}`}>
      <span className={`font-semibold uppercase tracking-[0.08em] text-white/80 ${large ? "text-xs" : "text-[10px]"}`}>{item.source.name}</span>
      <span className={`font-semibold leading-tight tracking-tight text-white/90 ${large ? "text-2xl" : "text-sm"}`}>{item.categories[0] ?? "Official release"}</span>
    </div>
  );
}

function Meta({ item }: { item: NewsItem }) {
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
      <span className="font-semibold text-fg">{item.source.name}</span>
      <span aria-hidden className="text-faint">·</span>
      <time dateTime={item.published_at}>{newsTime(item.published_at)}</time>
      {item.countries.length > 0 && <><span aria-hidden className="text-faint">·</span><span>{item.countries.map((c) => COUNTRY[c] ?? c).join(", ")}</span></>}
      {item.categories[0] && <><span aria-hidden className="text-faint">·</span><span>{item.categories.slice(0, 2).join(", ")}</span></>}
    </div>
  );
}

function ReadLink({ item }: { item: NewsItem }) {
  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer" data-testid="read-original"
      className="relative z-10 text-xs font-medium text-fg underline-offset-4 hover:underline">
      Read on {item.source.name} <span aria-hidden>↗</span>
    </a>
  );
}

// The lead story: large picture, large headline, the publisher's summary where allowed.
export function FeaturedStory({ item }: { item: NewsItem }) {
  return (
    <article data-testid="news-featured" className="group relative grid gap-6 lg:grid-cols-[1.25fr_1fr] lg:items-center">
      <NewsVisual item={item} large />
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">Most relevant now</div>
        <h2 className="mt-2 text-2xl font-semibold leading-tight tracking-tight sm:text-[2rem]" lang={item.language}>
          <Link href={`/news/${item.id}`} className="after:absolute after:inset-0 group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4">{item.title}</Link>
        </h2>
        {item.summary && <p className="mt-3 text-[15px] leading-relaxed text-muted">{item.summary}</p>}
        <div className="mt-4"><Meta item={item} /></div>
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1">
          <RelevanceLabel value={item.relevance} reason={item.relevance_reason} />
          <ReadLink item={item} />
        </div>
      </div>
    </article>
  );
}

// One story in a list: picture, headline, summary, source and time, topic, and the way out to the publisher.
export function NewsCard({ item, compact = false }: { item: NewsItem; compact?: boolean }) {
  if (compact) {
    return (
      <article data-testid="news-card" className="group relative py-4">
        <Meta item={item} />
        <h3 className="mt-1 text-sm font-medium leading-snug text-fg" lang={item.language}>
          <Link href={`/news/${item.id}`} className="after:absolute after:inset-0 group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4">{item.title}</Link>
        </h3>
        <div className="mt-2 flex flex-wrap items-center gap-x-4"><RelevanceLabel value={item.relevance} reason={item.relevance_reason} /><ReadLink item={item} /></div>
      </article>
    );
  }
  return (
    <article data-testid="news-card"
      className={`group relative py-5 ${item.image ? "grid grid-cols-[6.5rem_1fr] gap-4 sm:grid-cols-[13rem_1fr] sm:gap-6" : ""}`}>
      {/* A row shows a picture only when the publisher supplied a real one; otherwise the headline leads alone. */}
      {item.image && <NewsVisual item={item} ratio="aspect-[4/3]" />}
      <div className="min-w-0">
        <h3 className="text-[15px] font-semibold leading-snug text-fg sm:text-lg" lang={item.language}>
          <Link href={`/news/${item.id}`} className="after:absolute after:inset-0 group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4">{item.title}</Link>
        </h3>
        {item.summary && <p className="mt-1.5 line-clamp-2 hidden text-sm leading-relaxed text-muted sm:block">{item.summary}</p>}
        <div className="mt-2"><Meta item={item} /></div>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
          <RelevanceLabel value={item.relevance} reason={item.relevance_reason} />
          {item.companies.length > 0 && <span className="text-[11px] text-muted">Related: {item.companies.map((c) => c.security_id.split(":")[1]).join(", ")}</span>}
          <ReadLink item={item} />
        </div>
      </div>
    </article>
  );
}
