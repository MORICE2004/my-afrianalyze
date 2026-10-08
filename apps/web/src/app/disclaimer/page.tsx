import type { Metadata } from "next";
import React from "react";
import { InfoPage } from "@/components/ui/InfoPage";

export const metadata: Metadata = { title: "Risk disclaimer" };

export default function Disclaimer() {
  return (
    <InfoPage title="Risk disclaimer" lead="What AfriEdge research is, and what it is not." testId="disclaimer-page">
      <section><h2>Not investment advice</h2>
        <p>AfriEdge is for research and education only. Nothing on it is investment advice, an offer, or a solicitation to buy or sell any security. Figures are extracted from the sources cited; check the source before relying on any number.</p></section>
      <section><h2>Model views</h2>
        <p>A view such as undervalued or overvalued is the output of a fixed rule applied to stated assumptions. It can change when an assumption changes, and AfriEdge withholds a view when reasonable methods disagree.</p></section>
      <section><h2>Thinly traded markets</h2>
        <p>Many East African shares do not trade every day. Prices, returns and risk measures built on few trades are less reliable; pages say when a share did not trade.</p></section>
      <section><h2>Data timing</h2>
        <p>Market data is end of day, never live, and is shown with the date it applies to. Past performance does not indicate future results.</p></section>
    </InfoPage>
  );
}
