import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "Data methodology" };

export default function Methodology() {
  return (
    <InfoPage title="Data methodology" lead="How a figure reaches an AfriEdge page." testId="methodology-page">
      <section><h2>1. Source</h2>
        <p>Company figures come from audited annual reports published by the companies; macro data from the Bank of Tanzania, the National Bureau of Statistics and the World Bank; prices from the Dar es Salaam Stock Exchange&apos;s published end-of-day data. Each stored document keeps its address, retrieval time and a fingerprint (SHA-256).</p></section>
      <section><h2>2. Validation</h2>
        <p>Each statement figure is read by two independent extraction methods. Where both agree it is <em>Verified</em>; where only one read it, <em>Partially verified</em>; where they disagree, <em>Conflicting source</em>, and it is not used in any calculation. Totals are checked against their parts.</p></section>
      <section><h2>3. Calculation</h2>
        <p>Ratios, valuations and technical indicators are computed by deterministic code from validated figures. No language model computes or changes a number.</p></section>
      <section><h2>4. Status words</h2>
        <p>A figure that cannot be verified is not shown as a number; the page shows its status instead: Updated, Delayed, Stale, Limited data or Not available.</p></section>
      <section><h2>5. Review</h2>
        <p>Research is marked as a draft until a named reviewer approves it. The current state of every source is on the <Link href="/health" className="underline underline-offset-4">Data sources</Link> page.</p></section>
    </InfoPage>
  );
}
