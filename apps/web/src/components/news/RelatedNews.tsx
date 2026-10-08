"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Panel, Skeleton } from "@/components/ui/kit";
import { apiGet, type NewsList } from "@/lib/api";
import { newsTime, RelevanceLabel } from "./NewsCard";

// Stories linked to this company by a stated rule (named in the headline, or a sector rule such as a central-bank
// decision in its country). A passing mention is never a link.
export function RelatedNews({ securityId }: { securityId: string }) {
  const [data, setData] = useState<NewsList | null | "error">(null);
  useEffect(() => {
    let live = true;
    apiGet<NewsList>(`/api/v1/news?limit=4&security=${encodeURIComponent(securityId)}`).then((r) => live && setData(r.ok ? r.data : "error"));
    return () => { live = false; };
  }, [securityId]);
  return (
    <Panel title="Related news" testId="related-news" action={<Link href="/news" className="text-xs text-muted hover:text-fg">All news →</Link>}>
      {data === null ? <div className="space-y-2"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-2/3" /></div>
        : data === "error" ? <p className="text-sm text-muted">News is temporarily unavailable.</p>
        : data.items.length === 0 ? <p className="text-sm text-muted">No linked stories yet.</p>
        : (
          <ul className="divide-y divide-line">
            {data.items.map((n) => (
              <li key={n.id} className="py-2.5">
                <div className="text-[11px] text-muted">{n.source.name} · {newsTime(n.published_at)}</div>
                <Link href={`/news/${n.id}`} className="mt-0.5 block text-sm font-medium leading-snug hover:underline underline-offset-4">{n.title}</Link>
                <div className="mt-1"><RelevanceLabel value={n.relevance} reason={n.relevance_reason} /></div>
              </li>
            ))}
          </ul>
        )}
    </Panel>
  );
}
