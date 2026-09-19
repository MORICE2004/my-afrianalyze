import React from "react";
import { NotAvailable } from "@/components/ui/NotAvailable";
import type { Report } from "@/lib/api";
import { fmtPct } from "@/lib/format";

const COLORS = {
  Undervalued: "bg-green-100 text-green-900 border-green-300",
  "Fairly valued": "bg-amber-100 text-amber-900 border-amber-300",
  Overvalued: "bg-red-100 text-red-900 border-red-300",
};

// The model's view from the fixed rule in config/recommendation.json. It is the output of a
// calculation, not advice. Trade labels (BUY / HOLD / SELL) only appear when SHOW_TRADE_LABELS is on.
export function ModelViewBadge({
  recommendation,
  rule,
}: {
  recommendation: Report["header"]["recommendation"];
  rule: Report["recommendation_rule"];
}) {
  return (
    <div className="border border-neutral-200 bg-white p-4" data-testid="model-view">
      <div className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 mb-2">Model view</div>
      {recommendation.available ? (
        <>
          <span className={`inline-block border px-3 py-1 text-lg font-bold ${COLORS[recommendation.model_view]}`}>
            {recommendation.model_view}
          </span>
          {recommendation.trade_label && (
            <span className="ml-2 text-xs font-mono text-neutral-600">Trade label: {recommendation.trade_label}</span>
          )}
          <p className="mt-2 text-xs text-neutral-600">
            Expected total return {fmtPct(recommendation.expected_total_return)} (price {fmtPct(recommendation.price_upside)} +
            dividend {fmtPct(recommendation.dividend_yield)}). Undervalued above {fmtPct(recommendation.thresholds.above)},
            overvalued below {fmtPct(recommendation.thresholds.below)}.
          </p>
        </>
      ) : (
        <NotAvailable reason={recommendation.reason} status={recommendation.status} />
      )}
      <p className="mt-2 text-[11px] text-neutral-500">
        Rule: undervalued if the expected 12-month total return beats the cost of equity by more than{" "}
        {fmtPct(rule.buy_margin)}; overvalued if it falls short by more than {fmtPct(rule.sell_margin)}; otherwise fairly
        valued. This is a model output, not a recommendation to buy or sell.
      </p>
    </div>
  );
}
