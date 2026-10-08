"use client";

import Link from "next/link";
import React from "react";
import { Panel } from "@/components/ui/kit";
import { clearList, useSavedList } from "@/lib/local";

// Recently viewed and watchlist, from this browser only. Nothing is shown until the reader has history:
// no sample companies fill the space.
export function SavedLists() {
  const recent = useSavedList("recent");
  const watch = useSavedList("watchlist");
  if (!recent.length && !watch.length) return null;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {watch.length > 0 && (
        <Panel title="Watchlist" testId="watchlist-preview" action={<Link href="/watchlist" className="text-xs text-muted hover:text-fg">View all</Link>}>
          <SecurityLinks items={watch.slice(0, 6)} />
        </Panel>
      )}
      {recent.length > 0 && (
        <Panel title="Recently viewed" testId="recently-viewed"
          action={<button type="button" onClick={() => clearList("recent")} className="text-xs text-muted hover:text-fg">Clear</button>}>
          <SecurityLinks items={recent.slice(0, 6)} />
        </Panel>
      )}
    </div>
  );
}

export function SecurityLinks({ items }: { items: { id: string; name: string; currency: string }[] }) {
  return (
    <ul className="-my-1 divide-y divide-line">
      {items.map((s) => (
        <li key={s.id}>
          <Link href={`/report/${encodeURIComponent(s.id)}`} className="flex items-center justify-between gap-3 py-2 text-sm hover:text-fg">
            <span className="min-w-0 truncate"><span className="font-medium">{s.name}</span></span>
            <span className="shrink-0 font-mono text-xs text-muted">{s.id.split(":")[1]} · {s.currency}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
