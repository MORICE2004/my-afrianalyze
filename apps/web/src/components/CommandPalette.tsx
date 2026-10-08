"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useRouter } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";
import { apiGet, type Security } from "@/lib/api";
import { useSavedList } from "@/lib/local";

// Ctrl+K / ⌘K: jump to a company or a page without leaving the keyboard. Company results come from the same
// security-master search as the search box; nothing else is fetched.
const PAGES = [
  { label: "Dashboard", href: "/" }, { label: "Markets", href: "/markets" }, { label: "News", href: "/news" },
  { label: "Research", href: "/research" }, { label: "Portfolio", href: "/portfolio" },
  { label: "Watchlist", href: "/watchlist" }, { label: "Fixed income", href: "/fixed-income" },
  { label: "Settings", href: "/settings" },
];

type Row = { key: string; label: string; meta?: string; href: string; group: string };

export function CommandPalette() {
  const router = useRouter();
  const recent = useSavedList("recent");
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [found, setFound] = useState<Security[]>([]);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    const onOpen = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener("afriedge:palette", onOpen);
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener("afriedge:palette", onOpen); };
  }, []);

  useEffect(() => {
    const term = q.trim();
    if (!term) return;
    let cancelled = false;
    const t = setTimeout(async () => {
      const r = await apiGet<{ results: Security[] }>(`/api/v1/securities?limit=6&q=${encodeURIComponent(term)}`);
      if (!cancelled) setFound(r.ok ? r.data.results : []);
    }, 100);
    return () => { cancelled = true; clearTimeout(t); };
  }, [q]);

  const rows = useMemo<Row[]>(() => {
    const term = q.trim().toLowerCase();
    const companies: Row[] = term
      ? found.map((s) => ({ key: s.id, label: s.name, meta: `${s.ticker} · ${s.exchange} · ${s.currency}`, href: `/report/${encodeURIComponent(s.id)}`, group: "Companies" }))
      : recent.slice(0, 5).map((s) => ({ key: s.id, label: s.name, meta: `${s.id.split(":")[1]} · ${s.currency}`, href: `/report/${encodeURIComponent(s.id)}`, group: "Recent" }));
    const pages = PAGES.filter((p) => !term || p.label.toLowerCase().includes(term))
      .map((p) => ({ key: p.href, label: p.label, href: p.href, group: "Go to" }));
    return [...companies, ...pages];
  }, [q, found, recent]);

  const go = (r: Row) => { setOpen(false); setQ(""); router.push(r.href); };

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { setOpen(o); if (!o) setQ(""); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[80] bg-black/30 data-[state=open]:animate-[pop_0.15s_ease-out]" />
        <Dialog.Content aria-describedby={undefined} data-testid="command-palette"
          className="fixed left-1/2 top-[12vh] z-[81] w-[min(36rem,calc(100vw-2rem))] -translate-x-1/2 overflow-hidden rounded-xl border border-line bg-surface shadow-2xl data-[state=open]:animate-[pop_0.18s_ease-out]">
          <Dialog.Title className="sr-only">Search companies and pages</Dialog.Title>
          <input autoFocus value={q} placeholder="Search a company or go to a page…" aria-label="Search a company or go to a page"
            onChange={(e) => { setQ(e.target.value); setActive(0); if (!e.target.value.trim()) setFound([]); }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, rows.length - 1)); }
              else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
              else if (e.key === "Enter" && rows[active]) { e.preventDefault(); go(rows[active]); }
            }}
            className="h-12 w-full border-b border-line bg-transparent px-4 text-[15px] outline-none placeholder:text-faint" />
          <ul role="listbox" className="max-h-[50vh] overflow-y-auto py-1.5">
            {rows.length === 0 && <li className="px-4 py-3 text-sm text-muted">No company or page matched. Try a company name, ticker or ISIN.</li>}
            {rows.map((r, i) => (
              <React.Fragment key={r.group + r.key}>
                {(i === 0 || rows[i - 1].group !== r.group) && <li className="px-4 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wide text-faint">{r.group}</li>}
                <li role="option" aria-selected={i === active} onMouseEnter={() => setActive(i)} onClick={() => go(r)}
                  className={`mx-1.5 flex cursor-pointer items-center justify-between gap-3 rounded-md px-2.5 py-2 text-sm ${i === active ? "bg-surface-2" : ""}`}>
                  <span className="truncate">{r.label}</span>
                  {r.meta && <span className="shrink-0 font-mono text-[11px] text-muted">{r.meta}</span>}
                </li>
              </React.Fragment>
            ))}
          </ul>
          <div className="flex justify-between border-t border-line px-4 py-2 text-[11px] text-faint">
            <span>↑↓ to move · Enter to open</span><span>Esc to close</span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
