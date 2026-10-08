import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "Terms of use" };

// Formal terms need the owner's legal text; this page says so instead of inventing them.
export default function TermsPage() {
  return (
    <InfoPage title="Terms of use" lead="The formal terms of use are being prepared." testId="terms-page">
      <section><h2>Until they are published</h2>
        <p>AfriEdge is provided for research and education. Nothing on it is investment advice. The <Link href="/disclaimer" className="underline underline-offset-4">risk disclaimer</Link> describes the limits of the research, and the <Link href="/privacy" className="underline underline-offset-4">privacy policy</Link> describes what is collected.</p></section>
      <section><h2>Data from other publishers</h2>
        <p>Market data, documents and news belong to their publishers and are shown within their terms; each links to its original source.</p></section>
    </InfoPage>
  );
}
