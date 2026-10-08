import type { Metadata } from "next";
import React from "react";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "About" };

export default function About() {
  return (
    <InfoPage title="About AfriEdge" lead="Financial intelligence for African listed markets, starting with Tanzania." testId="about-page">
      <section><h2>What it does</h2>
        <p>AfriEdge reads the published reports of listed companies, checks the figures, values the company by stated rules, and shows where every number came from. It also follows the official economic news and market data that can move East African markets.</p></section>
      <section><h2>Coverage today</h2>
        <p>Companies listed on the Dar es Salaam Stock Exchange, with full research on NMB Bank and CRDB Bank; Bank of Tanzania government bonds; official news from the central banks of Tanzania and Kenya and from the World Bank. Kenya and Uganda market data are not yet connected.</p></section>
    </InfoPage>
  );
}
