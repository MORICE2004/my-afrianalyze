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

// One story: source, headline, time, place and topic, and two ways out (our context, the publisher's article).
export function NewsCard({ item, compact = false }: { item: NewsItem; compact?: boolean }) {
  return (
    <article data-testid="news-card" className="group relative py-4">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted">
        <span className="font-semibold uppercase tracking-wide text-fg">{item.source.name}</span>
        {item.source.tier_label && <span className="text-faint">{item.source.tier_label}</span>}
        <span aria-hidden className="text-faint">·</span>
        <time dateTime={item.published_at}>{newsTime(item.published_at)}</time>
        {item.countries.length > 0 && <><span aria-hidden className="text-faint">·</span><span>{item.countries.map((c) => COUNTRY[c] ?? c).join(", ")}</span></>}
        {item.categories[0] && <><span aria-hidden className="text-faint">·</span><span>{item.categories.slice(0, 2).join(", ")}</span></>}
      </div>
      <h3 className={`mt-1 font-medium leading-snug text-fg ${compact ? "text-sm" : "text-[15px]"}`} lang={item.language}>
        <Link href={`/news/${item.id}`} className="after:absolute after:inset-0 group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4">
          {item.title}
        </Link>
      </h3>
      {!compact && item.summary && <p className="mt-1 line-clamp-2 max-w-3xl text-sm text-muted">{item.summary}</p>}
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
        <RelevanceLabel value={item.relevance} reason={item.relevance_reason} />
        {!compact && item.companies.length > 0 && (
          <span className="text-[11px] text-muted">Related: {item.companies.map((c) => c.security_id.split(":")[1]).join(", ")}</span>
        )}
        <a href={item.url} target="_blank" rel="noreferrer" className="relative z-10 text-[11px] font-medium text-fg hover:underline underline-offset-4">
          Read article <span aria-hidden>↗</span>
        </a>
      </div>
    </article>
  );
}
