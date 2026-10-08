"use client";

import Link from "next/link";
import React from "react";
import { toggleSavedNews, useSavedNews } from "@/lib/local";
import { newsTime } from "./NewsCard";

// Stories the reader saved, kept in this browser only.
export function SavedStories() {
  const saved = useSavedNews();
  if (saved.length === 0) return null;
  return (
    <section aria-labelledby="saved-news" className="mt-12 border-t border-line pt-4" data-testid="saved-stories">
      <h2 id="saved-news" className="text-[13px] font-semibold uppercase tracking-[0.04em] text-muted">Saved stories</h2>
      <ul className="mt-2 divide-y divide-line">
        {saved.map((n) => (
          <li key={n.id} className="flex items-baseline justify-between gap-4 py-2.5 text-sm">
            <Link href={`/news/${n.id}`} className="min-w-0 truncate font-medium hover:underline underline-offset-4">{n.title}</Link>
            <span className="flex shrink-0 items-center gap-3 text-xs text-muted">
              {n.source} · {newsTime(n.published_at)}
              <button type="button" onClick={() => toggleSavedNews(n)} className="hover:text-fg">Remove</button>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
