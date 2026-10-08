"use client";

import React from "react";
import { Pill } from "@/components/ui/kit";
import type { Quote } from "@/lib/api";
import { fmtDate } from "@/lib/format";

// How fresh a price is, in a reader's words. The status words (CURRENT, STALE, BLOCKED ...) stay in the API and
// the administration page; here they become "Updated", "Out of date", "Price not shown" with the reason on hover.
export function QuoteFreshness({ quote }: { quote: Quote }) {
  if (!quote.available) {
    return (
      <Pill tone="neutral" hint={quote.public_reason} testId="freshness">
        {quote.public_label}
      </Pill>
    );
  }
  if (quote.reconciliation?.status === "CONFLICTING_SOURCE") {
    return (
      <Pill tone="warn" testId="freshness" hint={`Two data sources disagree about this close (${quote.reconciliation.provider_a}: ${quote.reconciliation.close_a}; ${quote.reconciliation.provider_b}: ${quote.reconciliation.close_b}). The exchange's figure is shown; it is not averaged.`}>
        Sources disagree
      </Pill>
    );
  }
  if (quote.timing === "STALE") {
    return (
      <Pill tone="warn" testId="freshness" hint={`The latest stored close is from ${fmtDate(quote.trade_date)}. Prices are refreshed after each trading session; this one is overdue.`}>
        Out of date
      </Pill>
    );
  }
  return (
    <Pill tone="good" testId="freshness" hint={`Closing price of the session on ${fmtDate(quote.trade_date)}, as published by the Dar es Salaam Stock Exchange. End of day, not a live price.`}>
      Updated
    </Pill>
  );
}
