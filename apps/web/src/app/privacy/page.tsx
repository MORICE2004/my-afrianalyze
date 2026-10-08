import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = { title: "Privacy & cookies", description: "What AfriEdge stores in your browser and why." };

// A factual description of what this site stores, written from the code. It is not a legal privacy policy; that
// text is the owner's to approve (docs/KNOWN_GAPS.md).
export default function PrivacyPage() {
  return (
    <article className="mx-auto max-w-2xl space-y-6 pb-10 text-sm leading-relaxed">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Privacy &amp; cookies</h1>
        <p className="mt-1 text-muted">What this site keeps in your browser, and what it does not.</p>
      </header>
      <section id="cookies" className="scroll-mt-20 border-t border-line pt-4">
        <h2 className="font-semibold">Cookies: necessary only</h2>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-muted">
          <li><span className="text-fg">Sign-in cookie</span>: set only when you sign in, so the site knows the session is yours. It cannot be read by page scripts and ends when you sign out.</li>
        </ul>
      </section>
      <section className="border-t border-line pt-4">
        <h2 className="font-semibold">Preferences kept on this device</h2>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-muted">
          <li><span className="text-fg">Theme</span>: light or dark.</li>
          <li><span className="text-fg">Recently viewed companies and your watchlist</span>: company names and tickers you chose. They never leave this browser; clear them in Settings.</li>
        </ul>
      </section>
      <section className="border-t border-line pt-4">
        <h2 className="font-semibold">Analytics</h2>
        <p className="mt-2 text-muted">
          AfriEdge sets no analytics or advertising cookies and loads no tracking scripts in your browser, so there is
          nothing to accept or decline here. Our server records a short list of events (for example, that a company&apos;s
          research page was opened, with that company&apos;s ticker) under a scrambled identifier, never your email address.
          If browser analytics are ever added, this page will ask for your consent first.
        </p>
      </section>
    </article>
  );
}
