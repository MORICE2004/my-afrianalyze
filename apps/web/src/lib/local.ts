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
