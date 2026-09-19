"use client";

import { useRouter } from "next/navigation";
import React, { useEffect, useId, useState } from "react";
import { apiGet, type Security } from "@/lib/api";

export function SecuritySearch() {
  const router = useRouter();
  const listId = useId();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Security[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [error, setError] = useState("");
  const [active, setActive] = useState(0);

  const onChange = (value: string) => {
    setQuery(value);
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
      const res = await apiGet<{ results: Security[] }>(`/api/v1/securities?q=${encodeURIComponent(q)}`);
      if (cancelled) return; // a newer query replaced this one
      if (res.ok) {
        setResults(res.data.results);
        setStatus("done");
        setActive(0);
      } else {
        setResults([]);
        setError(res.error);
        setStatus("error");
      }
    }, 150);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [query]);

  const open = (s: Security) => router.push(`/report/${encodeURIComponent(s.id)}`);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[active]) open(results[active]);
    }
  };

  const showList = query.trim().length > 0;

  return (
    <div className="relative">
      <label htmlFor="security-search" className="sr-only">Search listed companies by ticker or name</label>
      <input
        id="security-search"
        type="search"
        role="combobox"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        value={query}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Search by ticker or company, e.g. NMB"
        className="block w-full px-4 py-4 border border-neutral-300 bg-white text-lg font-mono placeholder-neutral-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black"
      />
      {showList && (
        <div id={listId} role="listbox" className="absolute z-20 mt-1 w-full border border-neutral-300 bg-white shadow-md">
          {status === "loading" && <div className="px-4 py-3 text-sm text-neutral-500">Searching…</div>}
          {status === "error" && <div className="px-4 py-3 text-sm text-red-700">{error}</div>}
          {status === "done" && results.length === 0 && (
            <div className="px-4 py-3 text-sm text-neutral-600" data-testid="search-no-results">
              No listed company matches “{query.trim()}”. Coverage is currently DSE, NSE and USE names in the security master.
            </div>
          )}
          {status === "done" &&
            results.map((s, i) => (
              <button
                type="button"
                role="option"
                aria-selected={i === active}
                key={s.id}
                onMouseEnter={() => setActive(i)}
                onClick={() => open(s)}
                className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm ${i === active ? "bg-neutral-100" : ""}`}
              >
                <span>
                  <span className="font-mono font-semibold">{s.id}</span>
                  <span className="ml-3 text-neutral-700">{s.name}</span>
                </span>
                <span className="text-xs text-neutral-500">
                  {s.has_report ? "Report available" : "No report yet"}
                </span>
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
