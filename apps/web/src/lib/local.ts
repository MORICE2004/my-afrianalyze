"use client";

// Lists kept in this browser only: recently viewed companies and the watchlist. They hold security ids and
// names the reader chose, nothing else, never leave the device and are not sent to analytics. Storage can be
// blocked (private windows, strict settings), so every access is guarded and the pages work without it.
import { useSyncExternalStore } from "react";

export type SavedSecurity = { id: string; name: string; currency: string };

const KEYS = { recent: "afriedge-recent", watchlist: "afriedge-watchlist" } as const;
type ListName = keyof typeof KEYS;
const MAX = { recent: 8, watchlist: 50 };
const EMPTY: SavedSecurity[] = [];
const listeners = new Set<() => void>();
const cache: Partial<Record<ListName, { raw: string | null; value: SavedSecurity[] }>> = {};

function read(name: ListName): SavedSecurity[] {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(KEYS[name]);
  } catch {
    return EMPTY;
  }
  const hit = cache[name];
  if (hit && hit.raw === raw) return hit.value;            // same snapshot object while nothing changed
  let value: SavedSecurity[] = EMPTY;
  try {
    const parsed = raw ? JSON.parse(raw) : [];
    if (Array.isArray(parsed)) {
      value = parsed.filter((x) => x && typeof x.id === "string" && typeof x.name === "string").slice(0, MAX[name]);
    }
  } catch {
    value = EMPTY;
  }
  cache[name] = { raw, value };
  return value;
}

function write(name: ListName, items: SavedSecurity[]) {
  try {
    window.localStorage.setItem(KEYS[name], JSON.stringify(items.slice(0, MAX[name])));
  } catch {
    // storage blocked: the list simply is not kept
  }
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  const onStorage = () => cb();
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

export function useSavedList(name: ListName): SavedSecurity[] {
  return useSyncExternalStore(subscribe, () => read(name), () => EMPTY);
}

export function rememberViewed(s: SavedSecurity) {
  write("recent", [s, ...read("recent").filter((x) => x.id !== s.id)]);
}

export function toggleWatch(s: SavedSecurity): boolean {
  const list = read("watchlist");
  const on = list.some((x) => x.id === s.id);
  write("watchlist", on ? list.filter((x) => x.id !== s.id) : [s, ...list]);
  return !on;
}

export function clearList(name: ListName) {
  write(name, []);
}

// Saved news stories: headline, source, time and id only, in this browser. Never sent anywhere.
export type SavedNews = { id: string; title: string; source: string; published_at: string };
const NEWS_KEY = "afriedge-saved-news";
const NO_NEWS: SavedNews[] = [];
let newsCache: { raw: string | null; value: SavedNews[] } = { raw: null, value: NO_NEWS };

function readNews(): SavedNews[] {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(NEWS_KEY);
  } catch {
    return NO_NEWS;
  }
  if (raw === newsCache.raw) return newsCache.value;
  let value = NO_NEWS;
  try {
    const parsed = raw ? JSON.parse(raw) : [];
    value = Array.isArray(parsed) ? parsed.filter((x) => x && typeof x.id === "string").slice(0, 100) : NO_NEWS;
  } catch { /* corrupted entry: start again */ }
  newsCache = { raw, value };
  return value;
}

export function useSavedNews(): SavedNews[] {
  return useSyncExternalStore(subscribe, readNews, () => NO_NEWS);
}

export function toggleSavedNews(n: SavedNews): boolean {
  const list = readNews();
  const on = list.some((x) => x.id === n.id);
  try {
    window.localStorage.setItem(NEWS_KEY, JSON.stringify(on ? list.filter((x) => x.id !== n.id) : [n, ...list]));
  } catch { /* storage blocked */ }
  listeners.forEach((l) => l());
  return !on;
}
