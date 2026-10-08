"use client";

import { useRouter } from "next/navigation";
import React, { useEffect, useId, useRef, useState } from "react";
import { Stagger, StaggerItem, VerifiedCheck } from "@/components/motion/primitives";
import { apiGet, type Security } from "@/lib/api";

// Company search over AfriEdge's security master: name, ticker or ISIN, ranked by the API (exact ticker or ISIN,
// prefixes, name words, then close spellings). It is a plain database lookup; nothing expensive runs until a
// company is chosen and its research page opens.
export function SecuritySearch({ size = "hero", autoFocus = false }: { size?: "hero" | "compact"; autoFocus?: boolean }) {
  const router = useRouter();
  const listId = useId();
  const inputId = useId();
  const wrap = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Security[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(false);
  // Enter pressed before the results for the current text arrived: open the first result when they do.
  const pendingEnter = useRef(false);

  function choose(s: Security) {
    setOpen(false);
    setQuery("");
    router.push(`/report/${encodeURIComponent(s.id)}`);
  }

  const onChange = (value: string) => {
    pendingEnter.current = false;
    setQuery(value);
    setOpen(true);
    if (value.trim()) {
      setStatus("loading");
    } else {
      setResults([]);
      setStatus("idle");
    }
  };

  useEffect(() => {
    const q = query.trim();
    if (!q) return;
    let cancelled = false;
    const t = setTimeout(async () => {
      const res = await apiGet<{ results: Security[] }>(`/api/v1/securities?limit=8&q=${encodeURIComponent(q)}`);
      if (cancelled) return; // a newer query replaced this one
      if (res.ok) {
        setResults(res.data.results);
        setStatus("done");
        setActive(0);
        const first = res.data.results[0];
        if (pendingEnter.current && first) {
          pendingEnter.current = false;
          setOpen(false);
          setQuery("");
          router.push(`/report/${encodeURIComponent(first.id)}`);
        }
      } else {
        setResults([]);
        setError("Search is not available right now. Please try again shortly.");
        setStatus("error");
      }
    }, 120);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [query, router]);

  // Close the list when focus or a click goes elsewhere.
  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);


  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (status === "loading") pendingEnter.current = true;
      else if (results[active]) choose(results[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const showList = open && query.trim().length > 0;
  const hero = size === "hero";
  const optionId = (i: number) => `${listId}-opt-${i}`;

  return (
    <div className="relative w-full" ref={wrap}>
      <label htmlFor={inputId} className="sr-only">Search companies, tickers or ISINs</label>
      <div className="relative">
        <svg className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-faint ${hero ? "left-4" : "left-3"}`}
          width={hero ? 18 : 15} height={hero ? 18 : 15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
          <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
        </svg>
        <input
          id={inputId}
          type="search"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList && results[active] ? optionId(active) : undefined}
          autoComplete="off"
          spellCheck={false}
          autoFocus={autoFocus}
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search companies, tickers or ISINs"
          data-testid={hero ? "search-hero" : "search-compact"}
          className={`block w-full rounded-lg border border-line bg-surface text-fg placeholder:text-faint transition-colors focus:border-fg focus:outline-none ${
            hero ? "h-14 pl-12 pr-4 text-base sm:text-lg shadow-sm" : "h-9 pl-9 pr-3 text-sm"}`}
        />
      </div>
      {showList && (
        <div id={listId} role="listbox" aria-label="Companies"
          className="absolute z-40 mt-1.5 w-full overflow-hidden rounded-lg border border-line bg-surface shadow-lg">
          {status === "loading" && results.length === 0 && (
            <div className="space-y-2 p-3" aria-hidden>
              {[0, 1, 2].map((i) => <div key={i} className="skeleton h-9" />)}
            </div>
          )}
          {status === "error" && <div className="px-4 py-3 text-sm text-neg">{error}</div>}
          {status === "done" && results.length === 0 && (
            <div className="px-4 py-3 text-sm text-muted" data-testid="search-no-results">
              <span className="font-medium text-fg">No company matched “{query.trim()}”.</span> Try a company name, ticker or
              ISIN. AfriEdge covers companies listed in Tanzania today; Kenya and Uganda are being added.
            </div>
          )}
          <Stagger key={results.map((r) => r.id).join()}>
          {results.map((s, i) => (
            <StaggerItem key={s.id}>
            <div
              role="option"
              id={optionId(i)}
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => choose(s)}
              className={`flex cursor-pointer items-center justify-between gap-3 px-4 py-2.5 text-sm transition-colors ${i === active ? "bg-surface-2" : ""}`}
            >
              <span className="min-w-0">
                <span className="block truncate font-medium text-fg">{s.name}</span>
                <span className="block truncate text-xs text-muted">
                  <span className="font-mono">{s.ticker}</span> · {s.exchange}{s.country ? ` · ${s.country}` : ""}
                </span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[11px] text-muted">{s.currency}</span>
                {s.has_report && (
                  <span className="hidden items-center gap-1 text-[11px] text-fg sm:inline-flex" title="Full research: statements checked against the annual reports">
                    <VerifiedCheck size={12} />Research
                  </span>
                )}
              </span>
            </div>
            </StaggerItem>
          ))}
          </Stagger>
        </div>
      )}
    </div>
  );
}
