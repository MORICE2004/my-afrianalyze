import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "Privacy policy", description: "What AfriEdge collects, why, and the choices you have." };

// A factual description written from the code. The owner's legal review is still pending (docs/KNOWN_GAPS.md).
export default function PrivacyPage() {
  return (
    <InfoPage title="Privacy policy" lead="What AfriEdge collects, why, and the choices you have." testId="privacy-page">
      <section><h2>Account</h2>
        <p>If you create an account, AfriEdge stores your email address and a one-way hash of your password (Argon2id). Your saved portfolios are visible only to your account.</p></section>
      <section><h2>On your device</h2>
        <p>Your theme, the companies you viewed recently and your watchlist are kept in this browser only. They are never sent to AfriEdge; clear them in Settings.</p></section>
      <section><h2>Analytics, only with your consent</h2>
        <p>If you accept analytics, AfriEdge&apos;s server records a short list of events, for example that a company&apos;s research page was opened, with that company&apos;s ticker, under a scrambled identifier, never your email address. If you reject them, nothing is recorded. No advertising or tracking scripts run in your browser.</p></section>
      <section><h2>Cookies</h2>
        <p>See the <Link href="/cookies" className="underline underline-offset-4">cookie policy</Link>, and change your choice at any time with &ldquo;Cookie preferences&rdquo; in the footer.</p></section>
      <section><h2>Status of this page</h2>
        <p className="text-muted">This page describes what the software does. A formal privacy notice reviewed for the applicable data-protection law has not been published yet.</p></section>
    </InfoPage>
  );
}
