import type { Metadata } from "next";
import React from "react";
import { CookiePreferencesButton } from "@/components/CookiePreferencesButton";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "Cookie policy", description: "The cookies and browser storage AfriEdge uses." };

const ROWS: [string, string, string, string][] = [
  ["afriedge_session", "Necessary", "Keeps you signed in; unreadable by page scripts", "Until you sign out, at most 7 days"],
  ["afriedge_consent", "Necessary", "Remembers your cookie choice", "12 months"],
  ["afriedge-theme (browser storage)", "Necessary", "Light or dark appearance", "Until cleared"],
  ["afriedge-recent, afriedge-watchlist (browser storage)", "Preference", "Companies you viewed or saved; never sent to AfriEdge", "Until cleared"],
];

export default function CookiesPage() {
  return (
    <InfoPage title="Cookie policy" lead="Every cookie and browser-storage item AfriEdge uses, and why." testId="cookies-page">
      <section>
        <h2>What is stored</h2>
        <div className="mt-3 overflow-x-auto" tabIndex={0} role="region" aria-label="Scrollable table">
          <table className="w-full min-w-[34rem] text-sm">
            <thead><tr className="text-left text-xs text-muted"><th className="py-2 pr-3 font-medium">Name</th><th className="py-2 pr-3 font-medium">Type</th><th className="py-2 pr-3 font-medium">Purpose</th><th className="py-2 font-medium">Duration</th></tr></thead>
            <tbody className="divide-y divide-line">
              {ROWS.map((r) => <tr key={r[0]} className="align-top">{r.map((c, i) => <td key={i} className={`py-2 ${i < 3 ? "pr-3" : ""} ${i === 0 ? "font-mono text-xs" : ""}`}>{c}</td>)}</tr>)}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h2>Optional analytics</h2>
        <p>Analytics set no cookie of their own. With your consent, your browser tells AfriEdge&apos;s server it may record usage events; without it, none are recorded. There are no advertising or third-party tracking cookies.</p>
      </section>
      <section>
        <h2>Your choice</h2>
        <p>You can change it at any time.</p>
        <CookiePreferencesButton />
      </section>
    </InfoPage>
  );
}
