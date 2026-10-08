"use client";

// The visitor's cookie choice. Stored in a necessary first-party cookie (afriedge_consent) for 12 months so the
// web server can read it too. "analytics" is the only optional category AfriEdge has; it is off until the visitor
// turns it on. The choice reaches the API as X-Analytics-Consent: granted, and the API records analytics events
// only then (packages/core/telemetry.py). No browser analytics script exists to load or block.
import { useSyncExternalStore } from "react";

export const CONSENT_COOKIE = "afriedge_consent";
export type Consent = { analytics: boolean; decided_at: string };

const listeners = new Set<() => void>();
let cachedRaw: string | null | undefined;
let cached: Consent | null = null;

function readRaw(): string | null {
  if (typeof document === "undefined") return null;
  const m = document.cookie.match(new RegExp(`(?:^|; )${CONSENT_COOKIE}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

export function readConsent(): Consent | null {
  const raw = readRaw();
  if (raw === cachedRaw) return cached;
  cachedRaw = raw;
  try {
    const v = raw ? JSON.parse(raw) : null;
    cached = v && typeof v.analytics === "boolean" ? { analytics: v.analytics, decided_at: String(v.decided_at ?? "") } : null;
  } catch {
    cached = null;
  }
  return cached;
}

export function saveConsent(analytics: boolean) {
  const value = encodeURIComponent(JSON.stringify({ analytics, decided_at: new Date().toISOString() }));
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${CONSENT_COOKIE}=${value}; Max-Age=${60 * 60 * 24 * 365}; Path=/; SameSite=Lax${secure}`;
  listeners.forEach((l) => l());
}

export function useConsent(): Consent | null | undefined {
  // undefined during server rendering: the banner waits for the browser before deciding whether to show.
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    readConsent,
    () => undefined,
  );
}

// Headers for requests the browser makes to the API.
export function consentHeaders(): Record<string, string> {
  return readConsent()?.analytics ? { "X-Analytics-Consent": "granted" } : {};
}
