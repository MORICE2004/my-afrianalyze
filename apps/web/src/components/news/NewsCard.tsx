"use client";

import Link from "next/link";
import React, { useState } from "react";
import type { LibraryPhoto as Photo, NewsItem, Relevance } from "@/lib/api";
import { toggleSavedNews, useSavedNews } from "@/lib/local";
import { LibraryPhoto } from "@/components/media/LibraryPhoto";
import { newsTime } from "@/lib/newsTime";
import { TopicArt } from "./TopicArt";

export { newsTime, timeBucket } from "@/lib/newsTime";

const COUNTRY: Record<string, string> = { TZ: "Tanzania", KE: "Kenya", UG: "Uganda" };
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

// The picture area of a story, always the same shape so nothing shifts while loading. In order: the publisher's
// own image when its terms permit it; an openly licensed library photo of the institution or city; an AfriEdge
// topic graphic. If a permitted image fails
// to load, the graphic takes its place, so a broken-image icon never shows.
// `photo` is the library photo the page chose for this story (each used once per page); undefined means the
// story's first suitable photo, null means none.
export function NewsVisual({ item, ratio = "aspect-[16/9]", large = false, photo }: { item: NewsItem; ratio?: string; large?: boolean; photo?: Photo | null }) {
  const [failed, setFailed] = useState(false);
  const img = item.image && !failed && (!large || item.image.width >= 1000) ? item.image : null;
  const art = <figure className={`relative overflow-hidden rounded-md ${ratio}`}><TopicArt id={item.id} topic={item.categories[0]} source={item.source.name} large={large} /></figure>;
  // No publisher image allowed: an openly licensed photo of the publishing institution or the story's city.
  const lib = photo === undefined ? item.photos[0] : photo;
  if (!img && lib) return <LibraryPhoto photo={lib} ratio={ratio} large={large} eager={large} fallback={art} />;
  return (
    <figure className={`relative overflow-hidden rounded-md bg-surface-2 ${ratio}`}>
      {img ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element -- a publisher image whose terms permit display */}
          <img src={img.url} alt="" loading={large ? "eager" : "lazy"} decoding="async" referrerPolicy="no-referrer"
            width={img.width} height={img.height} onError={() => setFailed(true)}
            className="absolute inset-0 h-full w-full object-cover" data-testid="news-image" />
          <figcaption className="absolute bottom-0 right-0 bg-black/55 px-1.5 py-0.5 text-[10px] text-white">Image: {img.credit}</figcaption>
        </>
      ) : <TopicArt id={item.id} topic={item.categories[0]} source={item.source.name} large={large} />}
    </figure>
  );
}

function Meta({ item }: { item: NewsItem }) {
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
      <span className="font-semibold text-fg">{item.source.name}</span>
      <span aria-hidden className="text-faint">·</span>
      <time dateTime={item.published_at}>{newsTime(item.published_at)}</time>
      {item.countries.length > 0 && <><span aria-hidden className="text-faint">·</span><span>{item.countries.map((c) => COUNTRY[c] ?? c).join(", ")}</span></>}
    </div>
  );
}

function SaveButton({ item }: { item: NewsItem }) {
  const saved = useSavedNews().some((s) => s.id === item.id);
  return (
    <button type="button" aria-pressed={saved} data-testid="save-article"
      onClick={() => toggleSavedNews({ id: item.id, title: item.title, source: item.source.name, published_at: item.published_at })}
      className="relative z-10 text-xs font-medium text-muted hover:text-fg">
      {saved ? "Saved" : "Save"}
    </button>
  );
}

function Actions({ item }: { item: NewsItem }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
      <a href={item.url} target="_blank" rel="noopener noreferrer" data-testid="read-original"
        className="relative z-10 text-xs font-medium text-fg underline-offset-4 hover:underline">
        Read on {item.source.name} <span aria-hidden>↗</span>
      </a>
      <SaveButton item={item} />
    </div>
  );
}

const Headline = ({ item, className }: { item: NewsItem; className: string }) => (
  <Link href={`/news/${item.id}`} lang={item.language}
    className={`after:absolute after:inset-0 group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4 ${className}`}>
    {item.title}
  </Link>
);

// The lead story: large visual, large headline, the publisher's summary where allowed.
export function FeaturedStory({ item, photo }: { item: NewsItem; photo?: Photo | null }) {
  return (
    <article data-testid="news-featured" className="group relative grid gap-6 lg:grid-cols-[1.3fr_1fr] lg:items-center">
      <NewsVisual item={item} large photo={photo} />
      <div>
        <div className="flex flex-wrap items-center gap-x-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
          <span>Lead story</span>{item.categories[0] && <span className="text-faint">{item.categories[0]}</span>}
        </div>
        <h2 className="mt-2 text-2xl font-semibold leading-tight tracking-tight text-fg sm:text-[1.875rem]"><Headline item={item} className="" /></h2>
        {item.summary && <p className="mt-3 text-[15px] leading-relaxed text-muted">{item.summary}</p>}
        <div className="mt-4"><Meta item={item} /></div>
        <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2">
          <RelevanceLabel value={item.relevance} reason={item.relevance_reason} />
          <Actions item={item} />
        </div>
      </div>
    </article>
  );
}

// A story in the grid: visual, topic, headline, source, time and region.
export function NewsTile({ item, photo }: { item: NewsItem; photo?: Photo | null }) {
  return (
    <article data-testid="news-card" className="group relative flex flex-col">
      <NewsVisual item={item} photo={photo} />
      <div className="mt-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">{item.categories.slice(0, 2).join(" · ") || "Official release"}</div>
      <h3 className="mt-1 text-[15px] font-semibold leading-snug text-fg"><Headline item={item} className="" /></h3>
      {item.summary && <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted">{item.summary}</p>}
      <div className="mt-2"><Meta item={item} /></div>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
        <RelevanceLabel value={item.relevance} reason={item.relevance_reason} />
        <Actions item={item} />
      </div>
    </article>
  );
}

// A compact row for sidebars (home page, company page).
export function NewsCard({ item }: { item: NewsItem; compact?: boolean }) {
  return (
    <article data-testid="news-card" className="group relative py-4">
      <Meta item={item} />
      <h3 className="mt-1 text-sm font-medium leading-snug text-fg"><Headline item={item} className="" /></h3>
      <div className="mt-2 flex flex-wrap items-center gap-x-4"><RelevanceLabel value={item.relevance} reason={item.relevance_reason} /></div>
    </article>
  );
}
